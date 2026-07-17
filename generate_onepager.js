const {
  Document, Packer, Paragraph, TextRun, HeadingLevel, Table, TableRow, TableCell,
  WidthType, ShadingType, BorderStyle, AlignmentType, LevelFormat, convertInchesToTwip
} = require("docx");

const PAGE_WIDTH = 12240;
const PAGE_HEIGHT = 15840;
const MARGIN = 720; // 0.5"

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
              shading: { type: ShadingType.CLEAR, fill: "F2F2F2" },
              margins: { top: 160, bottom: 160, left: 160, right: 160 },
              borders: {
                top: { style: BorderStyle.SINGLE, size: 2, color: "DDDDDD" },
                bottom: { style: BorderStyle.SINGLE, size: 2, color: "DDDDDD" },
                left: { style: BorderStyle.SINGLE, size: 2, color: "DDDDDD" },
                right: { style: BorderStyle.SINGLE, size: 2, color: "DDDDDD" },
              },
              children: [
                new Paragraph({
                  alignment: AlignmentType.CENTER,
                  children: [new TextRun({ text: it.big, bold: true, size: 30, color: "1A56DB" })],
                }),
                new Paragraph({
                  alignment: AlignmentType.CENTER,
                  spacing: { before: 40 },
                  children: [new TextRun({ text: it.label, size: 16, color: "555555" })],
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
    spacing: { before: 220, after: 80 },
    children: [new TextRun({ text, bold: true, color: "1A56DB", size: 24 })],
  });
}

function body(text, opts = {}) {
  return new Paragraph({
    spacing: { after: 100 },
    children: [new TextRun({ text, size: 20, ...opts })],
  });
}

function bullet(text) {
  return new Paragraph({
    numbering: { reference: "bullets", level: 0 },
    spacing: { after: 40 },
    children: [new TextRun({ text, size: 20 })],
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
  const widths = [1800, 5200, 2000, 2000];
  const mkCell = (text, bold, fill) =>
    new TableCell({
      width: { size: widths[0], type: WidthType.DXA },
      shading: fill ? { type: ShadingType.CLEAR, fill } : undefined,
      margins: { top: 80, bottom: 80, left: 120, right: 120 },
      children: [new Paragraph({ children: [new TextRun({ text, bold, size: 18 })] })],
    });
  const headerRow = new TableRow({
    tableHeader: true,
    children: header.map(
      (h, i) =>
        new TableCell({
          width: { size: widths[i], type: WidthType.DXA },
          shading: { type: ShadingType.CLEAR, fill: "1A56DB" },
          margins: { top: 80, bottom: 80, left: 120, right: 120 },
          children: [new Paragraph({ children: [new TextRun({ text: h, bold: true, size: 18, color: "FFFFFF" })] })],
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
              shading: { type: ShadingType.CLEAR, fill: idx % 2 === 0 ? "FFFFFF" : "F7F9FC" },
              margins: { top: 80, bottom: 80, left: 120, right: 120 },
              children: [new Paragraph({ children: [new TextRun({ text: c, size: 18 })] })],
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
          children: [new TextRun({ text: "ClearBill AI", bold: true, size: 44, color: "0F172A" })],
        }),
        new Paragraph({
          spacing: { after: 160 },
          children: [
            new TextRun({
              text: "Find the money hospitals didn't mean to bill you.",
              italics: true,
              size: 22,
              color: "555555",
            }),
          ],
        }),

        statBlock([
          { big: "49–80%", label: "of medical bills contain errors" },
          { big: "$88B", label: "lost annually to billing mistakes" },
          { big: "$220B", label: "in medical debt held by 100M Americans" },
        ]),

        sectionHeading("The Problem"),
        body(
          "Nearly half to four-fifths of U.S. medical bills contain at least one error — duplicate charges, unbundled panels, or amounts that don't match the insurer's own Explanation of Benefits. On a $10,000+ hospital bill, that averages roughly $1,300 in overcharges. Physicians lose an estimated $125B/year and hospitals $68B/year to billing mistakes system-wide (CFPB, Medical Bill Rescue, 2025). Patients have no standardized way to dispute a bill — every hospital routes it through its own phone line, mail address, or fax, and reviewing a bill line-by-line against an EOB takes hours most people don't have. Most people just pay."
        ),

        sectionHeading("The Insight"),
        body(
          "This isn't a hypothetical — it's the same problem the UF Warrington College of Business documented in complex multi-leg trades' cousin industry: opaque, asymmetric-information markets where the side with less time and expertise simply absorbs the loss. Medical billing is that market at consumer scale, and no one has built a self-serve, instant tool for the patient side."
        ),

        sectionHeading("The Solution"),
        body("Upload an itemized bill and its EOB. In under 60 seconds, ClearBill AI:"),
        bullet("Extracts every line item and CPT/HCPCS code using Gemini multimodal document understanding"),
        bullet("Flags exact duplicate charges — same code, same date, same encounter — a deterministic check with zero false positives"),
        bullet(
          "Cross-checks charges against CMS's own National Correct Coding Initiative (NCCI) Procedure-to-Procedure edits and Medically Unlikely Edits — the same public rule tables Medicare auditors use — flagging possible unbundling for review, never asserting fraud outright"
        ),
        bullet("Generates a ready-to-send dispute letter citing the specific code, date, and rule violated"),
        bullet("Auto-faxes the letter directly to the hospital's billing department on the patient's command"),

        sectionHeading("Proof It's Real, Not Hypothetical"),
        body(
          "We validated our pricing logic against Stanford Health Care's own CMS-mandated price transparency file (100% public data, updated April 2026). A single ER visit at Stanford can carry the following gross charges:"
        ),
        new Paragraph({ spacing: { before: 80, after: 160 }, children: [] }),
        cptTable(),

        sectionHeading("Why Now"),
        bullet("CFPB's 2025 rule barring medical debt from credit reports has sharpened scrutiny on billing accuracy"),
        bullet(
          "Gemini's multimodal document understanding + Live API make what used to require a $200/hr patient advocate instant and free to start"
        ),

        sectionHeading("Market"),
        body(
          "100M+ Americans currently hold medical debt; roughly 1.5B medical bills are issued in the U.S. annually. Existing white-glove medical-bill advocacy services (Resolve, GoodBill) charge 25–35% contingency fees — evidence of clear willingness to pay against a multi-billion-dollar pool of disputed medical debt."
        ),

        sectionHeading("Business Model"),
        bullet("Freemium: free bill scan + evidence report"),
        bullet("Success fee on verified, recovered savings once a dispute resolves"),
        bullet("B2B2C: white-label for employer benefits packages, patient advocacy nonprofits, and TPAs"),

        sectionHeading("The Ask"),
        body(
          "We're seeking pitch access to validate detection accuracy against real, anonymized billing datasets and explore integration partnerships with patient advocacy networks and self-insured employers."
        ),

        sectionHeading("Team"),
        body("[Team member names, roles, and one line of relevant background — fill in before submission]"),
      ],
    },
  ],
});

Packer.toBuffer(doc).then((buffer) => {
  require("fs").writeFileSync("ClearBill_AI_OnePager.docx", buffer);
  console.log("done");
});
