"""
Generates two SYNTHETIC demo documents for the ClearBill AI hackathon prototype:
  - sample_itemized_bill.pdf
  - sample_eob.pdf

All dollar figures are real, publicly published Stanford Health Care gross
charges / cash prices, pulled from SHC's CMS-mandated price transparency
file (946174066_stanford-health-care_standardcharges.json, updated 2026-04-01).
The patient, account numbers, and encounter itself are entirely fictional —
built only to exercise the bill-parsing demo, not derived from any real
patient record.
"""

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_RIGHT, TA_CENTER

styles = getSampleStyleSheet()
styles.add(ParagraphStyle(name="Small", fontSize=8, textColor=colors.grey))
styles.add(ParagraphStyle(name="RightSmall", fontSize=8, alignment=TA_RIGHT))
styles.add(ParagraphStyle(name="CenterNote", fontSize=8, alignment=TA_CENTER, textColor=colors.grey))

LINE_ITEMS = [
    # date, cpt, description, charge
    ("07/10/2026", "99285", "Emergency Dept Visit, High Complexity / Trauma", 15270.00),
    ("07/10/2026", "74177", "CT Abdomen-Pelvis with Contrast", 17197.00),
    ("07/10/2026", "80053", "Comprehensive Metabolic Panel", 1243.00),
    ("07/10/2026", "85025", "CBC with Automated Differential", 445.00),
    ("07/10/2026", "36415", "Venipuncture, Routine Collection", 112.00),
    ("07/10/2026", "36415", "Venipuncture, Routine Collection", 112.00),  # injected duplicate
]

# EOB "allowed amount" approximated from SHC's own published discounted cash price
ALLOWED = {
    "99285": 6108.00,
    "74177": 6878.80,
    "80053": 497.20,
    "85025": 178.00,
    "36415": 44.80,
}


def build_bill():
    doc = SimpleDocTemplate(
        "sample_itemized_bill.pdf",
        pagesize=letter,
        topMargin=0.6 * inch,
        bottomMargin=0.6 * inch,
        leftMargin=0.6 * inch,
        rightMargin=0.6 * inch,
    )
    story = []

    story.append(Paragraph("<b>Stanford Health Care</b>", styles["Title"]))
    story.append(Paragraph("300 Pasteur Drive, Stanford, CA 94305", styles["Normal"]))
    story.append(Spacer(1, 6))
    story.append(Paragraph("<b>Patient Billing Statement</b>", styles["Heading2"]))
    story.append(Spacer(1, 4))

    info_data = [
        ["Patient:", "Jordan A. Sample", "Account #:", "SHC-DEMO-00219"],
        ["Date of Service:", "07/10/2026", "Statement Date:", "07/16/2026"],
        ["Guarantor:", "Jordan A. Sample", "Provider:", "Stanford Health Care - Emergency Dept"],
    ]
    info_table = Table(info_data, colWidths=[1.2 * inch, 2.3 * inch, 1.2 * inch, 2.3 * inch])
    info_table.setStyle(
        TableStyle(
            [
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("FONTNAME", (2, 0), (2, -1), "Helvetica-Bold"),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    story.append(info_table)
    story.append(Spacer(1, 14))

    header = ["Date", "CPT/HCPCS", "Description", "Charge"]
    rows = [header]
    total = 0.0
    for date, cpt, desc, charge in LINE_ITEMS:
        rows.append([date, cpt, desc, f"${charge:,.2f}"])
        total += charge
    rows.append(["", "", "Total Charges", f"${total:,.2f}"])
    rows.append(["", "", "Amount Due", f"${total:,.2f}"])

    t = Table(rows, colWidths=[0.9 * inch, 0.9 * inch, 3.6 * inch, 1.2 * inch])
    style = [
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#8C1515")),  # Stanford cardinal
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ALIGN", (3, 0), (3, -1), "RIGHT"),
        ("GRID", (0, 0), (-1, -3), 0.5, colors.HexColor("#DDDDDD")),
        ("LINEABOVE", (0, -2), (-1, -2), 1, colors.black),
        ("FONTNAME", (2, -2), (3, -1), "Helvetica-Bold"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -3), [colors.white, colors.HexColor("#F7F7F7")]),
    ]
    t.setStyle(TableStyle(style))
    story.append(t)
    story.append(Spacer(1, 16))

    story.append(
        Paragraph(
            "Please remit payment within 30 days. For billing questions, contact "
            "Patient Billing Customer Service at 1-800-549-3720.",
            styles["Normal"],
        )
    )
    story.append(Spacer(1, 20))
    story.append(
        Paragraph(
            "SYNTHETIC DEMO DOCUMENT — generated for the Stanford x DeepMind Hackathon "
            "(ClearBill AI). Patient/account information is fictional. Dollar amounts are "
            "real Stanford Health Care gross charges published under the CMS Hospital Price "
            "Transparency Rule (45 CFR 180.50), file dated 2026-04-01.",
            styles["CenterNote"],
        )
    )

    doc.build(story)
    return total


def build_eob(bill_total):
    doc = SimpleDocTemplate(
        "sample_eob.pdf",
        pagesize=letter,
        topMargin=0.6 * inch,
        bottomMargin=0.6 * inch,
        leftMargin=0.6 * inch,
        rightMargin=0.6 * inch,
    )
    story = []

    story.append(Paragraph("<b>Cardinal Health Partners PPO</b>", styles["Title"]))
    story.append(Paragraph("Explanation of Benefits — This is not a bill", styles["Heading2"]))
    story.append(Spacer(1, 4))

    info_data = [
        ["Member:", "Jordan A. Sample", "Member ID:", "CHP-DEMO-778821"],
        ["Provider:", "Stanford Health Care", "Claim #:", "CLM-2026-0710-4471"],
        ["Date of Service:", "07/10/2026", "Processed:", "07/14/2026"],
    ]
    info_table = Table(info_data, colWidths=[1.2 * inch, 2.3 * inch, 1.2 * inch, 2.3 * inch])
    info_table.setStyle(
        TableStyle(
            [
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("FONTNAME", (2, 0), (2, -1), "Helvetica-Bold"),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    story.append(info_table)
    story.append(Spacer(1, 14))

    header = ["CPT", "Billed", "Allowed", "Plan Paid", "Patient Resp.", "Notes"]
    rows = [header]
    total_patient_resp = 0.0
    seen_36415 = 0
    for date, cpt, desc, charge in LINE_ITEMS:
        allowed = ALLOWED[cpt]
        if cpt == "36415":
            seen_36415 += 1
        if cpt == "36415" and seen_36415 == 2:
            plan_paid = 0.0
            patient_resp = 0.0
            note = "DENIED — duplicate of\nprior line item"
        else:
            plan_paid = round(allowed * 0.8, 2)
            patient_resp = round(allowed - plan_paid, 2)
            note = ""
        total_patient_resp += patient_resp
        rows.append(
            [
                cpt,
                f"${charge:,.2f}",
                f"${allowed:,.2f}",
                f"${plan_paid:,.2f}",
                f"${patient_resp:,.2f}",
                note,
            ]
        )
    rows.append(["", "", "", "", f"${total_patient_resp:,.2f}", "Total Patient Responsibility"])

    t = Table(rows, colWidths=[0.7 * inch, 0.9 * inch, 0.9 * inch, 0.9 * inch, 1.0 * inch, 1.6 * inch])
    style = [
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1A56DB")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("ALIGN", (1, 0), (4, -1), "RIGHT"),
        ("GRID", (0, 0), (-1, -2), 0.5, colors.HexColor("#DDDDDD")),
        ("LINEABOVE", (0, -1), (-1, -1), 1, colors.black),
        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
        ("TEXTCOLOR", (5, 1), (5, -2), colors.HexColor("#B91C1C")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -2), [colors.white, colors.HexColor("#F7F7F7")]),
    ]
    t.setStyle(TableStyle(style))
    story.append(t)
    story.append(Spacer(1, 16))

    story.append(
        Paragraph(
            f"Total billed by provider: ${bill_total:,.2f}. Your plan's allowed amount reflects "
            "negotiated rates, not the provider's list price. Duplicate services are not covered.",
            styles["Normal"],
        )
    )
    story.append(Spacer(1, 20))
    story.append(
        Paragraph(
            "SYNTHETIC DEMO DOCUMENT — generated for the Stanford x DeepMind Hackathon "
            "(ClearBill AI). All member/plan information is fictional and for demonstration only.",
            styles["CenterNote"],
        )
    )

    doc.build(story)
    return total_patient_resp


if __name__ == "__main__":
    total = build_bill()
    patient_resp = build_eob(total)
    print(f"Bill total: ${total:,.2f}")
    print(f"EOB patient responsibility: ${patient_resp:,.2f}")
    print(f"Gap ClearBill AI should catch (duplicate 36415 line + billed-vs-EOB mismatch): ${total - patient_resp:,.2f} (includes correctly-adjudicated insurance portion, not all overcharge)")
