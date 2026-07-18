# ClearBill AI — Submission Package

Everything needed for the 2:30 PM submission, in order. Items 2–4 need you to
actually execute them (deploy, record) — everything that can be pre-written
is pre-written below so execution is mechanical, not creative, on demo day.

---

## 1. One-Pager — ✅ done

`ClearBill_AI_OnePager.docx` in repo root. Rewritten to fix the one real gap
a judge who knows medical coding would have caught: it no longer claims we
detect NCCI "unbundling" violations (that's a stub — see `check_unbundling()`
in `app.py`). It now leads with what's actually real and tested: duplicate
detection and the bill-vs-EOB cross-check, plus a "Built and Verified"
section that states outright that we ran the live pipeline, wrote tests, and
fixed two real bugs before submitting — that's a credibility signal most
hackathon one-pagers don't have, so it's worth judges reading it, not cutting
it for space.

**Still needed from you:** real team names/roles in the last section (2 min).

---

## 2. Hosted Prototype — deploy checklist

`pytest tests/` is 8/8 passing and the app boots keyless right now — it's
ready to deploy as-is. Do this in order:

1. **Get a paid-tier Gemini key first.** Your teammate's plan doc flagged the
   free tier caps at 20 requests/day and one analysis = 3 calls (~6 runs/day)
   — easy to burn through in rehearsal before judges ever see it. Enable
   billing on the AI Studio key, or bring a second funded key as backup.
2. Go to [console.cloud.google.com/run](https://console.cloud.google.com/run)
   → **Create Service** → **Continuously deploy from a repository** → connect
   GitHub → select `LilChainyy/stanford_med`, branch `main`, build type
   **Dockerfile** (already Cloud-Run-ready — `$PORT` handling and a 120s
   timeout for the 3-call Gemini chain are already in there).
3. Add env var `GEMINI_API_KEY` = your paid-tier key. Optionally set
   `FAX_PROVIDER` if you've wired up Documo/Notifyre by then; otherwise leave
   it at `dryrun`.
4. **Allow unauthenticated invocations** — judges need to hit the URL without
   logging into anything.
5. Deploy. Copy the `*.run.app` URL — that's the Hosted Prototype link.
6. **Before you submit the link, load it and click "Use sample bill" →
   "Analyze Bill" yourself.** Confirm it actually completes a real Gemini
   round trip on the live URL, not just localhost. This takes 60 seconds and
   catches the one class of bug that only shows up in the deployed
   environment (missing env var, wrong port, cold-start timeout).

---

## 3. Two-Minute Video — Team Intro & Elevator Pitch

Timed script, ~290 words at a natural pace. Swap `[Name]` / `[background]`
for real people before recording — don't perform this with placeholders in.

**[0:00–0:15] Hook — one person, straight to camera**
> "Between 49 and 80 percent of medical bills in America have an error in
> them. On a $10,000 bill, that's an average $1,300 overcharge. Almost
> nobody catches it — not because the errors are subtle, but because nobody
> has an hour to cross-reference their bill against their insurance
> paperwork line by line. We built the thing that does."

**[0:15–0:40] Team — second person**
> "I'm [Name], [one line: background relevant to healthcare, data, or
> building things fast]. This is [Name], [same]. We're [Wharton MBA /
> Stanford / relevant program], and we spent this hackathon building
> something we'd actually want our own families to use the next time a
> hospital bill shows up."

**[0:40–1:20] What we built — trade off lines or one person**
> "ClearBill AI reads your itemized bill and your insurance EOB side by
> side. It catches exact duplicate charges — deterministically, not a model
> guess, so there's zero false-positive risk. And it catches something more
> interesting: when your insurer has *already* denied a charge as a
> duplicate, using their own official denial code, but the hospital billed
> you for it anyway. We didn't just prompt this and hope — we ran it live
> against Gemini, wrote an automated test suite, and caught two real bugs
> before this pitch, including a cross-check that was silently never firing.
> We fixed both. That's the standard we held ourselves to."

**[1:20–1:50] Why it matters / market**
> "This isn't a niche problem. A hundred million Americans carry medical
> debt. One and a half billion medical bills go out every year in the U.S.
> Services that do this by hand already charge 25 to 35 percent contingency
> fees — people are already paying for this, just slowly and manually. We
> made it instant."

**[1:50–2:00] Close**
> "We're ClearBill AI, and we'd love the chance to show you what it caught
> on a real bill in the next two minutes."

---

## 4. One-Minute Demo Video (Playcast) — shot list

Screen recording, no live narration needed over the clicks except where
noted — voiceover can be added after. Practice the click sequence twice
before recording; it should take under 45 seconds of actual clicking, leaving
room for the intro/outro card.

| Time | Action | On-screen / voiceover |
|---|---|---|
| 0:00–0:04 | Title card | "ClearBill AI — find the money hospitals didn't mean to bill you" |
| 0:04–0:10 | Land on the app | VO: "Upload your bill and your insurance EOB — or try it right now with a real Stanford Health Care bill." Click **Use sample bill**. |
| 0:10–0:14 | Files populate (show the green "has-file" state on both dropzones) | — |
| 0:14–0:16 | Click **Analyze Bill** | — |
| 0:16–0:20 | Loading state (pulse dots + cycling text) | VO: "In under a minute, it extracts every line item and checks it two ways." |
| 0:20–0:32 | Results appear — **hold on the summary stat box** ($34,379 billed / $112 flagged) then scroll to the two flag cards | VO: "First — an exact duplicate charge, caught with plain code logic, not a guess. Second — a charge the insurer already denied as a duplicate, using their own denial code, that the hospital billed anyway." |
| 0:32–0:45 | Scroll to the Draft Dispute Letter, show it's pre-filled and editable | VO: "It drafts the dispute letter, citing the exact code, date, and reason — ready to edit and send." |
| 0:45–0:55 | Click **Send Fax** *(if wired to a real provider by demo day — otherwise cut this beat and hold longer on the letter)* | VO: "And if you want, it's already on its way to their billing office." |
| 0:55–1:00 | End card | URL + "ClearBill AI — Stanford × DeepMind Hackathon" |

**If auto-fax isn't live yet by recording time:** don't fake it. Cut straight
from the letter to the end card at 0:45 and let the letter be the closing
beat — a real, grounded artifact is a stronger closer than a feature that
might visibly fail on camera. IVR/phone-call demos specifically should never
be attempted live per your teammate's plan notes; same logic applies here.

---

## 5. Code Repository

Link: **https://github.com/LilChainyy/stanford_med**

On the AI Studio sharing-mechanics wording in the official rule: send the
organizers a quick message asking whether a GitHub link satisfies rule #5 —
most hackathons accept it in practice, and it's a 30-second question versus
hours re-platforming tested code into AI Studio's generate-from-prompt flow
(which would discard the two verified checks and the test suite to
regenerate untested code from scratch). Ask before assuming either way.

The README's top section states the real, verified status up front
(duplicate detection + EOB cross-check both live-verified, unbundling
explicitly marked as not implemented) so a judge skimming the repo for 30
seconds gets an accurate picture without reading the whole file.
