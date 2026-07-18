# ClearBill AI — Step-by-Step Plan to Submission

Stanford x DeepMind Hackathon — Sunday July 19, 11:30am–2:30pm PT build sprint.
Every status below was verified by running the code, not by reading the pitch.

## Where things stand

| Piece | Status | Where |
|---|---|---|
| Line-item extraction (Gemini multimodal, structured JSON) | ✅ Works — verified live | `extract_line_items()` — `app.py:67` |
| Duplicate-charge detection (same code + same date) | ✅ Works — verified live, caught the planted CPT 36415 duplicate | `find_duplicate_charges()` — `app.py:87` |
| EOB cross-check (denied but still billed) | ✅ Works — verified live; true bill-vs-EOB join, cites CARC codes (Gap 1 fixed) | `cross_check_eob()` in `app.py` |
| Dispute letter generation (grounded in flags only) | ✅ Works — verified live | `draft_dispute_letter()` — `app.py:151` |
| Unbundling / NCCI edit check | ❌ Stub returns `[]` (AMA CPT license blocker) | `check_unbundling()` — `app.py:121` |
| Auto-fax | ❌ Stub returns 501 | `/api/send-fax` — `app.py:205` |
| Frontend (real app + standalone `preview/index.html` mockup) | ✅ Built | `templates/`, `static/`, `preview/` |
| Cloud Run deployment (**required for submission**) | ❌ Not done | `Dockerfile` exists, untested |

Full live pipeline round trip: ~22s on the demo docs. Letter is only generated
**when flags exist** (`app.py:186`) — a clean bill produces no letter.

## Known gaps (flagged during the live run)

### Gap 1 — EOB cross-check is broken in two independent ways — **FIXED, verified live (uncommitted)**

This is the "your insurer already denied this and they billed you anyway" flag —
one of the two headline demo moments — and it currently never fires.

1. **Extraction drops the denial info.** The extraction schema makes
   `description` optional, and Gemini returns EOB line items with no
   description at all. The CARC 18 ("exact duplicate claim/service") code
   printed on the demo EOB is extracted and thrown away. The check
   string-matches "denied"/"duplicate" in that missing field → always zero flags.
2. **The logic never actually cross-checks.** `cross_check_eob()` receives
   `bill_items` but never uses them. It only scans EOB lines and *assumes*
   any denied line is still on the bill. Nothing is joined between the two
   documents.

**Fix (both parts):** extract each EOB line with an explicit denial
status/reason field (capture CARC codes, don't string-match an optional
description), then match denied EOB lines against `bill_items` by code + date
and flag only when the denied charge is still billed as patient-owed.

### Gap 2 — model name was dead (fixed, needs commit)

`app.py` was pinned to `gemini-2.5-flash`, which Google no longer offers new
API users — the first-ever live request 404'd. Now switched to
`gemini-3.5-flash` (verified available on our key). **This change is in the
working tree but not yet committed.**

### Gap 3 — `.env` is not auto-loaded — **FIXED, verified (uncommitted)**

python-dotenv added; `app.py` loads `.env` at startup (real env vars, e.g. on
Cloud Run, take precedence). Keyless boot verified: app serves the UI, logs a
warning, `/api/analyze` returns a clean JSON error. A fresh clone now runs with
just `pip install -r requirements.txt && python app.py`.

### Gap 4 — one-pager overclaims unbundling

The one-pager says charges are cross-checked against CMS's NCCI PTP/MUE edits.
That check is a stub and realistically stays one (the NCCI files sit behind an
AMA CPT license click-through). A judge who knows medical coding will catch
this. Fix is copy, not code — see Step 3.

### Gap 6 — Gemini free-tier quota: 20 requests/day (**demo-day risk**)

Hit live during testing: the key is on the free tier, which allows
**20 requests/day per model** for `gemini-3.5-flash`. One analysis = 3 calls
(bill extract + EOB extract + letter), so that's ~6 full runs per day — easy
to burn through in rehearsal before the judges ever see it. Fix before Sunday:
enable billing on the Google AI Studio key (paid tier), or bring a second
funded key as backup. Two people also have `GEMINI_API_KEY` exported in their
shell profile (`~/.zshrc`) — remember real env vars override `.env`, so make
sure the funded key is the one actually loaded on the demo machine.

### Gap 5 — new demo PDFs are a harder extraction target

The redesigned demo bill/EOB (letterhead, info panels, remittance stub) are
richer documents than the originals. Extraction handled them correctly in the
live run, but re-verify after any regeneration of the demo assets.

## The steps, in order

### Step 1 — Fix the EOB cross-check (Gap 1) — ✅ DONE, verified live

Highest-priority code fix: it revives the second headline flag.

1. Extend the extraction schema/prompt for EOBs to capture denial status and
   reason codes (CARC) as explicit required fields.
2. Rewrite `cross_check_eob()` to join denied EOB lines against `bill_items`
   by code + date.
3. Re-run the live pipeline; confirm the `denied_but_still_billed` flag fires
   on the demo docs alongside the duplicate flag.

**Done when:** the demo run produces both flags and the letter cites both.

### Step 2 — Commit the model fix + resolve `.env` loading (Gaps 2, 3)

`.env` loading is resolved and README updated; everything still needs
committing. Also address the quota risk (Gap 6) — enable billing on the key.

**Done when:** a fresh clone following the README reaches a working live run,
on a key that won't hit the 20-request/day wall mid-demo.

### Step 3 — Fix the unbundling overclaim in the one-pager (Gap 4)

Rewrite the bullet so NCCI cross-checking is clearly roadmap, and lead with
the two checks that ARE real and deterministic (duplicates + EOB cross-check).
Do **not** ship a model-guessed bundling flag — an earlier guessed pair
(80048+80053) already proved unreliable.

**Done when:** every sentence in the one-pager describes something the code
actually does, or is clearly labeled roadmap.

### Step 4 — Wire up real auto-fax — ⚙️ BUILT, dryrun verified (uncommitted)

Implemented: `/api/send-fax` renders the letter to PDF (reportlab) and sends
via a pluggable provider layer (`fax_providers.py`) — Documo and Notifyre
adapters plus a `dryrun` provider that writes the PDF to `./outbox/`. Frontend
button prompts for a number and sends the edited letter. Config via
`FAX_PROVIDER`/`FAX_API_KEY` in `.env`. Verified live in dryrun mode: 2-page
PDF written, validation and config errors all return clear messages.

Remaining to make it real:
1. Sign up with Documo or Notifyre, put the key in `.env` as `FAX_API_KEY`.
2. **Confirm the adapter against the provider's current API docs** — both were
   written from documentation, never run against a live account.
3. **Never test against a real hospital's number** — use your own test inbox.

**Done when:** clicking "Send Fax" in the UI delivers the letter PDF to the
test inbox via the real provider.

### Step 5 — Fill in the Team section of the one-pager

Names/roles are still a placeholder. Two minutes; don't forget it.

### Step 6 — Deploy to Cloud Run — ⚙️ IMAGE VERIFIED LOCALLY (deploy itself remaining)

Done and verified in a local Docker run:

- Dockerfile fixed: honors Cloud Run's injected `$PORT` (was hardcoded),
  gunicorn `--timeout 120` (default 30s would kill a 3-Gemini-call analysis),
  threads for IO-bound concurrency.
- `.dockerignore` added — **`.env` was previously being baked into the image**
  (real API key); now verified absent from the container.
- `/healthz` endpoint (no Gemini spend) reports whether a key is configured.
- Sample bill/EOB served at `/demo_assets/…` and linked from the page, so
  judges on the hosted URL have something to try.
- Container verified: boots on a non-default port, serves UI + samples,
  fails gracefully keyless.

Remaining:
1. `gcloud run deploy` per README (exact command there) — use a **paid-tier**
   Gemini key (Gap 6) via `--set-env-vars` or Secret Manager.
2. Run the full demo flow against the hosted URL, not just localhost.

**Done when:** the public URL runs the whole pipeline end to end.

### Step 7 — Regenerate the one-pager

After Steps 3 and 5 copy changes land: `node generate_onepager.js` →
refreshes `ClearBill_AI_OnePager.docx` in the repo root.

### Step 8 — Videos + submission checklist

- 2-min team video
- 1-min demo video — pre-record the auto-phone-call moment if showing it
  (don't attempt live; IVR menus are unpredictable). Demo-video social
  engagement counts toward judging.
- Submit: one-pager, hosted URL, both videos, repo link
  (`github.com/LilChainyy/stanford_med`)

## Demo narrative (for the pitch)

Lead with the flags that are deterministic and defensible, in this order:

1. **Duplicate charge** — plain Python, zero false-positive risk, the flag to
   show live.
2. **EOB cross-check** (after Step 1) — "your insurer already denied this and
   they billed you anyway" — the most visceral catch, and after the fix it's a
   true bill-vs-EOB join, not an assumption.
3. **Dispute letter** — generated, grounded, citing the exact code/date/amount.
4. **Live fax send** (after Step 4) — "and it's already on its way to their
   billing office."
