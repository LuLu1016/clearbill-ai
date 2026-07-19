const {
  Document, Packer, Paragraph, TextRun, HeadingLevel, Table, TableRow, TableCell,
  WidthType, ShadingType, BorderStyle, AlignmentType, LevelFormat, convertInchesToTwip
} = require("docx");

const PAGE_WIDTH = 12240;
const PAGE_HEIGHT = 15840;
const MARGIN = 630; // ~0.44"

function statBlock(items) {
  return new Table({
    width: { size: PAGE_WIDTH - 2 * MARGIN, type: WidthType.DXA },
    columnWidths: items.map(() => (PAGE_WIDTH - 2 * MARGIN) / items.length),
    rows: [
      new TableRow({
        children: items.map(
          (it) =>
            new TableCell({
              width: { size: (PAGE_WIDTH - 2 * MARGIN) / items.length, type: WidthType.DXA },
              shading: { type: ShadingType.CLEAR, fill: "F1F0E8" },
              margins: { top: 140, bottom: 140, left: 140, right: 140 },
              borders: {
                top: { style: BorderStyle.SINGLE, size: 2, color: "DDD9C8" },
                bottom: { style: BorderStyle.SINGLE, size: 2, color: "DDD9C8" },
                left: { style: BorderStyle.SINGLE, size: 2, color: "DDD9C8" },
                right: { style: BorderStyle.SINGLE, size: 2, color: "DDD9C8" },
              },
              children: [
                new Paragraph({
                  alignment: AlignmentType.CENTER,
                  children: [new TextRun({ text: it.big, bold: true, size: 28, color: "2E7D3B" })],
                }),
                new Paragraph({
                  alignment: AlignmentType.CENTER,
                  spacing: { before: 30 },
                  children: [new TextRun({ text: it.label, size: 15, color: "555248" })],
                }),
              ],
            })
        ),
      }),
    ],
  });
}

function sectionHeading(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_2,
    spacing: { before: 200, after: 70 },
    children: [new TextRun({ text, bold: true, color: "2E7D3B", size: 22 })],
  });
}

function body(text, opts = {}) {
  return new Paragraph({
    spacing: { after: 90 },
    children: [new TextRun({ text, size: 19, ...opts })],
  });
}

function bullet(text) {
  return new Paragraph({
    numbering: { reference: "bullets", level: 0 },
    spacing: { after: 35 },
    children: [new TextRun({ text, size: 19 })],
  });
}

function cptTable() {
  const header = ["CPT Code", "Service", "Gross Charge", "Cash Price"];
  const rows = [
    ["99285", "ER visit, Level 5 / Trauma", "$15,270.00", "$6,108.00"],
    ["74177", "CT Abdomen-Pelvis w/Contrast", "$17,197.00", "$6,878.80"],
    ["80053", "Comprehensive Metabolic Panel", "$1,243.00", "$497.20"],
    ["85025", "CBC w/Auto Differential", "$445.00", "$178.00"],
    ["36415", "Venipuncture", "$112.00", "$44.80"],
  ];
  const widths = [1700, 5100, 2050, 2050];
  const headerRow = new TableRow({
    tableHeader: true,
    children: header.map(
      (h, i) =>
        new TableCell({
          width: { size: widths[i], type: WidthType.DXA },
          shading: { type: ShadingType.CLEAR, fill: "2E7D3B" },
          margins: { top: 70, bottom: 70, left: 110, right: 110 },
          children: [new Paragraph({ children: [new TextRun({ text: h, bold: true, size: 17, color: "FFFFFF" })] })],
        })
    ),
  });
  const dataRows = rows.map(
    (r, idx) =>
      new TableRow({
        children: r.map(
          (c, i) =>
            new TableCell({
              width: { size: widths[i], type: WidthType.DXA },
              shading: { type: ShadingType.CLEAR, fill: idx % 2 === 0 ? "FFFFFF" : "F6F5EE" },
              margins: { top: 70, bottom: 70, left: 110, right: 110 },
              children: [new Paragraph({ children: [new TextRun({ text: c, size: 17 })] })],
            })
        ),
      })
  );
  return new Table({
    width: { size: PAGE_WIDTH - 2 * MARGIN, type: WidthType.DXA },
    columnWidths: widths,
    rows: [headerRow, ...dataRows],
  });
}

const doc = new Document({
  numbering: {
    config: [
      {
        reference: "bullets",
        levels: [{ level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT }],
      },
    ],
  },
  sections: [
    {
      properties: {
        page: {
          size: { width: PAGE_WIDTH, height: PAGE_HEIGHT },
          margin: { top: MARGIN, bottom: MARGIN, left: MARGIN, right: MARGIN },
        },
      },
      children: [
        new Paragraph({
          children: [new TextRun({ text: "ClearBill AI", bold: true, size: 40, color: "16130E" })],
        }),
        new Paragraph({
          spacing: { after: 130 },
          children: [
            new TextRun({
              text: "Find the money hospitals didn't mean to bill you.",
              italics: true,
              size: 20,
              color: "555248",
            }),
          ],
        }),

        statBlock([
          { big: "49–80%", label: "of medical bills contain an error" },
          { big: "$1,300", label: "avg. overcharge on a $10K+ bill" },
          { big: "$220B", label: "medical debt held by 100M Americans" },
        ]),

        sectionHeading("The Problem"),
        body(
          "Nearly half to four-fifths of U.S. medical bills contain an error — duplicate charges, unbundled panels, or amounts that don't match the insurer's own Explanation of Benefits. On a $10,000+ bill, that averages roughly $1,300 in overcharges. Physicians lose an estimated $125B/year and hospitals $68B/year to billing mistakes system-wide. Patients have no standardized way to dispute a bill — every hospital routes it through its own phone line, mail address, or fax — and reviewing a bill line-by-line against an EOB takes hours most people don't have. Most people just pay."
        ),

        sectionHeading("The Insight"),
        body(
          "Billing errors aren't random — they're systematic, and the strongest signal that one occurred is already sitting in a document the patient already has: the insurer's own EOB. When an insurer marks a charge \"denied — duplicate,\" that's not our judgment, it's the payer's own adjudication. Nobody today cross-references the two documents by hand, because it requires reading two dense forms and matching line items by procedure code and date. That's a narrow, mechanical task — exactly what a deterministic pipeline does well, with Gemini doing the document understanding and plain code doing the parts that must never hallucinate."
        ),

        sectionHeading("The Solution"),
        body("Upload an itemized bill and its EOB. In under 60 seconds, ClearBill AI:"),
        bullet("Extracts every line item and CPT/HCPCS code from both documents using Gemini's multimodal document understanding"),
        bullet("Flags exact duplicate charges — same code, same date, same encounter — a deterministic check with zero false-positive risk, not a model guess"),
        bullet("Cross-references the bill against the EOB's own denial codes: if the insurer already said \"we're not paying this twice\" (citing the actual national Claim Adjustment Reason Code) and the provider billed it anyway, that's flagged"),
        bullet("Generates a ready-to-send dispute letter citing the specific code, date, and reason — grounded only in what was actually found, nothing invented"),
        bullet("Sends it — renders the letter to PDF and faxes it to the provider's billing office on the patient's command"),

        sectionHeading("Built and Verified, Not Just Pitched"),
        body(
          "Every flag we raise is grounded in something citable — a plain code check or the payer's own denial code — never a model's unverified judgment call. We deliberately do NOT claim to detect coding \"unbundling\" violations: that check requires CMS's official NCCI Procedure-to-Procedure edit tables, which sit behind an AMA licensing gate we haven't cleared, so it's on our roadmap, not our pitch. We'd rather ship two checks that are always right than three where one might be wrong. The full pipeline — extraction, duplicate detection, the bill-vs-EOB join, letter generation — has been run live against real Gemini calls, has an automated test suite, and had two real bugs (a broken EOB cross-check, a wrong CPT-code message) caught and fixed before this submission, not after."
        ),

        sectionHeading("Proof It's Real"),
        body(
          "We validated our pricing logic against Stanford Health Care's own CMS-mandated price transparency file (100% public data, updated April 2026). A single ER visit at Stanford can carry the following gross charges:"
        ),
        new Paragraph({ spacing: { before: 70, after: 130 }, children: [] }),
        cptTable(),

        sectionHeading("Why Now"),
        bullet("CFPB's 2025 rule barring medical debt from credit reports has sharpened scrutiny on billing accuracy"),
        bullet("Gemini's multimodal document understanding + Live API make what used to require a $200/hr patient advocate instant and free to start"),

        sectionHeading("Market"),
        body(
          "100M+ Americans currently hold medical debt; roughly 1.5B medical bills are issued in the U.S. annually. Existing white-glove medical-bill advocacy services (Resolve, GoodBill) charge 25–35% contingency fees — evidence of clear willingness to pay against a multi-billion-dollar pool of disputed medical debt."
        ),

        sectionHeading("Business Model"),
        bullet("Freemium: free bill scan + evidence report"),
        bullet("Success fee on verified, recovered savings once a dispute resolves"),
        bullet("B2B2C: white-label for employer benefits packages, patient advocacy nonprofits, and TPAs"),

        sectionHeading("Go-to-Market & Traction"),
        bullet("The core moment is inherently shareable: a 'we found $X you don't owe' result is the same content shape as tax-refund-reveal and settlement-check posts that already perform well on TikTok/Instagram — we designed a shareable result card for exactly this"),
        bullet("The hook itself travels: '49-80% of medical bills contain an error' is alarming, true, and citation-backed — built to be the opening line of the demo video, not just a stat in a deck"),
        bullet("Distribution is already mapped to existing communities with this exact pain point: r/personalfinance, r/HealthInsurance, patient-advocacy Facebook groups, and personal-finance creators who already cover medical debt"),
        bullet("The B2B2C channel is a distribution channel, not just revenue: one employer benefits partnership reaches thousands of employees in a single push"),

        sectionHeading("The Ask"),
        body(
          "We're seeking pitch access to validate detection accuracy against real, anonymized billing datasets and explore integration partnerships with patient advocacy networks and self-insured employers."
        ),

        sectionHeading("Team"),
        body("[Team member full names, roles, and one line of relevant background — confirm before submission]"),
      ],
    },
  ],
});

Packer.toBuffer(doc).then((buffer) => {
  require("fs").writeFileSync("ClearBill_AI_OnePager.docx", buffer);
  console.log("done");
});
