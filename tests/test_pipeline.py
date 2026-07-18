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
    # Pipeline tests must not depend on which CMS reference files a teammate
    # happens to have in data/raw/ -- pin both tables empty here; the
    # unbundling/MUE tests below inject their own small in-memory tables.
    monkeypatch.setattr(clearbill, "get_ptp_table", dict)
    monkeypatch.setattr(clearbill, "get_mue_table", dict)
    clearbill.app.config["TESTING"] = True
    return clearbill.app.test_client()


def _ptp_record(indicator, eff="20200101", deleted="", rationale="fake rationale (test only)"):
    return {
        "modifier_indicator": indicator,
        "effective_date": eff,
        "deletion_date": deleted,
        "rationale": rationale,
    }


def _line(code, amount, modifier="", date="2026-07-10", units=None):
    item = {"date": date, "code": code, "modifier": modifier,
            "description": f"Fake service {code}", "amount": amount}
    if units is not None:
        item["units"] = units
    return item


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


def test_unbundling_and_mue_are_noop_without_real_cms_files(fake, monkeypatch):
    """Proof that check_unbundling()/check_mue() change nothing observable
    until the real CMS files land in data/raw/: on the demo bill + EOB the
    flags are exactly what they were before this work. Uses the REAL table
    loaders (not the client fixture's empty-table pin), so it only runs
    where the files are genuinely absent."""
    for path in (clearbill.PTP_EDITS_PATH, clearbill.MUE_TABLE_PATH):
        if os.path.exists(path):
            pytest.skip(f"real CMS file present at {path} -- no-op premise no longer applies")

    monkeypatch.setattr(clearbill, "get_client", lambda: fake)
    monkeypatch.setattr(clearbill, "_ptp_table", None)
    monkeypatch.setattr(clearbill, "_mue_table", None)
    client = clearbill.app.test_client()
    resp, body = post_analyze(client)
    assert resp.status_code == 200, body
    flag_types = {f["type"] for f in body["flags"]}
    assert flag_types == {"duplicate_charge", "denied_but_still_billed"}, body["flags"]
    assert "unbundling" not in flag_types
    assert "mue_exceeded" not in flag_types
    assert body["total_flagged_amount"] == 112.0


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
    monkeypatch.setattr(clearbill, "get_ptp_table", dict)
    monkeypatch.setattr(clearbill, "get_mue_table", dict)
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


# --- Unbundling / MUE checks (small in-memory tables via monkeypatch, so no
# test depends on the 475K-row CMS download being present) -------------------

def test_unbundling_indicator_0_always_flags(monkeypatch):
    monkeypatch.setattr(clearbill, "get_ptp_table",
                        lambda: {("00000", "00001"): [_ptp_record("0")]})
    flags = clearbill.check_unbundling([_line("00000", 100.0), _line("00001", 40.0)])
    assert len(flags) == 1
    f = flags[0]
    assert f["type"] == "unbundling" and f["confidence"] == "high"
    assert f["code"] == "00001"  # the Column 2 code is the disputed line
    assert f["overcharge_amount"] == 40.0
    assert "CMS NCCI PTP edit" in f["explanation"]
    assert "fake rationale (test only)" in f["explanation"]  # CMS rationale cited


def test_unbundling_pair_matches_in_both_orders(monkeypatch):
    monkeypatch.setattr(clearbill, "get_ptp_table",
                        lambda: {("99999", "00001"): [_ptp_record("0")]})
    # bill lists the codes in the opposite order to the table's (col1, col2)
    flags = clearbill.check_unbundling([_line("00001", 40.0), _line("99999", 100.0)])
    assert len(flags) == 1 and flags[0]["code"] == "00001"


def test_unbundling_indicator_1_suppressed_by_modifier(monkeypatch):
    monkeypatch.setattr(clearbill, "get_ptp_table",
                        lambda: {("00000", "00001"): [_ptp_record("1")]})
    with_mod = [_line("00000", 100.0), _line("00001", 40.0, modifier="59")]
    without_mod = [_line("00000", 100.0), _line("00001", 40.0)]
    assert clearbill.check_unbundling(with_mod) == []
    assert len(clearbill.check_unbundling(without_mod)) == 1


def test_unbundling_indicator_9_never_flags(monkeypatch):
    monkeypatch.setattr(clearbill, "get_ptp_table",
                        lambda: {("00000", "00001"): [_ptp_record("9")]})
    assert clearbill.check_unbundling([_line("00000", 100.0), _line("00001", 40.0)]) == []


def test_unbundling_respects_effective_and_deletion_window(monkeypatch):
    # bill date of service is 2026-07-10 -> dos 20260710
    not_yet = {("00000", "00001"): [_ptp_record("0", eff="20270101")]}
    expired = {("00000", "00001"): [_ptp_record("0", deleted="20251231")]}
    active = {("00000", "00001"): [_ptp_record("0", deleted="20261231")]}
    items = [_line("00000", 100.0), _line("00001", 40.0)]
    for table, expected in ((not_yet, 0), (expired, 0), (active, 1)):
        monkeypatch.setattr(clearbill, "get_ptp_table", lambda t=table: t)
        assert len(clearbill.check_unbundling(items)) == expected, table


def test_unbundling_picks_the_window_covering_the_service_date(monkeypatch):
    """Real-file behavior: a pair deleted then re-added has two records,
    newest first. The record whose window covers the date of service must
    win -- not just whichever the parser saw first/last."""
    table = {("00000", "00001"): [
        _ptp_record("1", eff="20260101"),                      # current window
        _ptp_record("0", eff="20250101", deleted="20251231"),  # old window
    ]}
    monkeypatch.setattr(clearbill, "get_ptp_table", lambda: table)
    # dos 2026-07-10 -> current window ("1") applies; with a modifier on a
    # line it must be suppressed. If the old "0" record were wrongly used,
    # the modifier wouldn't matter and this would flag.
    items = [_line("00000", 100.0), _line("00001", 40.0, modifier="59")]
    assert clearbill.check_unbundling(items) == []
    # dos inside the old window -> the "0" record applies and modifier is moot
    old = [_line("00000", 100.0, date="2025-06-15"),
           _line("00001", 40.0, date="2025-06-15", modifier="59")]
    assert len(clearbill.check_unbundling(old)) == 1


def test_unbundling_requires_same_date(monkeypatch):
    monkeypatch.setattr(clearbill, "get_ptp_table",
                        lambda: {("00000", "00001"): [_ptp_record("0")]})
    items = [_line("00000", 100.0), _line("00001", 40.0, date="2026-07-11")]
    assert clearbill.check_unbundling(items) == []


def test_mue_flags_when_summed_units_exceed_max(monkeypatch):
    monkeypatch.setattr(clearbill, "get_mue_table", lambda: {"00001": 2})
    # 3 units across two lines of the same code+date; limit is 2
    flags = clearbill.check_mue([_line("00001", 80.0, units=2), _line("00001", 40.0, units=1)])
    assert len(flags) == 1
    f = flags[0]
    assert f["type"] == "mue_exceeded" and f["confidence"] == "high"
    assert f["units_billed"] == 3 and f["max_units_per_day"] == 2
    assert "CMS MUE" in f["explanation"]
    assert f["overcharge_amount"] == 40.0  # the third unit = the second line


def test_mue_missing_units_field_counts_as_one(monkeypatch):
    monkeypatch.setattr(clearbill, "get_mue_table", lambda: {"00001": 2})
    # recorded extractions predating the units field: 3 lines = 3 units
    lines = [_line("00001", 40.0), _line("00001", 40.0), _line("00001", 40.0)]
    flags = clearbill.check_mue(lines)
    assert len(flags) == 1 and flags[0]["units_billed"] == 3
    assert flags[0]["overcharge_amount"] == 40.0
    assert clearbill.check_mue(lines[:2]) == []  # at the limit -> no flag


def test_mue_zero_limit_flags_any_billing(monkeypatch):
    # a real MUE value of 0 means "never billable" -- one unit must flag
    monkeypatch.setattr(clearbill, "get_mue_table", lambda: {"99997": 0})
    flags = clearbill.check_mue([_line("99997", 25.0, units=1)])
    assert len(flags) == 1 and flags[0]["overcharge_amount"] == 25.0


def test_unbundling_and_mue_flags_flow_through_analyze_endpoint(monkeypatch):
    """End to end: injected tables + a bill containing a bundled pair and an
    over-limit code -> both flags appear in /api/analyze output, join the
    dedup total, and ground the dispute letter."""
    bill = BILL_ITEMS + [
        _line("00000", 100.0), _line("00001", 40.0),   # bundled pair
        _line("99997", 25.0, units=3),                  # MUE limit 1
    ]
    fake = FakeGemini(bill, EOB_ITEMS)
    monkeypatch.setattr(clearbill, "get_client", lambda: fake)
    monkeypatch.setattr(clearbill, "get_ptp_table",
                        lambda: {("00000", "00001"): [_ptp_record("0")]})
    monkeypatch.setattr(clearbill, "get_mue_table", lambda: {"99997": 1})
    client = clearbill.app.test_client()

    resp, body = post_analyze(client)
    assert resp.status_code == 200, body
    flag_types = {f["type"] for f in body["flags"]}
    assert {"unbundling", "mue_exceeded"} <= flag_types
    # pre-existing flags unaffected
    assert {"duplicate_charge", "denied_but_still_billed"} <= flag_types
    # dedup total: 112.0 (36415 line) + 40.0 (00001) + 2 excess units of 99997
    mue = next(f for f in body["flags"] if f["type"] == "mue_exceeded")
    assert mue["overcharge_amount"] == round(25.0 * 2 / 3, 2)
    assert body["total_flagged_amount"] == pytest.approx(112.0 + 40.0 + mue["overcharge_amount"])
    # letter grounded in the new flags too
    prompt = str(fake.calls[-1]["contents"])
    assert "unbundling" in prompt and "mue_exceeded" in prompt


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
