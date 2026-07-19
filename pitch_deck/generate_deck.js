const pptxgen = require("pptxgenjs");

// Brand tokens, matching the live product's design system.
const GREEN_DEEP = "1B4D38"; // title/close slide bg
const GREEN = "2E7D5B"; // primary accent
const GREEN_TINT = "E6F1EA";
const CREAM = "FCFBF9"; // light slide bg
const INK = "211F1B"; // body text
const MUTED = "68655A";
const GOLD = "B07A2C";
const GOLD_TINT = "F4E9D4";
const DANGER = "AB4A37";
const DANGER_TINT = "F5E2DB";
const WHITE = "FFFFFF";

const FONT_HEAD = "Cambria";
const FONT_BODY = "Calibri";

const TOTAL_SLIDES = 9;

function pres() {
  const p = new pptxgen();
  p.layout = "LAYOUT_WIDE"; // 13.3 x 7.5
  return p;
}

function darkSlide(p) {
  const s = p.addSlide();
  s.background = { color: GREEN_DEEP };
  return s;
}

function lightSlide(p) {
  const s = p.addSlide();
  s.background = { color: CREAM };
  return s;
}

function kicker(s, text, color = GREEN) {
  s.addText(text.toUpperCase(), {
    x: 0.6, y: 0.45, w: 8, h: 0.4,
    fontFace: FONT_BODY, fontSize: 13, bold: true, color,
    charSpacing: 2,
  });
}

function title(s, text, opts = {}) {
  s.addText(text, {
    x: 0.6, y: 0.8, w: 11.5, h: opts.h || 0.9,
    fontFace: FONT_HEAD, fontSize: opts.size || 34, bold: true, color: opts.color || INK,
    margin: 0,
  });
}

function pageNum(s, n, color = MUTED) {
  s.addText(`${n} / ${TOTAL_SLIDES}`, {
    x: 12.4, y: 7.05, w: 0.7, h: 0.3,
    fontFace: FONT_BODY, fontSize: 10, color, align: "right",
  });
}

function statCard(s, x, y, w, h, big, label, bigColor = GREEN) {
  s.addShape("roundRect", {
    x, y, w, h, rectRadius: 0.12,
    fill: { color: WHITE }, line: { color: "E7E3D9", width: 1 },
    shadow: { type: "outer", color: "211F1B", opacity: 0.12, blur: 8, offset: 3, angle: 90 },
  });
  s.addText(big, {
    x, y: y + 0.18, w, h: h * 0.55,
    fontFace: FONT_HEAD, fontSize: 40, bold: true, color: bigColor, align: "center", margin: 0,
  });
  s.addText(label, {
    x: x + 0.2, y: y + h - 0.62, w: w - 0.4, h: 0.5,
    fontFace: FONT_BODY, fontSize: 12.5, color: MUTED, align: "center", margin: 0,
  });
}

const doc = pres();

// ---------- Slide 1: Title ----------
{
  const s = darkSlide(doc);
  s.addShape("roundRect", {
    x: 0.6, y: 0.7, w: 0.75, h: 0.75, rectRadius: 0.16,
    fill: { color: GREEN }, line: { type: "none" },
  });
  s.addText("CB", {
    x: 0.6, y: 0.7, w: 0.75, h: 0.75,
    fontFace: FONT_HEAD, fontSize: 20, bold: true, color: WHITE, align: "center", valign: "middle", margin: 0,
  });
  s.addText("ClearBill AI", {
    x: 0.6, y: 2.35, w: 11.5, h: 1.2,
    fontFace: FONT_HEAD, fontSize: 56, bold: true, color: WHITE, margin: 0,
  });
  s.addText("Find the money hospitals didn't mean to bill you.", {
    x: 0.6, y: 3.55, w: 11, h: 0.55,
    fontFace: FONT_BODY, fontSize: 19, italic: true, color: "CFE3D8", margin: 0,
  });
  s.addText("49–80% of medical bills contain an error. Nobody catches it — because nobody has an hour to cross-reference their bill against their insurance paperwork by hand.", {
    x: 0.6, y: 4.35, w: 9.8, h: 1.1,
    fontFace: FONT_BODY, fontSize: 15, color: "8FB6A3", margin: 0, lineSpacingMultiple: 1.3,
  });
  s.addText("Stanford × DeepMind Hackathon  ·  Built on Gemini + Google Cloud Run", {
    x: 0.6, y: 6.55, w: 11, h: 0.4,
    fontFace: FONT_BODY, fontSize: 13, color: "8FB6A3",
  });
  s.addNotes(
    "[0:00-0:10 HOOK] Between 49 and 80 percent of medical bills in America contain an error. Nobody catches it, because nobody has an hour to cross-reference their bill against their insurance paperwork by hand."
  );
}

// ---------- Slide 2: The Problem ----------
{
  const s = lightSlide(doc);
  kicker(s, "The Problem");
  title(s, "Nobody has time to catch it, so everybody just pays");
  statCard(s, 0.6, 2.2, 3.7, 2.2, "49–80%", "of medical bills contain an error", GREEN);
  statCard(s, 4.6, 2.2, 3.7, 2.2, "$1,300", "avg. overcharge on a $10K+ bill", DANGER);
  statCard(s, 8.6, 2.2, 3.7, 2.2, "$220B", "medical debt held by 100M Americans", GOLD);
  s.addText(
    "Physicians lose an estimated $125B/yr and hospitals $68B/yr to billing mistakes system-wide. There's no standardized way to dispute a bill — every hospital routes it through its own phone line, mail address, or fax.",
    { x: 0.6, y: 4.9, w: 11.7, h: 1.2, fontFace: FONT_BODY, fontSize: 15, color: MUTED, margin: 0 }
  );
  s.addText("Sources: Medical Bill Rescue, Aptarro Healthcare Billing Statistics 2026", {
    x: 0.6, y: 6.85, w: 8, h: 0.3, fontFace: FONT_BODY, fontSize: 10, color: MUTED,
  });
  pageNum(s, 2);
  s.addNotes("(Visual support for the hook — no new spoken content here; keep talking through the hook while this is on screen.)");
}

// ---------- Slide 3: Team ----------
{
  const s = lightSlide(doc);
  kicker(s, "The Team");
  title(s, "Built by people who wanted to trust it themselves");

  const team = [
    ["[Name]", "[Role — one line of relevant background]"],
    ["[Name]", "[Role — one line of relevant background]"],
  ];
  team.forEach(([name, bio], i) => {
    const x = 0.6 + i * 6.0;
    s.addShape("ellipse", { x, y: 2.3, w: 1.1, h: 1.1, fill: { color: GREEN_TINT }, line: { type: "none" } });
    s.addText(
      name.replace(/\[|\]/g, "").split(" ").map((w) => w[0]).join("").slice(0, 2) || "??",
      { x, y: 2.3, w: 1.1, h: 1.1, align: "center", valign: "middle", fontFace: FONT_HEAD, bold: true, fontSize: 24, color: GREEN, margin: 0 }
    );
    s.addText(name, { x: x + 1.3, y: 2.45, w: 4.4, h: 0.45, fontFace: FONT_HEAD, bold: true, fontSize: 19, color: INK, margin: 0 });
    s.addText(bio, { x: x + 1.3, y: 2.9, w: 4.4, h: 0.9, fontFace: FONT_BODY, fontSize: 13, color: MUTED, margin: 0, lineSpacingMultiple: 1.3 });
  });

  s.addShape("roundRect", { x: 0.6, y: 4.5, w: 11.7, h: 1.8, rectRadius: 0.14, fill: { color: WHITE }, line: { color: "E7E3D9", width: 1 } });
  s.addText(
    "We built ClearBill AI this weekend because we wanted something we'd actually trust our own families to use the next time a hospital bill like this showed up.",
    { x: 1.0, y: 4.5, w: 10.9, h: 1.8, valign: "middle", fontFace: FONT_BODY, italic: true, fontSize: 16, color: INK, margin: 0, lineSpacingMultiple: 1.3 }
  );

  pageNum(s, 3);
  s.addNotes(
    "[0:10-0:22 TEAM] I'm [Name], [background]. This is [Name], [background]. We built ClearBill AI this weekend because we wanted something we'd actually trust our own families to use the next time a bill like this showed up."
  );
}

// ---------- Slide 4: The Insight ----------
{
  const s = lightSlide(doc);
  kicker(s, "The Insight");
  title(s, "The proof a bill is wrong is already in your hands");

  s.addText(
    "When an insurer marks a charge “denied — duplicate,” that's not our judgment.\nIt's the payer's own ruling.",
    { x: 0.6, y: 2.1, w: 6.6, h: 1.5, fontFace: FONT_BODY, fontSize: 19, color: INK, margin: 0, lineSpacingMultiple: 1.25 }
  );
  s.addText(
    "Nobody today cross-references the bill against the EOB by hand — it means reading two dense forms and matching line items by code and date. That's a narrow, mechanical task: exactly what a deterministic pipeline does well, with Gemini doing the document understanding and plain code doing the parts that must never hallucinate.",
    { x: 0.6, y: 3.75, w: 6.6, h: 2.3, fontFace: FONT_BODY, fontSize: 14.5, color: MUTED, margin: 0, lineSpacingMultiple: 1.3 }
  );

  s.addShape("roundRect", { x: 7.75, y: 2.15, w: 2.3, h: 1.5, rectRadius: 0.1, fill: { color: WHITE }, line: { color: "E7E3D9", width: 1 } });
  s.addText("Itemized Bill", { x: 7.75, y: 2.35, w: 2.3, h: 0.4, align: "center", fontFace: FONT_BODY, bold: true, fontSize: 12, color: INK, margin: 0 });
  s.addText("CPT 36415\nbilled twice", { x: 7.75, y: 2.85, w: 2.3, h: 0.7, align: "center", fontFace: FONT_BODY, fontSize: 11, color: MUTED, margin: 0 });

  s.addShape("roundRect", { x: 10.3, y: 2.15, w: 2.3, h: 1.5, rectRadius: 0.1, fill: { color: WHITE }, line: { color: "E7E3D9", width: 1 } });
  s.addText("Insurance EOB", { x: 10.3, y: 2.35, w: 2.3, h: 0.4, align: "center", fontFace: FONT_BODY, bold: true, fontSize: 12, color: INK, margin: 0 });
  s.addText("CARC 18:\ndenied duplicate", { x: 10.3, y: 2.85, w: 2.3, h: 0.7, align: "center", fontFace: FONT_BODY, fontSize: 11, color: MUTED, margin: 0 });

  s.addShape("roundRect", { x: 8.85, y: 4.0, w: 2.75, h: 0.85, rectRadius: 0.42, fill: { color: DANGER_TINT }, line: { type: "none" } });
  s.addText("$112 flagged", {
    x: 8.85, y: 4.0, w: 2.75, h: 0.85, align: "center", valign: "middle",
    fontFace: FONT_HEAD, bold: true, fontSize: 16, color: DANGER, margin: 0,
  });

  pageNum(s, 4);
  s.addNotes(
    "[0:22-0:48 INSIGHT + PRODUCT] Here's what nobody else does: the proof a bill is wrong is already in your hands. When your insurer denies a charge as a duplicate, that's their own ruling, not our opinion. Upload your bill and your EOB, and Gemini reads both, catches exact duplicates deterministically, cross-references what your insurer already denied, and drafts the dispute letter — citing the exact code and reason."
  );
}

// ---------- Slide 5: How it works ----------
{
  const s = lightSlide(doc);
  kicker(s, "The Product");
  title(s, "Upload. We check it. You dispute it.");

  const steps = [
    ["1", "Upload", "Your itemized bill, and your insurance statement if you have one"],
    ["2", "We check it", "Duplicate charges, and anything your insurer already denied"],
    ["3", "You dispute it", "A ready-to-send letter citing the exact lines and codes"],
  ];
  steps.forEach(([n, t, d], i) => {
    const x = 0.6 + i * 4.1;
    s.addShape("ellipse", { x, y: 2.3, w: 0.55, h: 0.55, fill: { color: GREEN_TINT }, line: { type: "none" } });
    s.addText(n, { x, y: 2.3, w: 0.55, h: 0.55, align: "center", valign: "middle", fontFace: FONT_HEAD, bold: true, fontSize: 16, color: GREEN, margin: 0 });
    s.addText(t, { x: x + 0.7, y: 2.32, w: 3.1, h: 0.4, fontFace: FONT_BODY, bold: true, fontSize: 15, color: INK, margin: 0 });
    s.addText(d, { x, y: 3.0, w: 3.7, h: 1.0, fontFace: FONT_BODY, fontSize: 12.5, color: MUTED, margin: 0, lineSpacingMultiple: 1.25 });
  });

  s.addShape("roundRect", { x: 0.6, y: 4.35, w: 11.7, h: 2.15, rectRadius: 0.14, fill: { color: WHITE }, line: { color: "E7E3D9", width: 1 } });
  s.addShape("roundRect", { x: 0.9, y: 4.6, w: 2.0, h: 0.4, rectRadius: 0.2, fill: { color: DANGER_TINT }, line: { type: "none" } });
  s.addText("DUPLICATE CHARGE", { x: 0.9, y: 4.6, w: 2.0, h: 0.4, align: "center", valign: "middle", fontFace: FONT_BODY, bold: true, fontSize: 9.5, color: DANGER, margin: 0 });
  s.addText("$112.00", { x: 10.3, y: 4.58, w: 1.9, h: 0.42, align: "right", fontFace: FONT_HEAD, bold: true, fontSize: 16, color: DANGER, margin: 0 });
  s.addText(
    "“Venipuncture, Routine Collection” (CPT 36415) was billed twice on Jul 10, 2026 — detected with plain line-count logic, not a model guess, so there's zero false-positive risk.",
    { x: 0.9, y: 5.15, w: 10.9, h: 0.7, fontFace: FONT_BODY, fontSize: 13, color: INK, margin: 0, lineSpacingMultiple: 1.25 }
  );
  s.addText("CPT 36415  ·  Jul 10, 2026  ·  high confidence", { x: 0.9, y: 5.95, w: 8, h: 0.35, fontFace: FONT_BODY, fontSize: 10.5, color: MUTED, margin: 0 });

  pageNum(s, 5);
  s.addNotes("(Continued visual for the 0:22-0:48 beat — this is the actual product, not a mockup.)");
}

// ---------- Slide 6: Proof it's real ----------
{
  const s = lightSlide(doc);
  kicker(s, "Technical Feasibility");
  title(s, "Built and verified, not just pitched");

  const checks = [
    ["Duplicate-charge detection", "Live-verified, deterministic, zero false-positive risk"],
    ["Bill-vs-EOB denial cross-check", "Live-verified — was silently broken, we found it and fixed it"],
    ["Dispute letter generation", "Live-verified, grounded only in flags actually found"],
    ["Automated test suite", "pytest: 27 passing, 0 failing"],
  ];
  checks.forEach(([t, d], i) => {
    const y = 2.15 + i * 0.68;
    s.addShape("ellipse", { x: 0.6, y: y + 0.03, w: 0.32, h: 0.32, fill: { color: GREEN }, line: { type: "none" } });
    s.addText("✓", { x: 0.6, y: y + 0.03, w: 0.32, h: 0.32, align: "center", valign: "middle", fontFace: FONT_BODY, bold: true, fontSize: 13, color: WHITE, margin: 0 });
    s.addText(t, { x: 1.1, y, w: 4.3, h: 0.35, fontFace: FONT_BODY, bold: true, fontSize: 13.5, color: INK, margin: 0 });
    s.addText(d, { x: 1.1, y: y + 0.32, w: 5.0, h: 0.35, fontFace: FONT_BODY, fontSize: 11.5, color: MUTED, margin: 0 });
  });
  s.addText("We deliberately do NOT claim to detect coding “unbundling” without the licensed CMS data behind it — roadmap, not pitch.", {
    x: 0.6, y: 5.1, w: 5.9, h: 0.6, fontFace: FONT_BODY, italic: true, fontSize: 11.5, color: MUTED, margin: 0,
  });

  s.addText("Real prices, Stanford Health Care's own published data", {
    x: 6.9, y: 2.1, w: 5.5, h: 0.35, fontFace: FONT_BODY, bold: true, fontSize: 13, color: INK, margin: 0,
  });
  const rows = [
    ["CPT", "Service", "Gross Charge"],
    ["99285", "ER visit, Level 5", "$15,270"],
    ["74177", "CT Abd-Pelvis w/Contrast", "$17,197"],
    ["80053", "Comprehensive Metabolic Panel", "$1,243"],
    ["36415", "Venipuncture", "$112"],
  ];
  s.addTable(
    rows.map((r, i) =>
      r.map((c) => ({
        text: c,
        options: {
          fontFace: FONT_BODY, fontSize: 11, color: i === 0 ? WHITE : INK, bold: i === 0,
          fill: { color: i === 0 ? GREEN : i % 2 === 0 ? WHITE : GREEN_TINT }, valign: "middle",
        },
      }))
    ),
    { x: 6.9, y: 2.55, w: 5.5, colW: [1.1, 3.1, 1.3], rowH: 0.42, border: { type: "solid", color: "E7E3D9", pt: 0.75 } }
  );
  pageNum(s, 6);
  s.addNotes(
    "[0:48-1:05 PROOF] We ran this live against Gemini, wrote 27 automated tests, and fixed two real bugs before this pitch. Every price is real — pulled from Stanford Health Care's own federal pricing data."
  );
}

// ---------- Slide 7: Why ClearBill Wins (differentiation) ----------
{
  const s = lightSlide(doc);
  kicker(s, "Why ClearBill Wins");
  title(s, "Not a weekend chatbot wrapper");

  const rows = [
    ["", "Generic AI Chatbot", "Manual Advocate\n(Resolve, GoodBill)", "ClearBill AI"],
    ["Accuracy", "Can hallucinate", "Accurate (human-reviewed)", "Deterministic — zero false positives"],
    ["Speed", "Instant", "Days to weeks", "Under 60 seconds"],
    ["Cost to patient", "Free / cheap", "25–35% contingency fee", "Free to start"],
    ["Follows through to refund", "No", "Yes", "Yes — on the roadmap"],
  ];
  s.addTable(
    rows.map((r, i) =>
      r.map((c, j) => ({
        text: c,
        options: {
          fontFace: FONT_BODY,
          fontSize: i === 0 ? 12.5 : 12,
          bold: i === 0 || j === 0 || j === 3,
          color: i === 0 ? WHITE : j === 3 && i > 0 ? GREEN : INK,
          fill: { color: i === 0 ? GREEN : j === 3 ? GREEN_TINT : i % 2 === 0 ? WHITE : "F6F5EE" },
          valign: "middle",
          align: j === 0 ? "left" : "center",
        },
      }))
    ),
    { x: 0.6, y: 2.15, w: 11.7, colW: [2.7, 2.9, 3.1, 3.0], rowH: 0.6, border: { type: "solid", color: "E7E3D9", pt: 0.75 } }
  );

  s.addText(
    "Every flag is grounded in deterministic logic or the insurer's own official denial code — never a model's guess. And we're building the full loop, from detection to a confirmed refund, not a one-time scan.",
    { x: 0.6, y: 5.55, w: 11.7, h: 0.9, fontFace: FONT_BODY, fontSize: 14, color: MUTED, italic: true, margin: 0, lineSpacingMultiple: 1.3 }
  );

  pageNum(s, 7);
  s.addNotes(
    "[1:05-1:25 WHY WE WIN] This isn't a chatbot wrapper. Every flag is grounded in deterministic code or your insurer's own official denial code — never a guess. And we're not building a one-time scanner. We're building the full loop: detect, dispute, follow up, and confirm the refund actually lands — which is the only reason a success fee makes sense."
  );
}

// ---------- Slide 8: Market & Go-to-Market ----------
{
  const s = lightSlide(doc);
  kicker(s, "Market Potential & Go-to-Market");
  title(s, "People already pay for this — slowly");

  statCard(s, 0.6, 2.15, 3.6, 1.5, "100M+", "Americans hold medical debt", GREEN);
  statCard(s, 4.35, 2.15, 3.6, 1.5, "1.5B", "medical bills issued/year in the US", GOLD);
  statCard(s, 8.1, 2.15, 4.2, 1.5, "25–35%", "contingency fees existing services already charge", DANGER);

  s.addShape("roundRect", { x: 0.6, y: 3.9, w: 5.6, h: 2.7, rectRadius: 0.14, fill: { color: GREEN_DEEP }, line: { type: "none" } });
  s.addText("“We found $112\nyou don't owe.”", {
    x: 0.9, y: 4.1, w: 5.0, h: 1.0, fontFace: FONT_HEAD, bold: true, fontSize: 20, color: WHITE, margin: 0, lineSpacingMultiple: 1.15,
  });
  s.addText(
    "Same content shape as viral tax-refund and settlement-check posts. We built a shareable result card for exactly this moment.",
    { x: 0.9, y: 5.15, w: 5.0, h: 1.3, fontFace: FONT_BODY, fontSize: 13, color: "CFE3D8", margin: 0, lineSpacingMultiple: 1.3 }
  );

  s.addText("Distribution already mapped", { x: 6.55, y: 3.9, w: 6, h: 0.35, fontFace: FONT_BODY, bold: true, fontSize: 13.5, color: INK, margin: 0 });
  [
    "r/personalfinance, r/HealthInsurance",
    "Patient-advocacy Facebook groups",
    "Employer benefits partnerships — 1 deal reaches thousands of employees",
  ].forEach((t, i) => {
    const y = 4.35 + i * 0.72;
    s.addShape("roundRect", { x: 6.55, y, w: 5.6, h: 0.6, rectRadius: 0.1, fill: { color: WHITE }, line: { color: "E7E3D9", width: 1 } });
    s.addText(t, { x: 6.8, y, w: 5.1, h: 0.6, valign: "middle", fontFace: FONT_BODY, fontSize: 12, color: INK, margin: 0, lineSpacingMultiple: 1.15 });
  });

  pageNum(s, 8);
  s.addNotes(
    "[1:25-1:45 MARKET + GTM] A hundred million Americans carry medical debt. Services that do this by hand already charge 25 to 35 percent — proof people already pay for this, just slowly. And a confirmed refund is inherently shareable: same content shape as every viral tax-refund post, distributed straight into the communities already talking about this."
  );
}

// ---------- Slide 9: Ask ----------
{
  const s = darkSlide(doc);
  kicker(s, "The Ask", "8FB6A3");
  s.addText("Give us two minutes with your bill.", {
    x: 0.6, y: 1.3, w: 11.5, h: 1.1, fontFace: FONT_HEAD, bold: true, fontSize: 38, color: WHITE, margin: 0,
  });
  s.addText("We'll show you exactly what it caught.", {
    x: 0.6, y: 2.2, w: 11, h: 0.6, fontFace: FONT_BODY, italic: true, fontSize: 18, color: "CFE3D8", margin: 0,
  });

  s.addText("Seeking", { x: 0.6, y: 3.4, w: 5, h: 0.4, fontFace: FONT_BODY, bold: true, fontSize: 14, color: "8FB6A3", margin: 0 });
  s.addText(
    "Not raising today. Thirty minutes with a fund that has real conviction in consumer healthcare fintech — to pressure-test the data-access strategy and the recovery-verification model the success fee depends on.",
    { x: 0.6, y: 3.8, w: 9.5, h: 1.1, fontFace: FONT_BODY, fontSize: 15, color: "CFE3D8", margin: 0, lineSpacingMultiple: 1.3 }
  );

  s.addText("Team", { x: 0.6, y: 5.2, w: 5, h: 0.4, fontFace: FONT_BODY, bold: true, fontSize: 14, color: "8FB6A3", margin: 0 });
  s.addText("[Name] · [Name]", {
    x: 0.6, y: 5.6, w: 6, h: 0.5, fontFace: FONT_BODY, fontSize: 15, color: WHITE, margin: 0,
  });

  s.addText("github.com/LilChainyy/stanford_med", {
    x: 0.6, y: 6.7, w: 8, h: 0.4, fontFace: FONT_BODY, fontSize: 13, color: "8FB6A3",
  });
  s.addNotes(
    "[1:45-2:00 CLOSE] We're ClearBill AI. Give us two minutes with your bill, and we'll show you what it caught."
  );
}

doc.writeFile({ fileName: "ClearBill_AI_Pitch_Deck.pptx" }).then(() => console.log("done"));
