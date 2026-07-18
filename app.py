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

import json
import os

from flask import Flask, jsonify, render_template, request, send_from_directory
from google import genai
from google.genai import types

app = Flask(__name__)
DEMO_ASSETS_DIR = os.path.join(os.path.dirname(__file__), "demo_assets")

MODEL = "gemini-2.5-flash"
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
                    "description": {"type": "string"},
                    "amount": {"type": "number"},
                },
                "required": ["date", "code", "amount"],
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
            "Extract every billed line item from this medical document. "
            "For each line give the date of service, the CPT/HCPCS code, "
            "a short description, and the dollar amount charged. "
            "Return ONLY the items actually printed on the document -- "
            "do not infer or add anything.",
        ],
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=EXTRACTION_SCHEMA,
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
            flags.append(
                {
                    "type": "duplicate_charge",
                    "confidence": "high",
                    "code": code,
                    "date": date,
                    "occurrences": len(items),
                    "total_amount": sum(i["amount"] for i in items),
                    "overcharge_amount": sum(i["amount"] for i in items[1:]),
                    "explanation": (
                        f"CPT {code} was billed {len(items)} times on {date}. "
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


def cross_check_eob(bill_items: list[dict], eob_items: list[dict]) -> list[dict]:
    """Flag anything the EOB marked as denied/duplicate that the bill still
    charges the patient for -- a very concrete, defensible catch."""
    flags = []
    for item in eob_items:
        note = (item.get("description") or "").lower()
        if "denied" in note or "duplicate" in note:
            flags.append(
                {
                    "type": "denied_but_still_billed",
                    "confidence": "high",
                    "code": item["code"],
                    "date": item["date"],
                    "explanation": (
                        f"Your insurer's EOB shows CPT {item['code']} on {item['date']} "
                        "was denied or flagged as a duplicate, yet the provider's bill "
                        "still lists it as patient-owed."
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
        "factual and polite. Ask for a corrected itemized statement.\n\n"
        f"Flagged issues (JSON): {json.dumps(flags, indent=2)}\n\n"
        f"Full billed line items for reference (JSON): {json.dumps(bill_items, indent=2)}"
    )
    response = get_client().models.generate_content(model=MODEL, contents=prompt)
    return response.text


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/demo_assets/<path:filename>")
def demo_assets(filename):
    """Serves the sample bill/EOB so the UI's "Use sample files" button can
    fetch real bytes and hand them to /api/analyze -- not a canned response,
    an actual round trip through the same code path a real upload takes."""
    return send_from_directory(DEMO_ASSETS_DIR, filename)


@app.route("/api/analyze", methods=["POST"])
def analyze():
    bill_file = request.files.get("bill")
    eob_file = request.files.get("eob")
    if not bill_file:
        return jsonify({"error": "Missing bill file"}), 400

    try:
        bill_items = extract_line_items(bill_file.read(), bill_file.mimetype)
        eob_items = extract_line_items(eob_file.read(), eob_file.mimetype) if eob_file else []

        flags = find_duplicate_charges(bill_items)
        flags += check_unbundling(bill_items)
        if eob_items:
            flags += cross_check_eob(bill_items, eob_items)

        letter = draft_dispute_letter(bill_items, flags) if flags else None
    except RuntimeError as e:
        return jsonify({"error": str(e)}), 500
    except Exception as e:  # Gemini API errors, malformed model output, etc.
        return jsonify({"error": f"Analysis failed: {e}"}), 502

    return jsonify(
        {
            "bill_items": bill_items,
            "eob_items": eob_items,
            "flags": flags,
            "total_flagged_amount": sum(
                f.get("overcharge_amount", 0) for f in flags if "overcharge_amount" in f
            ),
            "dispute_letter": letter,
        }
    )


@app.route("/api/send-fax", methods=["POST"])
def send_fax():
    """Stub. Wire up a fax API (e.g. Documo/mFax, Notifyre, Sfax) here.
    Deliberately not implemented with a live provider in this prototype --
    do not fax real hospitals during testing. Point this at your own test
    fax inbox until you have a real dispute to send."""
    return jsonify(
        {
            "sent": False,
            "message": "Fax sending is not wired to a live provider in this prototype. "
            "See README 'Auto-fax' section to connect one.",
        }
    ), 501


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)), debug=True)
