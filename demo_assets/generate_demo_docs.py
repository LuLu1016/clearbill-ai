"""
Generates two SYNTHETIC demo documents for the ClearBill AI hackathon prototype:
  - sample_itemized_bill.pdf
  - sample_eob.pdf

All dollar figures are real, publicly published Stanford Health Care gross
charges / cash prices, pulled from SHC's CMS-mandated price transparency
file (946174066_stanford-health-care_standardcharges.json, updated 2026-04-01).
The patient, account numbers, physician names, and the encounter itself are
entirely fictional -- built only to exercise the bill-parsing demo, not
derived from any real patient record.

The EOB's denial remark on the duplicate line uses CARC 18 ("Exact duplicate
claim/service"), the standard national Claim Adjustment Reason Code
maintained at x12.org/codes/claim-adjustment-reason-codes -- real EOBs use
this exact code for duplicate-billing denials, which is why it's worth
reproducing here rather than inventing a fake one.
"""

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, KeepTogether,
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_RIGHT, TA_CENTER, TA_LEFT

CARDINAL = colors.HexColor("#8C1515")
INK = colors.HexColor("#262624")
MUTED = colors.HexColor("#6B6862")
FAINT = colors.HexColor("#92897F")
LINE = colors.HexColor("#E8E6DF")
PANEL = colors.HexColor("#FAF9F5")
DANGER = colors.HexColor("#B3432F")
DANGER_TINT = colors.HexColor("#F7E4DE")
BLUE = colors.HexColor("#1A56DB")

styles = getSampleStyleSheet()
styles.add(ParagraphStyle(name="OrgName", fontSize=15, leading=18, textColor=INK, fontName="Helvetica-Bold"))
styles.add(ParagraphStyle(name="OrgSub", fontSize=8.5, leading=12, textColor=MUTED))
styles.add(ParagraphStyle(name="DocTitle", fontSize=12, leading=15, textColor=INK, fontName="Helvetica-Bold", spaceBefore=10, spaceAfter=6))
styles.add(ParagraphStyle(name="PanelLabel", fontSize=7, leading=9, textColor=FAINT, fontName="Helvetica-Bold"))
styles.add(ParagraphStyle(name="PanelValue", fontSize=9, leading=12, textColor=INK, fontName="Helvetica-Bold"))
styles.add(ParagraphStyle(name="Body", fontSize=8.5, leading=13, textColor=INK))
styles.add(ParagraphStyle(name="BodyMuted", fontSize=8, leading=12, textColor=MUTED))
styles.add(ParagraphStyle(name="Fine", fontSize=7, leading=10, textColor=FAINT))
styles.add(ParagraphStyle(name="FineCenter", fontSize=7, leading=10, textColor=FAINT, alignment=TA_CENTER))
styles.add(ParagraphStyle(name="RightBig", fontSize=13, leading=16, textColor=DANGER, fontName="Helvetica-Bold", alignment=TA_RIGHT))

LINE_ITEMS = [
    # date, cpt, description, qty, unit_charge
    ("07/10/2026", "99285", "Emergency Dept Visit, High Complexity / Trauma", 1, 15270.00),
    ("07/10/2026", "74177", "CT Abdomen-Pelvis with Contrast", 1, 17197.00),
    ("07/10/2026", "80053", "Comprehensive Metabolic Panel", 1, 1243.00),
    ("07/10/2026", "85025", "CBC with Automated Differential", 1, 445.00),
    ("07/10/2026", "36415", "Venipuncture, Routine Collection", 1, 112.00),
    ("07/10/2026", "36415", "Venipuncture, Routine Collection", 1, 112.00),  # injected duplicate
]

ALLOWED = {  # SHC's own published discounted cash price, used as EOB "allowed amount"
    "99285": 6108.00,
    "74177": 6878.80,
    "80053": 497.20,
    "85025": 178.00,
    "36415": 44.80,
}

PATIENT = {
    "name": "Jordan A. Sample",
    "dob": "03/22/1991",
    "account": "SHC-DEMO-00219",
    "mrn": "MRN-7788214",
    "address": "482 Escondido Mall, Apt 3B, Stanford, CA 94305",
}

INSURANCE = {
    "payer": "Cardinal Health Partners PPO",
    "member_id": "CHP-DEMO-778821",
    "group": "GRP-30442",
    "claim": "CLM-2026-0710-4471",
}


def panel_row(pairs, col_width):
    """A row of label/value pairs styled like a bill's info panel."""
    cells = []
    widths = []
    for label, value in pairs:
        cells.append(
            [
                Paragraph(label.upper(), styles["PanelLabel"]),
                Paragraph(value, styles["PanelValue"]),
            ]
        )
        widths.append(col_width)
    # Flatten into a single-row table where each "cell" is itself two stacked paragraphs
    row_cells = []
    for label, value in pairs:
        inner = Table(
            [[Paragraph(label.upper(), styles["PanelLabel"])], [Paragraph(value, styles["PanelValue"])]],
            colWidths=[col_width],
        )
        inner.setStyle(TableStyle([("TOPPADDING", (0, 0), (-1, -1), 0), ("BOTTOMPADDING", (0, 0), (-1, 0), 2),
                                    ("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 0)]))
        row_cells.append(inner)
    return row_cells, widths


def info_panel(rows, total_width):
    """rows: list of lists of (label, value) tuples -- each inner list is one visual row."""
    table_rows = []
    col_width = total_width / len(rows[0])
    for row in rows:
        cells, widths = panel_row(row, col_width)
        table_rows.append(cells)
    t = Table(table_rows, colWidths=[col_width] * len(rows[0]))
    t.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 9),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 14),
            ]
        )
    )
    return t


def letterhead(org_name, org_sub, accent):
    bar = Table([[""]], colWidths=[7.3 * inch], rowHeights=[4])
    bar.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), accent)]))
    return [
        bar,
        Spacer(1, 10),
        Paragraph(org_name, styles["OrgName"]),
        Paragraph(org_sub, styles["OrgSub"]),
        Spacer(1, 4),
    ]


def remittance_stub(amount_due, due_date):
    story = []
    story.append(Spacer(1, 18))
    story.append(HRFlowable(width="100%", thickness=0.75, color=FAINT, dash=(3, 3)))
    story.append(Spacer(1, 4))
    story.append(Paragraph("✂ PLEASE DETACH AND RETURN WITH PAYMENT", styles["FineCenter"]))
    story.append(Spacer(1, 8))

    left = [
        Paragraph("REMIT TO", styles["PanelLabel"]),
        Paragraph("Stanford Health Care<br/>Patient Financial Services<br/>PO Box 60965<br/>Palo Alto, CA 94306", styles["Body"]),
    ]
    right_rows = [
        ["Account #:", PATIENT["account"]],
        ["Statement Date:", "07/16/2026"],
        ["Due Date:", due_date],
        ["Amount Enclosed:", "$__________"],
    ]
    right_table = Table(right_rows, colWidths=[1.4 * inch, 1.7 * inch])
    right_table.setStyle(
        TableStyle(
            [
                ("FONTSIZE", (0, 0), (-1, -1), 8.5),
                ("FONTNAME", (0, 0), (0, -1), "Helvetica"),
                ("FONTNAME", (1, 0), (1, -1), "Helvetica-Bold"),
                ("TEXTCOLOR", (0, 0), (0, -1), MUTED),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )

    amount_cell = [
        Paragraph("TOTAL DUE", styles["PanelLabel"]),
        Paragraph(f"${amount_due:,.2f}", styles["RightBig"]),
    ]

    outer = Table(
        [[left, right_table, amount_cell]],
        colWidths=[2.6 * inch, 3.1 * inch, 1.6 * inch],
    )
    outer.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("BOX", (0, 0), (-1, -1), 0.75, LINE),
                ("BACKGROUND", (0, 0), (-1, -1), PANEL),
                ("TOPPADDING", (0, 0), (-1, -1), 12),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
                ("LEFTPADDING", (0, 0), (-1, -1), 12),
                ("RIGHTPADDING", (0, 0), (-1, -1), 12),
            ]
        )
    )
    story.append(outer)
    return story


def build_bill():
    doc = SimpleDocTemplate(
        "sample_itemized_bill.pdf",
        pagesize=letter,
        topMargin=0.55 * inch,
        bottomMargin=0.55 * inch,
        leftMargin=0.6 * inch,
        rightMargin=0.6 * inch,
    )
    story = []
    story += letterhead(
        "Stanford Health Care",
        "300 Pasteur Drive, Stanford, CA 94305 &nbsp;|&nbsp; Patient Billing: 1-800-549-3720",
        CARDINAL,
    )
    story.append(Paragraph("STATEMENT OF ACCOUNT", styles["DocTitle"]))

    rows = [
        [("Patient", PATIENT["name"]), ("Account #", PATIENT["account"]), ("MRN", PATIENT["mrn"])],
        [("Date of Birth", PATIENT["dob"]), ("Date of Service", "07/10/2026"), ("Statement Date", "07/16/2026")],
        [("Attending Provider", "M. Alvarez, MD"), ("Department", "Emergency Medicine"), ("Guarantor", PATIENT["name"])],
        [("Primary Insurance", INSURANCE["payer"]), ("Member ID", INSURANCE["member_id"]), ("Group #", INSURANCE["group"])],
    ]
    story.append(info_panel(rows, 7.3 * inch))
    story.append(Spacer(1, 4))

    header = ["Date", "CPT/HCPCS", "Description", "Qty", "Charge"]
    table_rows = [header]
    total = 0.0
    for date, cpt, desc, qty, unit in LINE_ITEMS:
        amount = qty * unit
        total += amount
        table_rows.append([date, cpt, desc, str(qty), f"${amount:,.2f}"])

    t = Table(table_rows, colWidths=[0.85 * inch, 0.85 * inch, 3.55 * inch, 0.4 * inch, 0.95 * inch])
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), CARDINAL),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8.5),
                ("ALIGN", (3, 0), (4, -1), "RIGHT"),
                ("ALIGN", (3, 0), (3, -1), "CENTER"),
                ("GRID", (0, 0), (-1, -1), 0.5, LINE),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, PANEL]),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    story.append(t)
    story.append(Spacer(1, 10))

    summary_rows = [
        ["Total Charges", f"${total:,.2f}"],
        ["Insurance Payments Applied", "$0.00 (pending claim adjudication)"],
        ["Patient Payments", "$0.00"],
    ]
    summary = Table(summary_rows, colWidths=[5.6 * inch, 1.7 * inch])
    summary.setStyle(
        TableStyle(
            [
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("ALIGN", (1, 0), (1, -1), "RIGHT"),
                ("TEXTCOLOR", (0, 0), (-1, -1), MUTED),
                ("LINEBELOW", (0, -1), (-1, -1), 0.75, LINE),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    story.append(summary)
    story.append(Spacer(1, 4))
    due_row = Table([["Balance Due", f"${total:,.2f}"]], colWidths=[5.6 * inch, 1.7 * inch])
    due_row.setStyle(
        TableStyle(
            [
                ("FONTSIZE", (0, 0), (-1, -1), 11),
                ("FONTNAME", (0, 0), (-1, -1), "Helvetica-Bold"),
                ("ALIGN", (1, 0), (1, -1), "RIGHT"),
                ("TEXTCOLOR", (0, 0), (-1, -1), INK),
            ]
        )
    )
    story.append(due_row)

    story += remittance_stub(total, "08/09/2026")

    story.append(Spacer(1, 16))
    story.append(
        Paragraph(
            "SYNTHETIC DEMO DOCUMENT -- generated for the Stanford x DeepMind Hackathon "
            "(ClearBill AI). Patient, provider, and account information is fictional. Dollar "
            "amounts are real Stanford Health Care gross charges published under the CMS "
            "Hospital Price Transparency Rule (45 CFR 180.50), file dated 2026-04-01.",
            styles["FineCenter"],
        )
    )

    doc.build(story)
    return total


def build_eob(bill_total):
    doc = SimpleDocTemplate(
        "sample_eob.pdf",
        pagesize=letter,
        topMargin=0.55 * inch,
        bottomMargin=0.55 * inch,
        leftMargin=0.6 * inch,
        rightMargin=0.6 * inch,
    )
    story = []
    story += letterhead(
        INSURANCE["payer"],
        "Explanation of Benefits &mdash; This is a summary of how your claim was processed. This is not a bill.",
        BLUE,
    )
    story.append(Paragraph("CLAIM SUMMARY", styles["DocTitle"]))

    rows = [
        [("Member", PATIENT["name"]), ("Member ID", INSURANCE["member_id"]), ("Group #", INSURANCE["group"])],
        [("Provider", "Stanford Health Care"), ("Claim #", INSURANCE["claim"]), ("Date of Service", "07/10/2026")],
        [("Date Processed", "07/14/2026"), ("Network Status", "In-Network"), ("Plan Type", "PPO")],
    ]
    story.append(info_panel(rows, 7.3 * inch))
    story.append(Spacer(1, 4))

    header = ["CPT", "Billed", "Allowed", "Plan Paid", "Patient Owes", "Remark"]
    table_rows = [header]
    total_patient_resp = 0.0
    seen_36415 = 0
    for date, cpt, desc, qty, unit in LINE_ITEMS:
        amount = qty * unit
        allowed = ALLOWED[cpt]
        if cpt == "36415":
            seen_36415 += 1
        if cpt == "36415" and seen_36415 == 2:
            plan_paid = 0.0
            patient_resp = 0.0
            remark = "CARC 18 -- Exact\nduplicate claim/service"
        else:
            plan_paid = round(allowed * 0.8, 2)
            patient_resp = round(allowed - plan_paid, 2)
            remark = ""
        total_patient_resp += patient_resp
        table_rows.append(
            [cpt, f"${amount:,.2f}", f"${allowed:,.2f}", f"${plan_paid:,.2f}", f"${patient_resp:,.2f}", remark]
        )

    t = Table(table_rows, colWidths=[0.65 * inch, 1.0 * inch, 1.0 * inch, 1.0 * inch, 1.05 * inch, 1.9 * inch])
    style = [
        ("BACKGROUND", (0, 0), (-1, 0), BLUE),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("ALIGN", (1, 0), (4, -1), "RIGHT"),
        ("GRID", (0, 0), (-1, -1), 0.5, LINE),
        ("TEXTCOLOR", (5, 1), (5, -1), DANGER),
        ("FONTNAME", (5, 1), (5, -1), "Helvetica-Bold"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, PANEL]),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]
    t.setStyle(TableStyle(style))
    story.append(t)
    story.append(Spacer(1, 10))

    due_row = Table([["Total Patient Responsibility", f"${total_patient_resp:,.2f}"]], colWidths=[5.6 * inch, 1.6 * inch])
    due_row.setStyle(
        TableStyle(
            [
                ("FONTSIZE", (0, 0), (-1, -1), 11),
                ("FONTNAME", (0, 0), (-1, -1), "Helvetica-Bold"),
                ("ALIGN", (1, 0), (1, -1), "RIGHT"),
            ]
        )
    )
    story.append(due_row)
    story.append(Spacer(1, 12))

    story.append(
        Paragraph(
            f"Provider billed <b>${bill_total:,.2f}</b> total. Your plan's allowed amount reflects "
            "negotiated rates, not the provider's list price. <b>CARC 18</b> is the national Claim "
            "Adjustment Reason Code for an exact duplicate service and means this plan will not pay "
            "it twice -- if your provider's statement still shows a balance for this line, that's "
            "worth disputing directly with them.",
            styles["Body"],
        )
    )
    story.append(Spacer(1, 16))
    story.append(
        Paragraph(
            "SYNTHETIC DEMO DOCUMENT -- generated for the Stanford x DeepMind Hackathon "
            "(ClearBill AI). All member/plan/claim information is fictional and for demonstration "
            "only.",
            styles["FineCenter"],
        )
    )

    doc.build(story)
    return total_patient_resp


if __name__ == "__main__":
    total = build_bill()
    patient_resp = build_eob(total)
    print(f"Bill total: ${total:,.2f}")
    print(f"EOB patient responsibility: ${patient_resp:,.2f}")
    print(f"Duplicate-charge overcharge ClearBill AI should catch: $112.00 (CPT 36415, denied by insurer via CARC 18, still billed)")
