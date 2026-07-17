---
name: clearbill-ai-context
description: Loads full context on the ClearBill AI project for the Stanford x DeepMind Hackathon (July 19, 2026) -- the pitch, the research behind it, what's built, and what's still open. Use this whenever a teammate asks about ClearBill AI, this hackathon project, the medical billing demo, the one-pager, or wants to keep building / debugging / preparing the pitch for it. Also use it if someone asks "what is this repo" or "catch me up" in this codebase, or wants a new hackathon idea evaluated against the same bar this one was held to.
---

# ClearBill AI — project context

Read this whole file before touching the code or the pitch. It's the compressed
output of a long ideation session -- it'll save you from re-deriving decisions
that were already made (and rejected) for specific reasons.

## The event

[Stanford x DeepMind Hackathon](https://luma.com/e51fygtm), Sunday July 19, 2026,
291 Campus Drive, Stanford. 3-hour build sprint (11:30am-2:30pm PT hard deadline),
then semi-finals -> live finals pitch (5 min pitch + 5 min Q&A) in front of a VC
judging panel. Winners get 30-min pitch meetings with funds writing $500K-$5M
checks -- the prize is pitch access, not guaranteed investment.

Submission requires: one-pager, hosted prototype (Google AI Studio / Cloud Run),
2-min team video, 1-min demo video, code repo link. Judged on technical
feasibility, innovation, real-world applicability, market potential/fundability,
and go-to-market traction (social engagement on the demo video matters).

## The idea-selection bar (why this idea, not the others)

Before landing on ClearBill AI, we screened ~15 ideas against a framework from the
user's own past hackathon experience: winning projects are either (a) technically
deep enough to be paper-grade -- rare, hard in 3 hours -- or (b) go genuinely deep
into one vertical, backed by real data, not something "thought up on the spot."
Market size matters too. Ideas without a real practitioner on the team or without
verifiable stats were filtered out (e.g. an SSDI appeal assistant and a job-search
triage tool scored well on data but got deprioritized by the user for other
reasons; a freelancer-late-payment tool was dropped for being too crowded already
-- Bonsai/HoneyBook/FreshBooks already own that space).

ClearBill AI survived because every claim in the pitch traces to a citable source
-- see "Grounding" below. If you extend this idea, keep that bar: don't add a
flag or a stat you haven't verified.

## The pitch (one-pager)

Full one-pager: `ClearBill_AI_OnePager.docx` in repo root. Summary:

- **Problem**: 49-80% of US medical bills contain errors (multiple studies);
  $10K+ bills average $1,300 in overcharges; $88B/year lost to billing mistakes;
  100M Americans hold $220B in medical debt. No standardized dispute channel --
  every hospital has its own phone/mail/fax process.
- **Solution**: upload an itemized bill + EOB -> Gemini multimodal extracts line
  items -> deterministic duplicate-charge detection -> EOB cross-check -> Gemini
  drafts a dispute letter -> (roadmap) auto-fax it.
- **Business model**: freemium scan + success fee on recovered savings, or
  B2B2C via employer benefits / patient advocacy nonprofits.
- **Team**: still a placeholder in the docx -- fill in names/roles before
  submission.

## Grounding: don't state anything here isn't verified

- **Real dollar amounts** in the demo bill/EOB come directly from Stanford Health
  Care's own CMS-mandated price transparency file (updated 2026-04-01), not
  invented numbers. See `demo_assets/stanford_cpt_reference.json` for the source
  URL and the 9 CPT codes we pulled (ER visits, CT scans, metabolic panels, CBC,
  venipuncture).
- **Duplicate-charge detection is the one flag we're fully confident in** --
  same CPT code + same date billed twice is checked with plain Python, not model
  judgment (`find_duplicate_charges` in `app.py`). Zero false-positive risk. This
  is the flag to lead with live on stage.
- **Unbundling (NCCI PTP edits) is deliberately NOT implemented.** CMS publishes
  the official rule tables for which CPT code pairs can't be billed together, but
  the raw files sit behind an AMA CPT license click-through we haven't accepted.
  Earlier in this project we guessed a specific bundled pair (80048+80053) from
  panel-composition logic and it turned out uncertain -- don't repeat that
  mistake. If you want this flag for real, either accept the AMA license and wire
  `check_unbundling()` up to the actual file, or verify pairs through a
  non-gated reference (Find-A-Code, AAPC) before claiming them in front of
  anyone who knows medical coding -- there may be judges who do.
- **There is no standardized bill-dispute submission channel** in the US
  healthcare system -- no API, no universal portal. Every hospital uses its own
  phone/mail/fax/patient-portal process. Don't build or imply an auto-submit-to-
  any-hospital feature; it isn't buildable and claiming it will read as fabricated
  to anyone in the industry. Auto-fax to a specific number is realistic (see
  Roadmap); auto-phone-calling is real but riskier live (see Roadmap).

## Architecture

```
Browser (templates/index.html, static/app.js)
   |  POST /api/analyze  (multipart: bill, eob)
   v
Flask (app.py)
   |  1. extract_line_items()     -> Gemini multimodal, structured JSON output
   |  2. find_duplicate_charges() -> deterministic Python, no model involved
   |  3. cross_check_eob()        -> deterministic Python
   |  4. check_unbundling()       -> stub, see Grounding section above
   |  5. draft_dispute_letter()   -> Gemini, grounded only in flags found above
   v
JSON response -> rendered in the browser
```

Full setup/run/deploy instructions are in `README.md` -- read that before asking
"how do I run this." Short version: `python3 -m venv venv && source venv/bin/
activate && pip install -r requirements.txt`, copy `.env.example` to `.env` and
add a Gemini key from https://aistudio.google.com/apikey, then `python app.py`.

## Demo assets

`demo_assets/sample_itemized_bill.pdf` and `sample_eob.pdf` -- synthetic (fake
patient, real prices) test files. The bill has a duplicated venipuncture line
(CPT 36415 billed twice); the EOB shows the insurer already denied the duplicate.
Regenerate with `python demo_assets/generate_demo_docs.py` if you need to change
the scenario. **Never test the fax/call features against a real hospital's real
number** -- use your own phone/test inbox until there's an actual bill to dispute.

## What's still open (pick these up first)

1. Team names/roles missing from the one-pager -- fill in before submission.
2. No Gemini API key configured in this repo (none of us have put a real one in
   `.env` yet) -- the full pipeline hasn't been run end to end against live Gemini,
   only unit-tested for the deterministic parts.
3. Auto-fax (`/api/send-fax` in `app.py`) is a stub. Roadmap: wire up a fax API
   (Documo/mFax, Notifyre, Sfax) -- straightforward, do this before the live demo
   since it's a strong on-stage moment.
4. Auto-phone-call (Gemini Live API + Twilio Voice) is real but don't attempt it
   live on stage -- IVR menus and call pickup are unpredictable. Pre-record a
   successful call for the 1-min demo video instead, and mention CA's two-party
   consent-to-record rule (Stanford Health Care's own billing page already has a
   TCPA section -- cite that if a judge asks about compliance).
5. Unbundling detection -- see Grounding section. Don't ship this flag without
   verifying against real NCCI data first.

## Repos

- https://github.com/LuLu1016/clearbill-ai (personal copy)
- https://github.com/LilChainyy/stanford_med (team working repo -- use this one)
