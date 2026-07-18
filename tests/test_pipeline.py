"""Integration tests for the full ClearBill AI pipeline.

Default mode replaces Gemini with recorded responses captured from real live
runs against the demo PDFs (2026-07-17), so the suite is deterministic, needs
no API key, and spends no quota. Everything else -- the Flask endpoint, file
handling, duplicate detection, the bill-vs-EOB join, total dedup, and letter
grounding -- is the real code under test.

    pytest tests/

Live end-to-end (3 real Gemini calls; needs a funded key in .env):

    RUN_LIVE_GEMINI=1 pytest tests/ -k live
"""

import json
import os
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

import app as clearbill

DEMO = pathlib.Path(__file__).resolve().parents[1] / "demo_assets"
BILL_PDF = DEMO / "sample_itemized_bill.pdf"
EOB_PDF = DEMO / "sample_eob.pdf"

# --- Recorded Gemini extraction output for the demo docs (live run, temp=0) ---

BILL_ITEMS = [
    {"date": "2026-07-10", "code": "99285", "modifier": "", "description": "Emergency Dept Visit, High Complexity / Trauma", "amount": 15270.0},
    {"date": "2026-07-10", "code": "74177", "modifier": "", "description": "CT Abdomen-Pelvis with Contrast", "amount": 17197.0},
    {"date": "2026-07-10", "code": "80053", "modifier": "", "description": "Comprehensive Metabolic Panel", "amount": 1243.0},
    {"date": "2026-07-10", "code": "85025", "modifier": "", "description": "CBC with Automated Differential", "amount": 445.0},
    {"date": "2026-07-10", "code": "36415", "modifier": "", "description": "Venipuncture, Routine Collection", "amount": 112.0},
    {"date": "2026-07-10", "code": "36415", "modifier": "", "description": "Venipuncture, Routine Collection", "amount": 112.0},
]

def _eob(code, billed, status, patient_resp, carc="", reason=""):
    return {
        "service_date": "2026-07-10", "procedure_code": code, "modifier": "",
        "description": "", "billed_amount": billed, "denial_status": status,
        "denial_reason": reason, "carc_code": carc,
        "patient_responsibility": patient_resp,
    }

EOB_ITEMS = [
    _eob("99285", 15270.0, "paid", 1221.6),
    _eob("74177", 17197.0, "paid", 1375.76),
    _eob("80053", 1243.0, "paid", 99.44),
    _eob("85025", 445.0, "paid", 35.6),
    _eob("36415", 112.0, "paid", 8.96),
    _eob("36415", 112.0, "denied", 0.0, carc="18", reason="CARC 18 -- Exact duplicate claim/service"),
]

LETTER_TEXT = "Dear Patient Billing Customer Service,\n\nI am writing to dispute..."


class FakeGemini:
    """Stands in for genai.Client. Dispatches on the response schema so the
    test does not depend on call order, and records every call so tests can
    assert what the letter prompt was grounded in."""

    def __init__(self, bill_items, eob_items, letter=LETTER_TEXT):
        self.bill_items, self.eob_items, self.letter = bill_items, eob_items, letter
        self.calls = []
        self.models = self

    def generate_content(self, model, contents, config=None):
        self.calls.append({"contents": contents, "config": config})
        schema = str(getattr(config, "response_schema", "") or "")
        if "denial_status" in schema:
            text = json.dumps({"line_items": self.eob_items})
        elif "line_items" in schema:
            text = json.dumps({"line_items": self.bill_items})
        else:
            text = self.letter
        return type("R", (), {"text": text})()


@pytest.fixture
def fake():
    return FakeGemini(BILL_ITEMS, EOB_ITEMS)


@pytest.fixture
def client(fake, monkeypatch):
    monkeypatch.setattr(clearbill, "get_client", lambda: fake)
    clearbill.app.config["TESTING"] = True
    return clearbill.app.test_client()


def post_analyze(client, with_eob=True):
    data = {"bill": (BILL_PDF.open("rb"), "bill.pdf", "application/pdf")}
    if with_eob:
        data["eob"] = (EOB_PDF.open("rb"), "eob.pdf", "application/pdf")
    resp = client.post("/api/analyze", data=data, content_type="multipart/form-data")
    return resp, resp.get_json()


# --- Stages 1-6 end to end -------------------------------------------------

def test_full_pipeline(client, fake):
    resp, body = post_analyze(client)
    assert resp.status_code == 200, body

    # Stage 3: line items extracted from both documents
    assert len(body["bill_items"]) == 6
    assert len(body["eob_items"]) == 6
    assert sum(1 for i in body["bill_items"] if i["code"] == "36415") == 2

    flags = {f["type"]: f for f in body["flags"]}
    assert set(flags) == {"duplicate_charge", "denied_but_still_billed"}, body["flags"]

    # Stage 4: duplicate charge detected deterministically
    dup = flags["duplicate_charge"]
    assert (dup["code"], dup["date"]) == ("36415", "2026-07-10")
    assert dup["occurrences"] == 2
    assert dup["overcharge_amount"] == 112.0
    assert dup["confidence"] == "high"

    # Stage 5: denied-but-still-billed found via the bill-vs-EOB join
    den = flags["denied_but_still_billed"]
    assert (den["code"], den["date"]) == ("36415", "2026-07-10")
    assert den["carc_code"] == "18"
    assert den["overcharge_amount"] == 112.0
    assert "CARC 18" in den["explanation"]

    # One bad line, two flags -- must be counted once, not $224
    assert body["total_flagged_amount"] == 112.0

    # Stage 6: dispute letter generated and grounded in the actual flags
    assert body["dispute_letter"] == LETTER_TEXT
    letter_call = fake.calls[-1]
    assert getattr(letter_call["config"], "response_schema", None) is None
    prompt = str(letter_call["contents"])
    assert "duplicate_charge" in prompt
    assert "denied_but_still_billed" in prompt
    assert "36415" in prompt


def test_bill_only_still_flags_duplicates(client):
    resp, body = post_analyze(client, with_eob=False)
    assert resp.status_code == 200
    assert body["eob_items"] == []
    assert [f["type"] for f in body["flags"]] == ["duplicate_charge"]
    assert body["total_flagged_amount"] == 112.0
    assert body["dispute_letter"] == LETTER_TEXT


def test_clean_bill_produces_no_flags_and_no_letter(monkeypatch):
    clean = [i for n, i in enumerate(BILL_ITEMS) if n != 5]  # drop the dup line
    clean_eob = [i for i in EOB_ITEMS if i["denial_status"] != "denied"]
    fake = FakeGemini(clean, clean_eob)
    monkeypatch.setattr(clearbill, "get_client", lambda: fake)
    client = clearbill.app.test_client()
    resp, body = post_analyze(client)
    assert resp.status_code == 200
    assert body["flags"] == []
    assert body["total_flagged_amount"] == 0
    assert body["dispute_letter"] is None
    # No flags -> the letter model must never have been called
    assert all(getattr(c["config"], "response_schema", None) is not None for c in fake.calls)


def test_missing_bill_is_rejected(client):
    resp = client.post("/api/analyze", data={}, content_type="multipart/form-data")
    assert resp.status_code == 400


# --- Stage-level regression tests (pure Python, no Flask) -------------------

def test_duplicate_detection_stage():
    flags = clearbill.find_duplicate_charges(BILL_ITEMS)
    assert len(flags) == 1
    assert flags[0]["overcharge_amount"] == 112.0


def test_cross_check_requires_charge_on_bill():
    denied_not_billed = [_eob("99999", 500.0, "denied", 0.0, carc="18")]
    assert clearbill.cross_check_eob(BILL_ITEMS, denied_not_billed) == []


def test_cross_check_ignores_paid_lines():
    paid_only = [i for i in EOB_ITEMS if i["denial_status"] == "paid"]
    assert clearbill.cross_check_eob(BILL_ITEMS, paid_only) == []


def test_cross_check_joins_on_normalized_key():
    denied = [_eob(" 36415 ", 112.0, "denied", 0.0, carc="18")]
    flags = clearbill.cross_check_eob(BILL_ITEMS, denied)
    assert len(flags) == 1 and flags[0]["overcharge_amount"] == 112.0


# --- Live end-to-end (opt-in: spends 3 real Gemini calls) -------------------

@pytest.mark.skipif(
    not os.environ.get("RUN_LIVE_GEMINI"),
    reason="set RUN_LIVE_GEMINI=1 to run the real Gemini end-to-end test",
)
def test_full_pipeline_live():
    client = clearbill.app.test_client()
    resp, body = post_analyze(client)
    assert resp.status_code == 200, body
    types_found = {f["type"] for f in body["flags"]}
    assert "duplicate_charge" in types_found, body["flags"]
    assert "denied_but_still_billed" in types_found, body["flags"]
    assert any(f["code"] == "36415" for f in body["flags"])
    assert body["total_flagged_amount"] > 0
    assert body["dispute_letter"] and "36415" in body["dispute_letter"]
