# award/report.py
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table,
                                 TableStyle, PageBreak)

def render_award_report(report: dict, tender_meta: dict, path: str):
    styles = getSampleStyleSheet()
    doc = SimpleDocTemplate(path, pagesize=A4,
                            title=f"Award report — {tender_meta['reference']}",
                            author="Evaluation system")
    story = [
        Paragraph(f"Award recommendation — {tender_meta['title']}", styles["Title"]),
        Paragraph(f"Reference: {tender_meta['reference']}", styles["Normal"]),
        Paragraph(f"Formula: {report['formula'].upper()}", styles["Normal"]),
        Paragraph(f"Computed: {report['computed_at']}", styles["Normal"]),
        Spacer(1, 12),
    ]

    headers = ["Rank", "Bidder", "Tech", "Price (SGD)", "Fee", "Final", "Status"]
    data = [headers]
    for b in sorted(report["bidders"], key=lambda x: (x["rank"] is None, x["rank"])):
        status = ("Winner" if b["rank"] == 1 else
                  b["ineligible_reason"] or "Eligible" if b["rank"] else
                  b["ineligible_reason"] or "Not ranked")
        data.append([
            str(b["rank"]) if b["rank"] else "—",
            b["bidder_name"],
            b["technical_score"],
            b["evaluated_price"] or "—",
            b["fee_score"] or "—",
            b["final_score"] or "—",
            status,
        ])
    t = Table(data, colWidths=[40, 140, 55, 80, 50, 55, 90])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#eeeeee")),
        ("FONT", (0,0), (-1,0), "Helvetica-Bold"),
        ("FONT", (0,0), (-1,-1), "Helvetica", 8),
        ("GRID", (0,0), (-1,-1), 0.5, colors.grey),
        ("VALIGN", (0,0), (-1,-1), "TOP"),
    ]))
    story.append(t)
    story.append(Spacer(1, 18))

    # per-bidder detail
    for b in report["bidders"]:
        story.append(PageBreak())
        story.append(Paragraph(f"{b['bidder_name']}", styles["Heading2"]))
        story.append(Paragraph(
            f"Technical: <b>{b['technical_score']}</b> · "
            f"Price: <b>{b['evaluated_price'] or '—'}</b> · "
            f"Rank: <b>{b['rank'] or '—'}</b>", styles["Normal"]))
        story.append(Paragraph(f"Compliance: {b['compliance_summary']}", styles["Normal"]))
        if b["ineligible_reason"]:
            story.append(Paragraph(
                f"<font color='red'>Ineligible: {b['ineligible_reason']}</font>",
                styles["Normal"]))
        story.append(Spacer(1, 8))
        story.append(Paragraph(
            "Full evidence, criterion scores and compliance matrix are available "
            "in the sealed technical and commercial envelopes.", styles["Italic"]))

    story.append(Spacer(1, 24))
    story.append(Paragraph(
        f"Report hash (SHA-256): <font face='Courier' size='7'>{report.get('report_hash', '')}</font>",
        styles["Normal"]))
    doc.build(story)
