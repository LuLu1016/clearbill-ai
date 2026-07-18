# Prompt for Google AI Studio Build mode

Paste this as the initial "Build" prompt. It describes the app precisely
enough (exact logic, exact copy, exact design tokens) that what Gemini
generates should closely match what's already tested in `app.py` — not just
the same idea, the same behavior.

---

```
Build a web app called "ClearBill AI" — a medical bill dispute assistant.
Tagline: "Find the money hospitals didn't mean to bill you."

FLOW
Two file uploads: "Itemized Bill" (required, PDF or image) and "Insurance
Statement (EOB)" (optional, PDF or image, hint text: "the notice your
insurer sends after processing a claim"). A primary "Analyze Bill" button
(disabled until a bill is attached) and a secondary "Use sample bill" button
that loads two pre-made sample files.

On analyze, call gemini-3-flash-preview twice with structured JSON output:

1. Extract line items from the bill: for each line return date (normalize to
   YYYY-MM-DD), code (bare CPT/HCPCS, uppercase, no punctuation), modifier,
   description (as printed), amount (plain number, no currency symbols).
   Skip subtotals/totals/payment rows. Extract ONLY what's printed — never
   invent a value.

2. If an EOB was uploaded, extract its lines the same way, plus:
   denial_status (paid / denied / partially_paid / unknown), denial_reason
   (verbatim text), carc_code (bare code, e.g. "CARC 18" -> "18"),
   patient_responsibility (number).

THE TWO CHECKS — BOTH MUST BE PLAIN CODE, NEVER A MODEL JUDGMENT CALL

Check 1 — Duplicate charge: group bill line items by (code, date). Any group
with more than one item is a duplicate-charge flag. overcharge_amount = sum
of all occurrences except the first. Explanation should lead with the plain
description from the bill, not the bare code, e.g. "'Venipuncture, Routine
Collection' (CPT 36415) was billed 2 times on Jul 10, 2026." — reformat the
internal YYYY-MM-DD date to "Jul 10, 2026" style ONLY in text a human reads,
never in the matching logic itself.

Check 2 — Denied but still billed: for every EOB line with
denial_status == "denied", look up the same (code, date) key in the bill
items. If it exists there too, flag it. overcharge_amount = the EOB line's
billed_amount (not patient_responsibility — a denied line's
patient_responsibility is correctly $0, that IS the point). If the EOB's
denial_reason text already starts with the CARC code being cited (e.g.
"CARC 18 -- Exact duplicate claim/service"), strip that repeated prefix
before composing the sentence "(CARC 18: Exact duplicate claim/service)" —
don't let it read "(CARC 18: CARC 18 -- ...)".

Do NOT build a third check for coding "unbundling" (NCCI edits) — that
requires CMS's official Procedure-to-Procedure edit tables, which require an
AMA license to access. Leave it out entirely rather than approximate it from
general medical knowledge; a wrong bundling claim is worse than no claim.

If any flags were found, make one more gemini-3-flash-preview call to draft
a dispute letter addressed to the provider's billing office, referencing
ONLY the specific flagged issues (pass them as JSON context), polite and
factual, never accusing the hospital of fraud, asking for a corrected
itemized statement. If zero flags, don't generate a letter — show "No
issues found in this bill" instead.

RESULTS UI
A "Billing Health Report" card: total billed, amount flagged for review (sum
of overcharge_amount across flags — if a duplicate charge is also the
denied-EOB line, don't double count the same dollar twice in this total,
each flag can still display its own amount), and "N issues found across N
line items." Below it, one card per flag with a category pill (uppercase,
tinted background), the dollar amount, the plain-language explanation, and a
small meta line "CPT {code} · {friendly date} · {confidence} confidence."
Then an editable dispute-letter textarea with Copy and Send Fax buttons
(Send Fax can be a stub that shows a toast saying it's not connected to a
live provider yet). A "Start over" button clears everything.

COPY VOICE
Plain language first, jargon in parentheses second, always. Never say
"AI-powered" or "smart" anywhere in the UI. Loading state cycles through:
"Extracting line items…" / "Checking for duplicate charges…" /
"Cross-referencing your EOB…" / "Drafting your dispute letter…".

DESIGN
Warm, humanistic, professional — the opposite of a generic AI-tool look.
No purple/blue gradients, no glow effects, no sparkle icons, no monospace
"terminal" styling anywhere, no serif display font. One warm humanist sans
throughout (system font stack: -apple-system, "Avenir Next", "Segoe UI").
Palette: soft warm off-white background (#fcfbf9), white cards, deep forest
green as the single accent (#2e7d5b) used flat with no gradient, a warm gold
used sparingly for a small "preview" badge only, warm red-brown for danger/
flagged amounts (#ab4a37) — semantic color, kept separate from the accent.
Generous whitespace, soft shadows, pill-shaped buttons, rounded document
icons with a folded corner (not a generic outline glyph), a three-dot pulse
animation for loading (not a spinning ring). Respect
prefers-reduced-motion. Support both light and dark color schemes via CSS
custom properties.

Above the upload card, show a "why this matters" stat strip with three
numbers: "49-80%" (of medical bills contain an error), "$1,300" (avg.
overcharge on a $10k+ bill), "60 sec" (to check yours, free) — cite "Medical
Bill Rescue, Aptarro Healthcare Billing Statistics 2026" underneath in small
text. Below that, a 3-step "How it works": 1) Upload — your itemized bill,
and your insurance statement if you have one; 2) We check it — duplicate
charges, and anything your insurer already denied; 3) You dispute it — a
ready-to-send letter citing the exact lines and codes.
```

---

## Good follow-up prompts once the base app is generated

Use these one at a time inside the same AI Studio Build session to extend
it — each is scoped to one change so you can verify it didn't regress
anything before stacking the next one.

1. **Wire up real auto-fax:**
   > "Add a real fax-sending integration to the Send Fax button. Render the
   > dispute letter to a PDF, then POST it to Documo's fax API using an
   > environment variable for the API key. Prompt the user for the
   > destination fax number first, validate it's at least 10 digits, and
   > show a clear success/error message. Default to a 'dryrun' mode that
   > just logs what would have been sent, so it's safe to test without a
   > real account."

2. **Add real bill-price validation:**
   > "Add a reference lookup: after extracting bill line items, compare each
   > CPT code's charged amount against a small built-in table of Stanford
   > Health Care's published gross charges for these codes: 99285 $15,270,
   > 74177 $17,197, 80053 $1,243, 85025 $445, 36415 $112. If a charge
   > exceeds the reference by more than 20%, add an informational note (not
   > a flag) suggesting the patient verify the rate — label it clearly as a
   > reference comparison, not a claim of an error."

3. **Improve accessibility:**
   > "Add aria-live to the loading region, visible focus states on every
   > interactive element, and make sure the flag cards' color-only severity
   > indicator (the red left border) is backed up by the text label too."

Don't ask it to add the NCCI unbundling check unless you've actually
obtained the licensed CMS edit data first — see the README for why.
