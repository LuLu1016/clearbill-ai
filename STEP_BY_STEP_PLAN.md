# ClearBill AI — Step-by-Step Plan to Submission

Stanford x DeepMind Hackathon — Sunday July 19, 11:30am–2:30pm PT build sprint.

## Done (verified by running the code, not by reading the pitch)

- Line-item extraction (Gemini multimodal, structured JSON) — `extract_line_items()`
- Duplicate-charge detection (same code + same date) — `find_duplicate_charges()`
- EOB cross-check (denied-but-still-billed) — true bill-vs-EOB join on code+date, cites CARC codes — `cross_check_eob()`
- Dispute letter generation, grounded only in the flags actually found — `draft_dispute_letter()`
- Auto-fax pipeline built (`fax_providers.py`): renders letter to PDF, pluggable provider (Documo/Notifyre adapters + `dryrun`). Dryrun verified live — writes to `./outbox/`.
- `.env` auto-loading (python-dotenv), model fixed to a working `gemini-3.5-flash` pin, `/healthz` endpoint (no Gemini spend)
- Frontend: real app (`templates/`, `static/`) + standalone `preview/index.html` mockup
- Docker image verified locally: honors Cloud Run's `$PORT`, gunicorn timeout raised to 120s, `.env` confirmed excluded from the image via `.dockerignore`

**Loose ends on the "done" list** — small, not architectural:
- Model-name and dotenv fixes are in the working tree but not committed
- Free-tier Gemini key caps at 20 requests/day/model — will run out mid-rehearsal; needs billing enabled or a funded backup key before Sunday
- Team section in the one-pager is still a placeholder
- `gcloud run deploy` itself hasn't actually been run yet (image is verified, deploy is not)
- No demo/team videos yet

## Not done — Unbundling / NCCI check (current focus)

**The old plan here is being thrown out.** It proposed either hardcoding a small
"seed list" of specific CPT pairs guessed from panel-composition logic or
third-party blog posts (e.g. "80048+80053"), or giving up on the check
entirely and only fixing the one-pager's copy. Both options keep fake/guessed
data inside the actual checking logic, which is the same mistake already made
once on this project. The fix isn't a better guess — it's building the
pipeline to check the real government file, so nothing in `check_unbundling()`
depends on anyone's memory of which codes bundle with which.

### Step 1 — Build the parser for CMS's real PTP + MUE file format (no real data yet)

Write a generic loader targeting the documented CMS quarterly file structure:
PTP files have Column 1 code, Column 2 code, effective date, deletion date,
modifier indicator, rationale category; MUE files have code + max-units-per-day.
This gets unit-tested against a small fabricated CSV that only proves the
*parser* works — no real CPT pairs get hardcoded into app logic at this stage.

### Step 2 — Get the real CMS file

This step cannot be done on your behalf: CMS gates the PTP/MUE download behind
an AMA CPT copyright click-through, and accepting that agreement has to be
your own action, not something taken for you. To unblock Step 3:

1. Go to CMS's NCCI PTP Edits page, accept the click-through
2. Download the current quarter's **Hospital Outpatient PTP Edits** file and
   the **Outpatient Hospital MUE table**
3. Drop the files in `data/raw/` in the repo (or hand them over directly)

**Keep `data/raw/` out of git** (add it to `.gitignore`): the CMS PTP/MUE
files contain AMA-copyrighted CPT content — that's exactly why the download
sits behind a license click-through. The license covers your own use, not
redistribution, so the raw files must not be committed to a public repo.
Each machine that needs them downloads its own copy via the steps above.

### Step 3 — Wire the real file into `check_unbundling()` / new `check_mue()`

Once the real file exists locally, point the Step 1 parser at it and replace
the stub. The check then runs against actual CMS data for whatever codes
happen to appear on whatever bill gets uploaded — nothing hardcoded, nothing
guessed.

### Step 4 — Only now, build the demo scenario

With the real check running, pick a pair the official file actually confirms
is bundled and use it to construct (or update) the synthetic demo bill/EOB —
same pattern as the existing fake-patient + duplicated-venipuncture demo, just
for unbundling this time. The synthetic data belongs in `demo_assets/`, built
on top of a verified-real rule — not invented rules dressed up as real.

### Step 5 — Update docs

`README.md` "Why this is defensible" section and this plan: once real, describe
unbundling as a lookup against the official CMS file (name the exact file /
effective date checked in), not a stub and not a guess.

## Other remaining items (unchanged from before)

- Fill in the Team section in the one-pager
- `gcloud run deploy` for real (image already verified locally)
- Enable billing on the Gemini key / confirm a funded backup before demo day
- 2-min team video, 1-min demo video
- Regenerate `ClearBill_AI_OnePager.docx` after copy changes land (`node generate_onepager.js`)

## Demo narrative (for the pitch)

Lead with what's deterministic and defensible, in this order:

1. **Duplicate charge** — plain Python, zero false-positive risk, the flag to show live.
2. **EOB cross-check** — "your insurer already denied this and they billed you anyway" — a true bill-vs-EOB join, not an assumption.
3. **Dispute letter** — generated, grounded, citing the exact code/date/amount.
4. **Live fax send** — "and it's already on its way to their billing office."
5. **Unbundling** — only mention on stage once Steps 1-4 above are actually done against the real CMS file. Until then, don't claim it.
