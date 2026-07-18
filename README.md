# ClearBill AI

Find the money hospitals didn't mean to bill you.

Upload an itemized medical bill (and, optionally, the insurer's EOB) and get back a
Billing Health Report in under a minute: extracted line items, flagged duplicate
charges, and a ready-to-send dispute letter.

Built for the [Stanford x DeepMind Hackathon](https://luma.com/e51fygtm), July 19, 2026.

**[Interactive preview](https://claude.ai/code/artifact/a71af5c3-3b75-4d1f-834b-c4929320e29d)** — click "Use sample bill" then "Analyze Bill" to see the full flow with no setup and no API key. It's a static walkthrough of a real Stanford Health Care scenario, not the live Gemini pipeline — that's `app.py`. The same file is checked in at `preview/index.html` if you'd rather open it locally.

## Why this is defensible, not a guess

Every flag ClearBill AI raises is grounded in something citable:

- **Duplicate charges** — same CPT code, same date, billed more than once. This is
  checked with plain Python dictionary logic (`find_duplicate_charges` in `app.py`),
  *not* the model's judgment, so there's no hallucination risk.
- **Denied-but-still-billed** — cross-references the EOB: if the insurer already
  marked a line as denied/duplicate but the bill still charges the patient for it,
  that's flagged.
- **Unbundling (NCCI PTP edits)** — intentionally **not implemented** in this
  prototype. CMS's official Procedure-to-Procedure edit tables are the correct source
  for this, but the raw files require accepting an AMA CPT license click-through
  before download. Don't let the model infer bundling rules from general medical
  knowledge — wire `check_unbundling()` in `app.py` up to the real CMS edit file (or
  a licensed third-party coding API) before claiming this in front of anyone who
  knows medical billing.

## Demo assets

`demo_assets/` has a synthetic (fake patient, real prices) itemized bill and EOB to
test with:

- `sample_itemized_bill.pdf` — an ER visit at "Stanford Health Care" with a
  duplicated venipuncture line (CPT 36415, billed twice)
- `sample_eob.pdf` — the matching EOB, where the insurer denies the duplicate line
- `stanford_cpt_reference.json` — the source data: real gross charges and cash
  prices pulled directly from **Stanford Health Care's own CMS-mandated price
  transparency file**, dated 2026-04-01 ([source](https://stanfordhealthcare.org/for-patients-visitors/price-transparency.html))

Regenerate them with `python demo_assets/generate_demo_docs.py` (needs `reportlab`).

**Do not test against real hospitals' real fax/phone numbers.** Point the fax
integration at your own test inbox until you're submitting an actual dispute.

## Run locally

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # add your Gemini API key from https://aistudio.google.com/apikey
python app.py
```

`.env` is loaded automatically at startup (python-dotenv) — no need to export
anything manually. If the key is missing the app still boots and serves the UI,
logs a warning, and `/api/analyze` returns a clear error instead of crashing.
On Cloud Run, real environment variables are used as-is; a `.env` file isn't
needed and won't override them.

Open http://localhost:8080, upload the two files from `demo_assets/`, click Analyze.

## Tests

```bash
pip install -r requirements-dev.txt
pytest tests/
```

The suite runs the full pipeline through the Flask endpoint with Gemini replaced
by recorded real responses — deterministic, no API key, no quota spend. It
verifies extraction plumbing, duplicate detection, the bill-vs-EOB denial join,
the no-double-count total, and that the letter is grounded in the actual flags.

Before demo day, run the true end-to-end once (3 real Gemini calls):

```bash
RUN_LIVE_GEMINI=1 pytest tests/ -k live
```

## Deploy

### Option A — Google AI Studio (vibe-coding path)

Per the hackathon rules, you can build/iterate directly in
[Google AI Studio](https://aistudio.google.com/) and share via its sharing
mechanics for the "Code Repository" submission requirement. Paste `app.py` and the
`templates/`/`static/` files in as your starting point.

### Option B — Google Cloud Run

```bash
gcloud auth login
gcloud config set project YOUR_PROJECT_ID

gcloud run deploy clearbill-ai \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --timeout 120 \
  --set-env-vars GEMINI_API_KEY=YOUR_KEY,FAX_PROVIDER=dryrun
```

Cloud Run builds the `Dockerfile` automatically. Grab the printed URL — that's your
"Hosted Prototype" link for submission.

Notes:

- `--timeout 120` matters: one analysis makes three sequential Gemini calls
  (~20–60s total); the gunicorn worker timeout in the Dockerfile is set to match.
- Secrets are injected at runtime — `.env` is excluded from the image by
  `.dockerignore`, never baked in. For anything beyond a hackathon, prefer
  `--set-secrets GEMINI_API_KEY=gemini-key:latest` (Secret Manager) over
  `--set-env-vars`.
- Health check: `GET /healthz` returns `{"status": "ok", "gemini_key_configured": true}`
  without spending a Gemini call — use it to verify the deploy landed with a key.
- The hosted page links the sample bill/EOB for download (served at
  `/demo_assets/…`), so judges can try the flow without a bill of their own.
- Make sure the key you deploy with is **paid tier** — the free tier's
  20 requests/day/model dies mid-demo.

## Auto-fax

`/api/send-fax` renders the dispute letter to PDF (reportlab) and sends it via a
pluggable provider (`fax_providers.py`). Configure in `.env`:

```bash
FAX_PROVIDER=dryrun    # dryrun | documo | notifyre
FAX_API_KEY=           # required for documo/notifyre; from the provider dashboard
```

- **dryrun** (default) writes the PDF to `./outbox/` instead of faxing — the full
  flow works with no account and nothing is ever sent. Use this for all testing.
- **documo / notifyre** POST to the provider's send API. Written from their docs
  but not yet exercised against a live account — when you sign up, confirm the
  endpoint/payload against current docs before relying on it on stage.
- Swapping in another vendor = one new subclass in `fax_providers.py`; `app.py`
  doesn't change.

**Never fax a real hospital's number during testing.** Point real providers at
your own test fax inbox until there's an actual dispute to send.

If you build the outbound-voice-call variant instead (Gemini Live API + Twilio
Voice), open the call with a spoken disclosure ("this call may be recorded") —
California is a two-party-consent state for call recording, and Stanford Health
Care's own billing page already has a TCPA section, so plan on this being asked
about by judges.

## Architecture

```
Browser (templates/index.html, static/app.js)
   |  POST /api/analyze  (multipart: bill, eob)
   v
Flask (app.py)
   |  1. extract_line_items()   -> Gemini multimodal, structured JSON output
   |  2. find_duplicate_charges() -> deterministic Python, no model involved
   |  3. cross_check_eob()      -> deterministic Python
   |  4. check_unbundling()     -> stub, see above
   |  5. draft_dispute_letter() -> Gemini, grounded only in the flags found above
   v
JSON response -> rendered in the browser
```

## One-pager

See `ClearBill_AI_OnePager.docx` in the repo root for the pitch one-pager (problem,
market size, business model, ask).
