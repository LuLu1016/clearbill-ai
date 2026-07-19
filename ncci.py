"""Load CMS NCCI reference data for the unbundling/MUE checks in app.py.

Parses the real CMS quarterly files dropped in data/raw/ (see
STEP_BY_STEP_PLAN.md Step 2 for how to obtain them):

- PTP (Procedure-to-Procedure) edits: tab-delimited .txt with a multi-line
  header block, then one row per edit pair -- Column 1 code, Column 2 code,
  "in existence prior to 1996" flag, effective date, deletion date,
  modifier indicator, rationale. The basis for check_unbundling().
- MUE (Medically Unlikely Edits): CSV with a quoted AMA-copyright preamble
  and a header row, then one row per code -- code, max units per day,
  adjudication indicator, rationale. The basis for check_mue().

Format-fidelity note (the fixture-vs-real-format decision): there is ONE
parser per file, targeting the real CMS format. The synthetic fixtures in
tests/fixtures/ mimic that real shape exactly but contain only fake codes
(00000/00001/99998/99999 -- outside the CPT code space), so the fast
portable tests exercise the same code path that parses the real download.
No second "generic CSV" code path exists; a parser that only handles a
format CMS doesn't ship isn't worth testing.

No CPT pairs or unit limits are hardcoded here; everything comes from the
official CMS files at runtime.
"""

import csv


def load_ptp_edits(path: str) -> dict[tuple[str, str], list[dict]]:
    """Load CMS NCCI PTP (Procedure-to-Procedure) edits from a quarterly file.

    Expects the real CMS format: tab-delimited text, CRLF or LF line
    endings, a header block of unknown length (skipped by detection, not by
    counting lines: a data row is one whose first field is non-empty and
    whose 4th field is an 8-digit effective date), then rows of
    [column_1_code, column_2_code, pre-1996 flag (ignored), effective_date
    YYYYMMDD, deletion_date (YYYYMMDD, or "*"/blank = no deletion),
    modifier_indicator ("0"/"1"/"9"), rationale].

    Returns a dict mapping (column_1_code, column_2_code) -> LIST of record
    dicts, one per row for that pair, in file order:
        {"modifier_indicator": "0"|"1"|"9",   # 0=never together,
                                              # 1=modifier allowed, 9=n/a
         "effective_date": "YYYYMMDD",
         "deletion_date": "YYYYMMDD" or "",   # "" = still active
         "rationale": str}                    # CMS's own PTP edit rationale

    Why a list: ~26K pairs appear multiple times in the real file with
    disjoint date windows (an edit deleted, then re-added with a different
    indicator), listed newest-first. Collapsing to one record per pair
    silently drops whichever window loses -- the caller must instead pick
    the record whose [effective, deletion] window covers the bill's date of
    service. (Windows for a pair never overlap in the real file: at most
    one record is in force on any given date.) The record shape, rather
    than a bare indicator string, exists because check_unbundling() must
    honor that window and cite CMS's rationale text.

    If `path` does not exist, returns {} rather than raising, so the
    unbundling check degrades to a no-op when the CMS file hasn't been
    downloaded yet.
    """
    try:
        edits = {}
        # CMS ships these files cp1252-encoded (the AMA preamble contains a
        # raw "\xae" for the CPT(R) mark); latin-1 decodes every byte and the
        # fields we consume are plain ASCII either way.
        with open(path, newline="", encoding="latin-1") as f:
            for line in f:
                fields = [x.strip() for x in line.rstrip("\r\n").split("\t")]
                if (
                    len(fields) < 6
                    or not fields[0]
                    or len(fields[3]) != 8
                    or not fields[3].isdigit()
                ):
                    continue  # header block, column-label rows, blank lines
                deletion = fields[4]
                edits.setdefault((fields[0], fields[1]), []).append(
                    {
                        "modifier_indicator": fields[5],
                        "effective_date": fields[3],
                        "deletion_date": "" if deletion in ("", "*") else deletion,
                        "rationale": fields[6] if len(fields) > 6 else "",
                    }
                )
        return edits
    except FileNotFoundError:
        return {}


def load_mue_table(path: str) -> dict[str, int]:
    """Load a CMS MUE (Medically Unlikely Edits) table from a quarterly file.

    Expects the real CMS format: CSV whose first row is a long quoted AMA
    copyright preamble, then a header row, then data rows of
    [code, max units per day, adjudication indicator, rationale]. Data rows
    are detected, not counted: a row whose first field is a non-empty code
    and whose second field is an integer. (An MUE value of 0 is meaningful:
    that code should never be billed at all.)

    Returns a dict mapping code -> max units/day (int).

    If `path` does not exist, returns {} rather than raising, so the MUE
    check degrades to a no-op when the CMS file hasn't been downloaded yet.
    """
    try:
        table = {}
        # latin-1 for the same reason as load_ptp_edits: CMS's preamble is
        # cp1252, and every field we consume is ASCII.
        with open(path, newline="", encoding="latin-1") as f:
            for row in csv.reader(f):
                if len(row) < 2:
                    continue
                code, units = row[0].strip(), row[1].strip()
                if not code or " " in code or not units.isdigit():
                    continue  # preamble, header, blank rows
                table[code] = int(units)
        return table
    except FileNotFoundError:
        return {}


# Integration (STEP_BY_STEP_PLAN.md Step 3, now live): app.py caches both
# tables in module-level lazy singletons (get_ptp_table()/get_mue_table(),
# same pattern as get_client()) so the ~475K-row PTP file is parsed once
# per process, not per request. check_unbundling()/check_mue() read from
# those caches. With no files in data/raw/ the loaders return {} and both
# checks flag nothing.
