"""Unit tests for ncci.py in isolation.

Two tiers:

1. Synthetic-fixture tests -- run everywhere, fast. The fixtures in
   tests/fixtures/ mimic the REAL CMS file layouts (tab-delimited PTP file
   with multi-line header block; CSV MUE file with quoted preamble) but
   contain only fake codes, so these exercise the exact code path that
   parses the real downloads without shipping any AMA-copyrighted rows.
2. Real-file tests -- run only when the actual CMS downloads are present
   locally (paths from .env; see STEP_BY_STEP_PLAN.md Step 2). Skipped on
   machines without them. No real CMS rows are committed to the repo: the
   AMA click-through license covers use, not redistribution, so the tests
   read the local download instead of a checked-in slice.

Nothing here touches check_unbundling(), check_mue(), or app.py.

    pytest tests/test_ncci.py -v
"""

import os
import pathlib
import sys

import pytest
from dotenv import load_dotenv

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from ncci import load_mue_table, load_ptp_edits

ROOT = pathlib.Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")

FIXTURES = pathlib.Path(__file__).resolve().parent / "fixtures"
PTP_FIXTURE = str(FIXTURES / "fake_ptp_edits.txt")
MUE_FIXTURE = str(FIXTURES / "fake_mue_table.csv")
MISSING = str(FIXTURES / "does_not_exist.csv")


def _real_path(env_var: str) -> str:
    p = os.environ.get(env_var, "")
    return p if os.path.isabs(p) else str(ROOT / p) if p else ""


REAL_PTP = _real_path("PTP_EDITS_PATH")
REAL_MUE = _real_path("MUE_TABLE_PATH")


# --- Synthetic fixtures (real CMS layout, fake codes) -----------------------

def test_load_ptp_edits_parses_all_rows_and_skips_header():
    edits = load_ptp_edits(PTP_FIXTURE)
    assert len(edits) == 5  # 6 data rows, one pair has two windows
    assert sum(len(v) for v in edits.values()) == 6
    for key, records in edits.items():
        assert isinstance(key, tuple) and len(key) == 2
        for record in records:
            assert record["modifier_indicator"] in {"0", "1", "9"}
            assert len(record["effective_date"]) == 8


def test_load_ptp_edits_modifier_indicators_and_rationale():
    edits = load_ptp_edits(PTP_FIXTURE)
    assert edits[("00000", "00001")][0]["modifier_indicator"] == "0"
    assert edits[("00000", "99999")][0]["modifier_indicator"] == "1"
    assert edits[("99998", "99999")][0]["modifier_indicator"] == "9"
    assert "never allowed together" in edits[("00000", "00001")][0]["rationale"]


def test_load_ptp_edits_deletion_date_star_means_active():
    edits = load_ptp_edits(PTP_FIXTURE)
    # "*" in the file = no deletion date = still active -> normalized to ""
    assert edits[("00000", "00001")][0]["deletion_date"] == ""
    # a real 8-digit deletion date is preserved
    assert edits[("00001", "99998")][0]["deletion_date"] == "20260630"


def test_load_ptp_edits_keeps_every_window_of_a_repeated_pair():
    # Real-file behavior: a pair can be deleted then re-added -- the file
    # lists both rows (newest first). Both windows must survive parsing.
    records = load_ptp_edits(PTP_FIXTURE)[("00000", "99998")]
    assert len(records) == 2
    assert records[0]["deletion_date"] == "" and records[0]["modifier_indicator"] == "1"
    assert records[1]["deletion_date"] == "20251231" and records[1]["modifier_indicator"] == "0"


def test_load_ptp_edits_missing_file_returns_empty_dict():
    assert load_ptp_edits(MISSING) == {}


def test_load_mue_table_parses_rows_and_skips_preamble():
    mue = load_mue_table(MUE_FIXTURE)
    assert mue == {"00000": 1, "00001": 4, "99999": 2, "99997": 0}
    for value in mue.values():
        assert isinstance(value, int)


def test_load_mue_table_missing_file_returns_empty_dict():
    assert load_mue_table(MISSING) == {}


# --- Real CMS downloads (local-only; skipped if absent) ---------------------

needs_real_ptp = pytest.mark.skipif(
    not (REAL_PTP and os.path.exists(REAL_PTP)),
    reason="real CMS PTP file not downloaded (see STEP_BY_STEP_PLAN.md Step 2)",
)
needs_real_mue = pytest.mark.skipif(
    not (REAL_MUE and os.path.exists(REAL_MUE)),
    reason="real CMS MUE file not downloaded (see STEP_BY_STEP_PLAN.md Step 2)",
)


@needs_real_ptp
def test_real_ptp_file_parses_at_scale():
    edits = load_ptp_edits(REAL_PTP)
    # v32.2 outpatient hospital file has ~475K data rows across ~449K pairs;
    # any rewrite that silently drops a chunk of the file should trip these.
    assert len(edits) > 400_000
    assert sum(len(v) for v in edits.values()) > 470_000
    for records in list(edits.values())[:1000]:
        for record in records:
            assert record["modifier_indicator"] in {"0", "1", "9"}
            assert len(record["effective_date"]) == 8 and record["effective_date"].isdigit()
            assert record["deletion_date"] == "" or (
                len(record["deletion_date"]) == 8 and record["deletion_date"].isdigit()
            )


@needs_real_ptp
def test_real_ptp_file_repeated_pairs_and_indicator_kinds():
    edits = load_ptp_edits(REAL_PTP)
    flat = [r for records in edits.values() for r in records]
    assert {r["modifier_indicator"] for r in flat} == {"0", "1", "9"}
    assert any(r["deletion_date"] == "" for r in flat)  # "*" rows normalized
    assert any(r["deletion_date"] != "" for r in flat)
    # ~26K pairs carry multiple date windows -- they must all be retained,
    # and no pair may have two windows active at once (which would make
    # "which edit applies" ambiguous for current bills)
    multi = [records for records in edits.values() if len(records) > 1]
    assert len(multi) > 10_000
    assert all(sum(1 for r in records if not r["deletion_date"]) <= 1 for records in multi)


@needs_real_mue
def test_real_mue_file_parses_to_code_int_map():
    mue = load_mue_table(REAL_MUE)
    assert len(mue) > 1000
    assert all(isinstance(v, int) for v in mue.values())
    # the preamble/header must not have leaked in as fake "codes"
    assert all(" " not in code and code for code in mue)
