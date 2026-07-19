const {
  Document, Packer, Paragraph, TextRun, HeadingLevel, Table, TableRow, TableCell,
  WidthType, ShadingType, BorderStyle, AlignmentType, LevelFormat, convertInchesToTwip
} = require("docx");

const PAGE_WIDTH = 12240;
const PAGE_HEIGHT = 15840;
const MARGIN = 540; // ~0.375" -- tight, this must fit one page
const FONT = "Arial";
const GREEN = "2E7D3B";
const MUTED = "555248";
const INK = "16130E";

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
              margins: { top: 100, bottom: 100, left: 120, right: 120 },
              borders: {
                top: { style: BorderStyle.SINGLE, size: 2, color: "DDD9C8" },
                bottom: { style: BorderStyle.SINGLE, size: 2, color: "DDD9C8" },
                left: { style: BorderStyle.SINGLE, size: 2, color: "DDD9C8" },
                right: { style: BorderStyle.SINGLE, size: 2, color: "DDD9C8" },
              },
              children: [
                new Paragraph({
                  alignment: AlignmentType.CENTER,
                  children: [new TextRun({ text: it.big, bold: true, size: 26, color: GREEN, font: FONT })],
                }),
                new Paragraph({
                  alignment: AlignmentType.CENTER,
                  spacing: { before: 20 },
                  children: [new TextRun({ text: it.label, size: 13, color: MUTED, font: FONT })],
                }),
              ],
            })
        ),
      }),
    ],
  });
}

// A label-and-value block, one visual line: "SECTION LABEL   compact content"
// This is the workhorse of the whole page -- bold caps label a reader's eye
// catches while skimming, immediately followed by the answer, not a lead-in.
function line(label, text, opts = {}) {
  return new Paragraph({
    spacing: { after: opts.after ?? 95 },
    children: [
      new TextRun({ text: label.toUpperCase() + "   ", bold: true, size: 15, color: GREEN, font: FONT }),
      new TextRun({ text, size: 18, color: INK, font: FONT }),
    ],
  });
}

function bullet(text, opts = {}) {
  return new Paragraph({
    numbering: { reference: "bullets", level: 0 },
    spacing: { after: opts.after ?? 45 },
    children: [new TextRun({ text, size: 18, color: INK, font: FONT })],
  });
}

function sectionLabel(text) {
  return new Paragraph({
    spacing: { before: 130, after: 40 },
    children: [new TextRun({ text: text.toUpperCase(), bold: true, size: 15, color: GREEN, font: FONT, characterSpacing: 10 })],
  });
}

const doc = new Document({
  styles: {
    default: {
      document: { run: { font: FONT } },
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
        // ---- Header ----
        new Paragraph({
          children: [new TextRun({ text: "ClearBill AI", bold: true, size: 36, color: INK, font: FONT })],
        }),
        new Paragraph({
          spacing: { after: 60 },
          children: [
            new TextRun({
              text: "Find the money hospitals didn't mean to bill you.",
              italics: true, size: 18, color: MUTED, font: FONT,
            }),
          ],
        }),
        // The 30-second explainer -- written for a reader with zero healthcare
        // background. If this line needs a follow-up question, it's wrong.
        new Paragraph({
          spacing: { after: 130 },
          children: [
            new TextRun({
              text: "We cross-check your hospital bill against your insurance company's own paperwork — the same comparison a $200/hr patient advocate does by hand — and catch the exact overcharges automatically, in under a minute, for free.",
              size: 18, color: INK, font: FONT,
            }),
          ],
        }),

        statBlock([
          { big: "49–80%", label: "of medical bills contain an error" },
          { big: "$220B", label: "medical debt held by 100M Americans" },
          { big: "25–35%", label: "fee competitors already charge to do this by hand" },
        ]),

        sectionLabel("The Problem"),
        new Paragraph({
          spacing: { after: 100 },
          children: [new TextRun({
            text: "On a $10K+ bill, errors average $1,300 in overcharges — but there's no standard way to dispute one, and checking a bill against an insurance EOB by hand takes hours nobody has. Most people just pay.",
            size: 18, color: INK, font: FONT,
          })],
        }),

        sectionLabel("What We Do"),
        bullet("Upload a bill + EOB. Gemini extracts every line item and code in seconds."),
        bullet("We flag exact duplicate charges (deterministic, zero false positives) and anything your insurer already denied that the hospital billed anyway, citing their own official denial code."),
        bullet("We draft — and can send — the dispute letter. Roadmap: we follow up until the refund is confirmed, not just filed."),

        sectionLabel("Why ClearBill Wins"),
        bullet("Not a chatbot wrapper. Every flag is grounded in deterministic logic or the insurer's own official code — never an LLM's guess. Zero false-positive risk on our core check."),
        bullet("Grounded in regulatory data most competitors skip: CMS pricing files, the national CARC/RARC denial-code registry, NPI provider records."),
        bullet("Building the full loop — detection through confirmed refund — not a one-time scanner competitors can copy in a weekend."),

        line("Proof", "Live-verified against real Gemini calls. 27 automated tests passing. Two real bugs found and fixed pre-launch. Prices benchmarked against Stanford Health Care's own federally mandated pricing data."),
        line("Market", "$220B in medical debt, 100M Americans, 1.5B bills issued annually. Competitors already charge 25–35% contingency fees to do this manually — proof the market pays for the outcome."),
        line("Go-to-Market", "A confirmed refund is inherently shareable — same content shape as viral tax-refund posts. Distribution is mapped: r/personalfinance, patient-advocacy communities, employer benefits partnerships (one deal reaches thousands of employees)."),
        line("Business Model", "Free scan → success fee on recovered savings → B2B2C through employer benefits platforms and TPAs."),
        line("The Ask", "Not raising today. We want 30 minutes with a fund that has real conviction in consumer healthcare fintech.", { after: 130 }),
        line("Team", "Lu Lu — Wharton MBA, Penn M.S. Computer Science, product management intern at Adobe. Yiyan — go-to-market & growth."),
      ],
    },
  ],
});

Packer.toBuffer(doc).then((buffer) => {
  require("fs").writeFileSync("ClearBill_AI_OnePager.docx", buffer);
  console.log("done");
});
