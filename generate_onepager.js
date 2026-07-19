const {
  Document, Packer, Paragraph, TextRun, HeadingLevel, Table, TableRow, TableCell,
  WidthType, ShadingType, BorderStyle, AlignmentType, LevelFormat, convertInchesToTwip
} = require("docx");

const PAGE_WIDTH = 12240;
const PAGE_HEIGHT = 15840;
const MARGIN = 630; // ~0.44"
const FONT = "Arial";

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
                  children: [new TextRun({ text: it.big, bold: true, size: 28, color: "2E7D3B", font: FONT })],
                }),
                new Paragraph({
                  alignment: AlignmentType.CENTER,
                  spacing: { before: 30 },
                  children: [new TextRun({ text: it.label, size: 15, color: "555248", font: FONT })],
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
    children: [new TextRun({ text, bold: true, color: "2E7D3B", size: 22, font: FONT })],
  });
}

function body(text, opts = {}) {
  return new Paragraph({
    spacing: { after: 90 },
    children: [new TextRun({ text, size: 19, font: FONT, ...opts })],
  });
}

function bullet(text) {
  return new Paragraph({
    numbering: { reference: "bullets", level: 0 },
    spacing: { after: 35 },
    children: [new TextRun({ text, size: 19, font: FONT })],
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
          children: [new Paragraph({ children: [new TextRun({ text: h, bold: true, size: 17, color: "FFFFFF", font: FONT })] })],
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
              children: [new Paragraph({ children: [new TextRun({ text: c, size: 17, font: FONT })] })],
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
  styles: {
    default: {
      document: { run: { font: FONT } },
      heading2: { run: { font: FONT } },
    },
  },
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
          children: [new TextRun({ text: "ClearBill AI", bold: true, size: 40, color: "16130E", font: FONT })],
        }),
        new Paragraph({
          spacing: { after: 130 },
          children: [
            new TextRun({
              text: "Find the money hospitals didn't mean to bill you.",
              italics: true,
              size: 20,
              color: "555248",
              font: FONT,
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
          "Between 49% and 80% of U.S. medical bills contain an error: duplicate charges, unbundled panels, or amounts that do not match the insurer's own Explanation of Benefits. On a $10,000+ bill, that averages roughly $1,300 in overcharges. Billing mistakes cost physicians an estimated $125B per year and hospitals $68B per year system-wide. Patients have no standardized way to dispute a bill. Every hospital routes disputes through its own phone line, mail address, or fax, and reconciling a bill against an EOB by hand takes hours most people do not have. Most people simply pay."
        ),

        sectionHeading("The Insight"),
        body(
          "Billing errors are not random. The strongest signal that one occurred is already sitting in a document the patient already holds: the insurer's own EOB. When an insurer marks a charge \"denied, duplicate,\" that is not our judgment; it is the payer's own adjudication. No one today cross-references the two documents by hand, because doing so requires reading two dense forms and matching line items by procedure code and date. That is a narrow, mechanical task, and exactly what a deterministic pipeline is suited to: Gemini performs the document understanding, and plain code performs the parts that must never hallucinate."
        ),

        sectionHeading("The Solution"),
        body("Upload an itemized bill and its EOB. In under 60 seconds, ClearBill AI will:"),
        bullet("Extract every line item and CPT/HCPCS code from both documents using Gemini's multimodal document understanding"),
        bullet("Flag exact duplicate charges: same code, same date, same encounter. Deterministic, with zero false-positive risk, never a model guess"),
        bullet("Cross-reference the bill against the EOB's own denial codes. If the insurer already declined to pay a charge and the provider billed the patient for it anyway, that is flagged and cited by its official Claim Adjustment Reason Code"),
        bullet("Generate a dispute letter grounded only in what was actually found, citing the specific code, date, and reason"),
        body("This is the first step. The product is designed around a longer loop."),

        sectionHeading("The Full Loop (Roadmap)"),
        body(
          "A letter that never gets sent recovers nothing. The roadmap extends ClearBill AI from a one-time audit into a managed dispute: the system sends the letter through the channel the provider actually uses (patient portal message, email, or fax), reads the provider's response when it arrives, drafts the next round of correspondence if the dispute continues, and escalates automatically if the provider does not respond within the customary window. The loop closes only when the refund is confirmed, whether through a corrected statement, a credit, or a returned payment. This is also the mechanism the success-fee model depends on: a fee tied to recovered savings requires tracking recovery, not just filing a dispute."
        ),

        sectionHeading("Built and Verified"),
        body(
          "Every flag we raise is grounded in something citable: a plain code check or the payer's own denial code, never an unverified judgment call from the model. We do not claim to detect coding \"unbundling\" violations. That check requires CMS's official NCCI Procedure-to-Procedure edit tables, which sit behind an AMA licensing gate we have not yet cleared, so it remains on the roadmap rather than the pitch. We would rather ship two checks that are always correct than three where one might not be. The full pipeline, extraction, duplicate detection, the bill-to-EOB join, and letter generation, has been run live against Gemini, is covered by an automated test suite, and had two real defects (a broken EOB cross-check and an incorrect CPT-code message) identified and fixed before this submission."
        ),

        sectionHeading("Grounded in Real Pricing Data"),
        body(
          "We validated our pricing logic against Stanford Health Care's own CMS-mandated price transparency file, current as of April 2026. A single ER visit at Stanford can carry the following gross charges:"
        ),
        new Paragraph({ spacing: { before: 70, after: 130 }, children: [] }),
        cptTable(),

        sectionHeading("Why Now"),
        bullet("The CFPB's 2025 rule removing medical debt from credit reports has increased scrutiny on billing accuracy"),
        bullet("Gemini's multimodal document understanding makes work that once required a $200/hour patient advocate available instantly and at no cost to start"),

        sectionHeading("Market Size"),
        body(
          "More than 100 million Americans currently hold medical debt, and roughly 1.5 billion medical bills are issued in the U.S. annually. Existing full-service medical-bill advocacy firms (Resolve, GoodBill) charge 25% to 35% contingency fees: evidence of a market that already pays for this outcome, manually and slowly."
        ),

        sectionHeading("Business Model"),
        bullet("Freemium: free bill scan and evidence report"),
        bullet("Success fee on recovered savings, paid only once a dispute resolves and the refund is confirmed"),
        bullet("B2B2C distribution through employer benefits platforms, patient advocacy nonprofits, and third-party administrators"),

        sectionHeading("Go-to-Market & Traction"),
        bullet("The core result is inherently shareable. A confirmed refund follows the same content pattern as the tax-refund and settlement-check posts that already perform well on TikTok and Instagram; we built a shareable result card for exactly this moment"),
        bullet("The opening stat travels on its own merit: between 49% and 80% of medical bills contain an error, a claim that is alarming, true, and fully citable"),
        bullet("Distribution channels are already identified: r/personalfinance, r/HealthInsurance, patient-advocacy communities, and personal-finance creators who already cover medical debt"),
        bullet("The B2B2C channel doubles as distribution. A single employer benefits partnership reaches thousands of employees at once"),

        sectionHeading("The Ask"),
        body(
          "We are not raising today. We want thirty minutes with a fund that has genuine conviction in consumer healthcare fintech, to pressure-test two things: the data-access strategy for scaling detection beyond a single hospital's pricing file, and the recovery-verification model the success fee depends on."
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
