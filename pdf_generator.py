"""Render an Invoice to a PDF file using ReportLab."""

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer,
)

from invoice_models import Invoice

ACCENT = colors.HexColor("#1F3864")
LIGHT = colors.HexColor("#EAF0FA")


def _styles():
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle("Head", parent=styles["Title"],
                              textColor=ACCENT, fontSize=22, spaceAfter=2))
    styles.add(ParagraphStyle("Label", parent=styles["Normal"],
                              textColor=ACCENT, fontSize=8, leading=10,
                              spaceAfter=1, fontName="Helvetica-Bold"))
    styles.add(ParagraphStyle("Body", parent=styles["Normal"],
                              fontSize=9, leading=12))
    styles.add(ParagraphStyle("Small", parent=styles["Normal"],
                              fontSize=8, leading=11, textColor=colors.HexColor("#555555")))
    return styles


def _party_block(party, styles):
    txt = f"<b>{party.name}</b><br/>{party.address}<br/>{party.city}<br/>{party.country}"
    if party.tax_id:
        txt += f"<br/>Tax ID: {party.tax_id}"
    return Paragraph(txt, styles["Body"])


def invoice_to_pdf(invoice: Invoice, path: str) -> str:
    styles = _styles()
    cfg = invoice.region_config
    doc = SimpleDocTemplate(path, pagesize=A4,
                            leftMargin=18 * mm, rightMargin=18 * mm,
                            topMargin=16 * mm, bottomMargin=16 * mm)
    elements = []

    # Header
    header = Table([[
        Paragraph("COMMERCIAL INVOICE", styles["Head"]),
        Paragraph(
            f"<b>No.</b> {invoice.number}<br/>"
            f"<b>Date:</b> {invoice.issue_date:%d %b %Y}<br/>"
            f"<b>Incoterm:</b> {invoice.incoterm}<br/>"
            f"<b>Currency:</b> {cfg.currency}",
            styles["Small"]),
    ]], colWidths=[105 * mm, 69 * mm])
    header.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ALIGN", (1, 0), (1, 0), "RIGHT"),
    ]))
    elements += [header, Spacer(1, 8 * mm)]

    # Seller / Buyer
    parties = Table([
        [Paragraph("SELLER / EXPORTER", styles["Label"]),
         Paragraph("BUYER / CONSIGNEE", styles["Label"])],
        [_party_block(invoice.seller, styles),
         _party_block(invoice.buyer, styles)],
    ], colWidths=[87 * mm, 87 * mm])
    parties.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 4),
    ]))
    elements += [parties, Spacer(1, 8 * mm)]

    # Items table
    data = [["#", "Description", "Qty", "Unit price", "Amount"]]
    for i, item in enumerate(invoice.items, 1):
        data.append([
            str(i), item.description, f"{item.quantity:g}",
            invoice.money(item.unit_price), invoice.money(item.amount),
        ])
    items = Table(data, colWidths=[10 * mm, 86 * mm, 16 * mm, 30 * mm, 32 * mm])
    items.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), ACCENT),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ALIGN", (2, 0), (-1, -1), "RIGHT"),
        ("ALIGN", (0, 0), (0, -1), "CENTER"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT]),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#CCCCCC")),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    elements += [items, Spacer(1, 6 * mm)]

    # Totals
    totals_rows = [["Subtotal", invoice.money(invoice.subtotal)]]
    if cfg.show_trade_terms:
        totals_rows.append(["Freight", invoice.money(invoice.freight)])
        totals_rows.append(["Insurance", invoice.money(invoice.insurance)])
    totals_rows.append(["TOTAL", invoice.money(invoice.total)])
    totals = Table(totals_rows, colWidths=[32 * mm, 32 * mm], hAlign="RIGHT")
    totals.setStyle(TableStyle([
        ("ALIGN", (0, 0), (-1, -1), "RIGHT"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("LINEABOVE", (0, -1), (-1, -1), 0.8, ACCENT),
        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
        ("TEXTCOLOR", (0, -1), (-1, -1), ACCENT),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
    ]))
    elements += [totals, Spacer(1, 8 * mm)]

    # Bank details
    bank_lines = f"<b>{cfg.bank_name}</b><br/>" + "<br/>".join(
        f"{k}: {v}" for k, v in cfg.bank_details.items())
    elements += [
        Paragraph("PAYMENT / BANK DETAILS", styles["Label"]),
        Paragraph(bank_lines, styles["Small"]),
        Spacer(1, 5 * mm),
    ]

    if invoice.notes:
        elements += [Paragraph("NOTES", styles["Label"]),
                     Paragraph(invoice.notes, styles["Small"])]

    doc.build(elements)
    return path
