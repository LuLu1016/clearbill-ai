"""
ClearBill AI - hackathon prototype backend.

Flow:
  1. User uploads an itemized bill + EOB (PDF or image).
  2. Gemini (multimodal) extracts structured line items from each document.
  3. Deterministic Python logic flags EXACT duplicate charges (same code +
     same date). This check does NOT depend on the model's judgment, so it
     has no false-positive risk.
  4. Gemini drafts a dispute letter citing the specific flagged lines.

Deliberately out of scope for this prototype: NCCI/MUE "unbundling" checks.
That requires CMS's official Procedure-to-Procedure edit tables, which sit
behind an AMA CPT license click-through. Wire it up as `check_unbundling()`
once that data source is in place -- do not let the model guess bundling
rules on its own.
"""

import io
import json
import os
import re
from datetime import datetime

from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request, send_from_directory
from google import genai
from google.genai import types
from reportlab.lib.pagesizes import letter as LETTER_PAGE
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

import fax_providers

# Load .env from the project root so `python app.py` just works after
# `cp .env.example .env`. Real environment variables (e.g. on Cloud Run,
# where there is no .env file) take precedence and are not overridden.
load_dotenv()

app = Flask(__name__)
DEMO_ASSETS_DIR = os.path.join(os.path.dirname(__file__), "demo_assets")

if not os.environ.get("GEMINI_API_KEY"):
    app.logger.warning(
        "GEMINI_API_KEY is not set -- the app will boot, but /api/analyze will "
        "fail. Copy .env.example to .env and add a key from "
        "https://aistudio.google.com/apikey"
    )

MODEL = "gemini-3.5-flash"
_client = None


def get_client() -> genai.Client:
    """Lazy init so the app can still boot (e.g. for a smoke test) without
    a key configured -- it only fails when an actual Gemini call is made."""
    global _client
    if _client is None:
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError(
                "GEMINI_API_KEY is not set. Copy .env.example to .env and add a key "
                "from https://aistudio.google.com/apikey"
            )
        _client = genai.Client(api_key=api_key)
    return _client

# Shared normalization contract for both document types. Every field is
# required-with-empty-value rather than optional: with optional fields the
# model tends to omit them entirely, which is how denial info got silently
# dropped before. Deterministic formats also make the bill-vs-EOB join safe --
# both sides normalize to the same key.
NORMALIZATION_RULES = (
    "Normalization rules -- apply to every field:\n"
    "- Dates: YYYY-MM-DD (e.g. '07/10/2026' -> '2026-07-10'). If a line has no "
    "date, use the claim/statement service date printed elsewhere on the "
    "document; if none exists, use an empty string.\n"
    "- Procedure codes: the bare 5-character CPT or HCPCS code, uppercase, no "
    "spaces or punctuation (e.g. 'cpt 36415' -> '36415', 'j1885' -> 'J1885'). "
    "If a modifier is appended (e.g. '36415-59'), put only the base code in the "
    "code field and the modifier in the modifier field. Never invent a code -- "
    "if none is printed, use an empty string.\n"
    "- Money: plain dollar numbers (e.g. '$1,243.00' -> 1243.00). Strip currency "
    "symbols and thousands separators. Parenthesized or 'CR' amounts are "
    "credits -> negative. Blank -> 0.\n"
    "- Blank or missing text fields: empty string. Never omit a field, never "
    "write 'N/A' or null.\n"
    "- Extract ONLY what is printed on the document. Do not infer, merge, or "
    "add line items."
)

EXTRACTION_SCHEMA = {
    "type": "object",
    "properties": {
        "line_items": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "date": {"type": "string"},
                    "code": {"type": "string"},
                    "modifier": {"type": "string"},
                    "description": {"type": "string"},
                    "amount": {"type": "number"},
                },
                "required": ["date", "code", "modifier", "description", "amount"],
            },
        }
    },
    "required": ["line_items"],
}

# EOBs need a richer schema than bills: the whole point of reading one is the
# adjudication columns (denial status, reason/CARC codes, patient share).
EOB_EXTRACTION_SCHEMA = {
    "type": "object",
    "properties": {
        "line_items": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "service_date": {"type": "string"},
                    "procedure_code": {"type": "string"},
                    "modifier": {"type": "string"},
                    "description": {"type": "string"},
                    "billed_amount": {"type": "number"},
                    "denial_status": {
                        "type": "string",
                        "enum": ["paid", "denied", "partially_paid", "unknown"],
                    },
                    "denial_reason": {"type": "string"},
                    "carc_code": {"type": "string"},
                    "patient_responsibility": {"type": "number"},
                },
                "required": [
                    "service_date",
                    "procedure_code",
                    "modifier",
                    "description",
                    "billed_amount",
                    "denial_status",
                    "denial_reason",
                    "carc_code",
                    "patient_responsibility",
                ],
            },
        }
    },
    "required": ["line_items"],
}


def extract_line_items(file_bytes: bytes, mime_type: str) -> list[dict]:
    """Ask Gemini to pull structured line items out of a bill or EOB."""
    response = get_client().models.generate_content(
        model=MODEL,
        contents=[
            types.Part.from_bytes(data=file_bytes, mime_type=mime_type),
            "This is a patient's itemized medical bill. Extract every "
            "individual service line item. For each line give: date (date of "
            "service), code (CPT/HCPCS), modifier, description (short, as "
            "printed), and amount (the dollar amount charged for that line). "
            "Skip rows that are not service lines: subtotals, totals, balance "
            "forward, payments, adjustments, and remittance-stub rows.\n\n"
            + NORMALIZATION_RULES,
        ],
        config=types.GenerateContentConfig(
            temperature=0,
            response_mime_type="application/json",
            response_schema=EXTRACTION_SCHEMA,
        ),
    )
    return json.loads(response.text)["line_items"]


def extract_eob_line_items(file_bytes: bytes, mime_type: str) -> list[dict]:
    """Ask Gemini to pull adjudicated line items out of an EOB, including
    denial status and reason codes -- the fields the cross-check runs on."""
    response = get_client().models.generate_content(
        model=MODEL,
        contents=[
            types.Part.from_bytes(data=file_bytes, mime_type=mime_type),
            "This is an insurer's Explanation of Benefits (EOB). Extract every "
            "adjudicated service line. For each line give: service_date, "
            "procedure_code (CPT/HCPCS), modifier, description (short, as "
            "printed), billed_amount, and the adjudication outcome fields:\n"
            "- denial_status: 'denied' if the line was denied, disallowed, "
            "rejected, or marked not covered; 'paid' if the line was allowed "
            "and processed (even if the patient owes a deductible/coinsurance "
            "share); 'partially_paid' if part of the billed charge was denied; "
            "otherwise 'unknown'.\n"
            "- denial_reason: the denial/adjustment reason text exactly as "
            "printed (empty string if none).\n"
            "- carc_code: the Claim Adjustment Reason Code as the bare code "
            "without any group prefix (e.g. 'CO-18' or 'CARC 18' -> '18'; "
            "empty string if none is printed). If several codes appear on one "
            "line, use the one that explains the denial.\n"
            "- patient_responsibility: the patient-owed dollar amount for that "
            "line as stated by the insurer (0 if none shown).\n\n"
            + NORMALIZATION_RULES,
        ],
        config=types.GenerateContentConfig(
            temperature=0,
            response_mime_type="application/json",
            response_schema=EOB_EXTRACTION_SCHEMA,
        ),
    )
    return json.loads(response.text)["line_items"]


def find_duplicate_charges(line_items: list[dict]) -> list[dict]:
    """Deterministic check: same code + same date billed more than once.

    This is intentionally NOT delegated to the model. It is a plain
    dictionary count, so it cannot hallucinate a duplicate that isn't there.
    """
    seen = {}
    for item in line_items:
        key = (item["code"], item["date"])
        seen.setdefault(key, []).append(item)

    flags = []
    for (code, date), items in seen.items():
        if len(items) > 1:
            # Patients don't recognize CPT codes -- lead the explanation with
            # the plain-language description as printed on their own bill,
            # and keep the code as supporting detail, not the headline.
            description = next((i.get("description", "").strip() for i in items if i.get("description", "").strip()), "")
            label = f'"{description}" (CPT {code})' if description else f"CPT {code}"
            flags.append(
                {
                    "type": "duplicate_charge",
                    "confidence": "high",
                    "code": code,
                    "date": date,
                    "description": description,
                    "occurrences": len(items),
                    "total_amount": sum(i["amount"] for i in items),
                    "overcharge_amount": sum(i["amount"] for i in items[1:]),
                    "explanation": (
                        f"{label} was billed {len(items)} times on {_friendly_date(date)}. "
                        "Billing the same discrete service twice in one encounter "
                        "without a modifier documenting medical necessity of a repeat "
                        "is almost always a duplicate-entry error."
                    ),
                }
            )
    return flags


def check_unbundling(line_items: list[dict]) -> list[dict]:
    """Placeholder. Do NOT implement this with the model's own billing
    knowledge -- verify code pairs against CMS's official NCCI PTP edit
    file first (requires AMA CPT license acceptance). See README."""
    return []


def _line_key(code: str, date: str) -> tuple[str, str]:
    return (str(code).strip().upper(), str(date).strip())


def _friendly_date(iso: str) -> str:
    """YYYY-MM-DD is the right format to match bill/EOB lines on -- it's not
    the right format to put in a sentence a patient reads. Reformat only for
    human-facing text; matching/joining always uses the raw ISO string."""
    try:
        d = datetime.strptime(iso, "%Y-%m-%d")
        return f"{d.strftime('%b')} {d.day}, {d.year}"  # avoids non-portable %-d
    except (ValueError, TypeError):
        return iso


def cross_check_eob(bill_items: list[dict], eob_items: list[dict]) -> list[dict]:
    """Join denied EOB lines against the bill: flag only when the insurer
    denied a charge AND that same charge (code + date) is still on the
    patient's bill. Deterministic -- no model judgment involved."""
    billed = {}
    for item in bill_items:
        billed.setdefault(_line_key(item["code"], item["date"]), []).append(item)

    flags = []
    for item in eob_items:
        if item["denial_status"] != "denied":
            continue
        key = _line_key(item["procedure_code"], item["service_date"])
        if key not in billed:
            continue  # denied by insurer but not billed to the patient -- nothing to dispute
        code, date = item["procedure_code"], item["service_date"]
        carc = item.get("carc_code", "").strip()
        reason = item.get("denial_reason", "").strip()
        # The model is told to copy denial_reason "exactly as printed," and
        # EOBs often print the CARC code inline with the reason text (e.g.
        # "CARC 18 -- Exact duplicate claim/service"). Strip a leading repeat
        # of the code we're about to cite separately, or the message reads
        # "CARC 18: CARC 18 -- Exact duplicate claim/service".
        if carc:
            reason = re.sub(rf"^\s*(CARC\s*)?{re.escape(carc)}\s*[-:]+\s*", "", reason, flags=re.IGNORECASE)
        cited = f" (CARC {carc}: {reason})" if carc and reason else (
            f" (CARC {carc})" if carc else (f' ("{reason}")' if reason else "")
        )
        description = next(
            (b.get("description", "").strip() for b in billed[key] if b.get("description", "").strip()), ""
        )
        label = f'"{description}"' if description else f"CPT {code}"
        flags.append(
            {
                "type": "denied_but_still_billed",
                "confidence": "high",
                "code": code,
                "date": date,
                "description": description,
                "denial_status": item["denial_status"],
                "denial_reason": reason,
                "carc_code": carc,
                "patient_responsibility": item["patient_responsibility"],
                # The disputed amount is the billed charge for the denied line,
                # NOT the EOB's patient_responsibility -- on a denied line the
                # insurer says the patient owes $0, which is exactly the point.
                "billed_amount": item["billed_amount"],
                "overcharge_amount": item["billed_amount"],
                "explanation": (
                    f"Your insurer's EOB shows {label} on {_friendly_date(date)} was denied{cited}, "
                    "yet the provider's bill still lists this charge as patient-owed."
                ),
            }
        )
    return flags


def draft_dispute_letter(bill_items: list[dict], flags: list[dict]) -> str:
    prompt = (
        "You are drafting a formal billing dispute letter on behalf of a patient, "
        "addressed to a hospital's Patient Billing Customer Service office. "
        "Reference ONLY the specific flagged issues below -- do not invent "
        "additional claims, do not accuse the hospital of fraud, and keep the tone "
        "factual and polite. Ask for a corrected itemized statement. If several "
        "flagged issues concern the same line item (same code and date), treat them "
        "as one disputed charge supported by multiple findings -- do not add their "
        "amounts together.\n\n"
        f"Flagged issues (JSON): {json.dumps(flags, indent=2)}\n\n"
        f"Full billed line items for reference (JSON): {json.dumps(bill_items, indent=2)}"
    )
    response = get_client().models.generate_content(model=MODEL, contents=prompt)
    return response.text


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/healthz")
def healthz():
    """Liveness probe -- no Gemini call, safe for load balancers to poll."""
    return jsonify(
        {
            "status": "ok",
            "gemini_key_configured": bool(os.environ.get("GEMINI_API_KEY")),
        }
    )


@app.route("/demo_assets/<path:filename>")
def demo_assets(filename):
    """
    Serve synthetic sample bill/EOB PDFs for demo uploads.

    The UI uses these files and sends them through the exact same
    /api/analyze pipeline as a real user upload.
    """
    if not filename.endswith(".pdf"):
        return jsonify({"error": "Not found"}), 404

    return send_from_directory(DEMO_ASSETS_DIR, filename)


@app.route("/api/analyze", methods=["POST"])
def analyze():
    bill_file = request.files.get("bill")
    eob_file = request.files.get("eob")
    if not bill_file:
        return jsonify({"error": "Missing bill file"}), 400

    try:
        bill_items = extract_line_items(bill_file.read(), bill_file.mimetype)
        eob_items = extract_eob_line_items(eob_file.read(), eob_file.mimetype) if eob_file else []

        flags = find_duplicate_charges(bill_items)
        flags += check_unbundling(bill_items)
        if eob_items:
            flags += cross_check_eob(bill_items, eob_items)

        letter = draft_dispute_letter(bill_items, flags) if flags else None
    except RuntimeError as e:
        return jsonify({"error": str(e)}), 500
    except Exception as e:  # Gemini API errors, malformed model output, etc.
        return jsonify({"error": f"Analysis failed: {e}"}), 502

    # A single bill line can trip more than one check (e.g. a duplicate the
    # insurer also denied) -- count each disputed line once, not per flag.
    per_line = {}
    for f in flags:
        if "overcharge_amount" in f:
            key = _line_key(f["code"], f["date"])
            per_line[key] = max(per_line[key], f["overcharge_amount"]) if key in per_line else f["overcharge_amount"]

    return jsonify(
        {
            "bill_items": bill_items,
            "eob_items": eob_items,
            "flags": flags,
            "total_flagged_amount": sum(per_line.values()),
            "dispute_letter": letter,
        }
    )


def render_letter_pdf(text: str) -> bytes:
    """Render the dispute letter as a simple one-column PDF letter."""
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=LETTER_PAGE,
        leftMargin=1 * inch,
        rightMargin=1 * inch,
        topMargin=1 * inch,
        bottomMargin=1 * inch,
        title="Billing dispute letter",
    )
    style = getSampleStyleSheet()["Normal"]
    style.fontSize = 11
    style.leading = 15

    story = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            story.append(Spacer(1, 10))
            continue
        # The letter arrives as light markdown; keep bold, escape the rest.
        line = line.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        line = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", line)
        story.append(Paragraph(line, style))
    doc.build(story)
    return buf.getvalue()


@app.route("/api/send-fax", methods=["POST"])
def send_fax():
    """Render the dispute letter to PDF and send it via the configured fax
    provider (see fax_providers.py; FAX_PROVIDER/FAX_API_KEY in .env).
    Do not fax real hospitals during testing -- use FAX_PROVIDER=dryrun or
    your own test fax inbox until there is an actual dispute to send."""
    data = request.get_json(silent=True) or {}
    letter_text = (data.get("letter") or "").strip()
    fax_number = re.sub(r"[^\d+]", "", data.get("fax_number") or "")

    if not letter_text:
        return jsonify({"sent": False, "message": "Missing 'letter' -- run an analysis first."}), 400
    if len(re.sub(r"\D", "", fax_number)) < 10:
        return jsonify(
            {"sent": False, "message": "Enter a valid fax number (at least 10 digits, e.g. +16505551234)."}
        ), 400

    try:
        provider = fax_providers.get_provider()
    except fax_providers.FaxError as e:
        return jsonify({"sent": False, "message": str(e)}), 501

    try:
        result = provider.send(render_letter_pdf(letter_text), fax_number)
    except fax_providers.FaxError as e:
        return jsonify({"sent": False, "message": str(e)}), 502
    except Exception as e:  # network failures, provider outages, etc.
        return jsonify({"sent": False, "message": f"Fax failed unexpectedly: {e}"}), 502

    return jsonify(
        {
            "sent": True,
            "provider": provider.name,
            "id": result.get("id"),
            "message": f"Fax to {fax_number} accepted via {provider.name}. {result.get('detail', '')}".strip(),
        }
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)), debug=True)
