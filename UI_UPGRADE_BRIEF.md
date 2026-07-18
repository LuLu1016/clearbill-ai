# UI instruction: elevate ClearBill AI to a top-tier business website

What exists today is a well-crafted **utility tool** — one flow, upload to
result, clean and warm. A "top business website" is a different job: it has
to sell the company in the first five seconds, build trust before anyone
touches the product, and only THEN hand them the tool. That's a landing page
wrapped around the tool, not a redecorated version of the tool.

Reference bar, for calibration: **Ramp, Mercury, Linear, Rocket Money
(Truebill)** — the last one especially, since it's a direct category peer
(consumer bill-savings) that already made these decisions well. Not Stripe —
Stripe's audience is developers; yours is a stressed patient and a VC judge
in the same thirty seconds, which is a harder brief.

## Page structure (top to bottom)

1. **Sticky nav** — logo mark, 2–3 anchor links (How it works, Proof it's
   real), one CTA button ("Check your bill") that jumps to the tool. Nav
   goes from transparent to a soft shadowed bar on scroll.

2. **Hero** — this is the thesis, not a banner. Bold headline (keep "Find
   the money hospitals didn't mean to bill you" — it's already good, don't
   replace a working line for the sake of change), one supporting sentence,
   primary CTA. Pair it with a **real visual**, not decoration: a framed
   mockup of the actual Billing Health Report card showing the $112 flag —
   proof, in the hero, before any explanation. This is the single place to
   spend your boldest visual idea; everything below stays quieter.

3. **Trust bar** — small, immediately below the hero: "Built on Stanford
   Health Care's own published CMS pricing data" + a one-line credibility
   stat ("49–80% of medical bills contain an error"). This is doing the job
   a logo bar does on a B2B site, adapted for a consumer product with no
   customers yet — cite the data, not customers you don't have.

4. **Problem, with motion** — the existing three stats, but let them count
   up on scroll into view rather than appearing static. One well-placed
   animation reads as craft; five of them read as a template.

5. **How it works** — keep the 3-step structure, give it more visual
   weight: each step gets a small illustrative mockup fragment (a cropped
   piece of the actual UI — the dropzone, the flag card, the letter), not a
   generic icon. Connect the three with a subtle line so it reads as a
   sequence, since it genuinely is one.

6. **Proof it's real** — promote the "Built and Verified" story from the
   one-pager onto the site itself: real bugs found and fixed, tests
   passing, Stanford's own data. This is your actual differentiator versus
   every other hackathon demo — a section built specifically to make that
   land visually (not just a paragraph) is worth the effort.

7. **Try it** — the actual functional tool, unchanged in logic, dropped in
   as its own section lower on the page rather than being the entire page.

8. **FAQ / objection handling** — 3–4 questions a skeptical patient or a
   privacy-conscious judge would actually ask: "Is this legal advice?" (no),
   "What happens to my data?", "Does this cost anything?", "What if it
   doesn't find anything?". Answering objections before they're asked is
   what makes a site feel trustworthy rather than just polished.

9. **Footer** — links, hackathon attribution, the "not legal/medical
   advice" disclaimer (currently a footer line — keep it, just give it a
   proper footer instead of a single sentence under the tool).

## Visual craft to add

- **Real type scale with intentional contrast** — the hero headline should
  be dramatically larger than anything else on the page (think 4.5–5.5rem
  on desktop); body copy stays where it is. Bigger contrast between largest
  and smallest text reads as "designed," not just "styled."
- **Motion, used once, deliberately** — scroll-triggered reveals on section
  entry (fade + slight rise, ~400ms, respect `prefers-reduced-motion`), a
  hover lift on the CTA and on the flag-card mockups. Don't animate
  everything; an orchestrated page-load or scroll sequence beats scattered
  hover effects everywhere.
- **Asymmetry** — break the current single centered 600px column at least
  once, in the hero or the proof section, so the page doesn't read as one
  long vertical stack.
- Keep every constraint from the current design system: no purple/blue
  gradients, no glow, no sparkle icons, no monospace "terminal" styling, no
  serif — those choices were made deliberately to avoid a generic AI-tool
  look, and a landing page is exactly where that look is most tempting to
  fall back into.

## Before you commit to this

This is realistically 3–5x the build effort of what exists now — a proper
multi-section landing page with scroll motion is a different project than a
single-flow tool, and your submission deadline is Sunday. Two honest paths:

- **If judging time is short and 1:1** (a judge opens one link and clicks
  through), the current tool-first page may actually convert better — it
  gets to the proof in one click instead of asking someone to scroll past a
  pitch first.
- **If this is also going to live beyond the hackathon** (LinkedIn/X posts,
  cold outreach, an actual landing page you'll point people to), the
  upgrade is worth it — that audience judges the company from the page
  before they ever touch the product.

Want me to build this now, or should we get the Cloud Run deploy and videos
done first and treat this as a post-hackathon upgrade?
