# Prompt: expand ClearBill AI's data sources beyond the Stanford demo

Use these one at a time (in AI Studio or directly against `app.py`) — each is
scoped to one integration so you can verify it before stacking the next.
Ordered by how free/easy each data source actually is to get, not by
importance.

---

## 1. CARC/RARC code lookup table (do this first — free, no account needed)

```
Add a local reference table for Claim Adjustment Reason Codes (CARC) and
Remittance Advice Remark Codes (RARC), sourced from the official public list
at x12.org/codes (maintained by the Washington Publishing Company / X12).
Store it as a JSON file (code -> plain-language description) bundled with
the app, not a live API call.

Update extract_eob_line_items so that after Gemini extracts a bare carc_code
from the EOB, the app looks up the full official description from this
table -- don't rely on Gemini to have memorized what every CARC code means,
and don't trust the "denial_reason" text as printed on the EOB alone, since
some EOBs print it abbreviated or not at all. If the code isn't in the
table, fall back to whatever text was extracted from the document.

This removes the current hardcoding: cross_check_eob only handles CARC 18
correctly today because that's the one code in the demo EOB. A real bill's
EOB could cite any of ~200 active CARC codes.
```

## 2. NPI Registry lookup (free CMS API, no key required)

```
Add a lookup against the CMS NPPES NPI Registry public API
(https://npiregistry.cms.hhs.gov/api/) to validate and enrich provider
information. After extracting the billing provider's name from the bill,
query the registry to confirm the NPI is real and pull the provider's
registered mailing address. Use this to auto-fill the "send to" address on
the generated dispute letter and, later, the fax number field, instead of
requiring the patient to find and type it themselves.

Handle the case where the provider isn't found (name mismatch, extraction
error) by falling back to whatever address was printed on the bill itself
-- never block letter generation on this lookup succeeding.
```

## 3. Medicare Physician Fee Schedule benchmark (free CMS data, bigger integration)

```
Add a reference dataset from CMS's Physician Fee Schedule (the public PFS
Relative Value Files) so that alongside each flagged charge, the dispute
letter can cite what Medicare pays for the same CPT code as an additional
data point -- e.g. "Medicare's reimbursement rate for CPT 74177 in this
region is $X, for context." This is not a claim that the hospital
overcharged relative to Medicare (private-pay rates are legitimately
different) -- frame it strictly as informational context that strengthens
the patient's negotiating position, and say so explicitly in the letter
template so it can't be read as an accusation.
```

## 4. Multi-hospital price transparency (bigger scope -- pick ONE approach)

```
Currently the app's price-benchmark logic (if any) is hardcoded to Stanford
Health Care's own published CMS price transparency file. To generalize
beyond one hospital, integrate with Turquoise Health's price transparency
API (https://turquoise.health -- commercial, has a free tier) instead of
parsing individual hospitals' raw machine-readable files directly, since
those files vary wildly in format and compliance quality across providers.
Given a hospital name or NPI extracted from the bill, query Turquoise
Health for that hospital's published rates on the flagged CPT codes, and
use it the same way the Stanford data is used now -- as supporting evidence
in the dispute letter, never as the basis for the duplicate-charge or
denied-but-billed checks, which must stay purely deterministic and
independent of any pricing lookup.
```

## Not worth prompting Gemini for -- do these by hand instead

- **Insurance payer appeals-department directory** (fax/address for
  UnitedHealth, Anthem, Aetna, Cigna, etc.) — no clean free API exists for
  this; it needs to be manually researched and hardcoded as a small lookup
  table. Ask Gemini to help you *format* that table once you have the real
  contact info, not to invent the contact info itself.
- **NCCI PTP/MUE edit tables** — already covered in `AI_STUDIO_PROMPT.md`'s
  warning: don't prompt this into existence without the actual licensed CMS
  data behind it. Same rule applies here.
- **Application database** (user accounts, saved bills, dispute-status
  tracking) — this is a real infrastructure decision (Postgres vs.
  Firestore, auth provider, schema design) that's worth making deliberately
  with a human, not delegating to a single generation prompt.
