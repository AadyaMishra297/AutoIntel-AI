"""
report_generator.py — PDF diagnosis report builder for AutoIntel AI.

Pure presentation/output helper: takes an already-assembled dict of
diagnosis data (built by app.py from the existing db.py /
complaint_adapter.py results) and renders a professional PDF using
ReportLab. Contains no database access and no complaint-matching logic.
"""

import io
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    HRFlowable,
)

NAVY = colors.HexColor("#1d4ed8")
DARK = colors.HexColor("#101828")
GREY = colors.HexColor("#475467")
LIGHT_BG = colors.HexColor("#f8fafc")
BORDER = colors.HexColor("#e2e8f0")


def _styles():
    base = getSampleStyleSheet()
    styles = {
        "title": ParagraphStyle(
            "ReportTitle", parent=base["Title"], textColor=DARK, fontSize=18, spaceAfter=2,
        ),
        "subtitle": ParagraphStyle(
            "ReportSubtitle", parent=base["Normal"], textColor=GREY, fontSize=9, spaceAfter=10,
        ),
        "h2": ParagraphStyle(
            "H2", parent=base["Heading2"], textColor=NAVY, fontSize=12.5,
            spaceBefore=14, spaceAfter=6,
        ),
        "body": ParagraphStyle(
            "Body", parent=base["Normal"], textColor=DARK, fontSize=9.5, leading=14,
        ),
        "small": ParagraphStyle(
            "Small", parent=base["Normal"], textColor=GREY, fontSize=8.5, leading=12,
        ),
        "footer": ParagraphStyle(
            "Footer", parent=base["Normal"], textColor=GREY, fontSize=8, alignment=1,
        ),
    }
    return styles


def _kv_table(pairs, col_widths=(45 * mm, 115 * mm)):
    """Render a list of (label, value) pairs as a clean two-column table."""
    styles = _styles()
    data = [
        [Paragraph(f"<b>{label}</b>", styles["small"]), Paragraph(str(value), styles["body"])]
        for label, value in pairs
        if value not in (None, "")
    ]
    if not data:
        return Paragraph("No data on file.", styles["small"])
    table = Table(data, colWidths=list(col_widths))
    table.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("LINEBELOW", (0, 0), (-1, -1), 0.4, BORDER),
            ]
        )
    )
    return table


def _bullet_list(items):
    styles = _styles()
    if not items:
        return Paragraph("No entries on file.", styles["small"])
    text = "<br/>".join(f"&bull;&nbsp;&nbsp;{item}" for item in items)
    return Paragraph(text, styles["body"])


def build_pdf_report(data: dict) -> bytes:
    """
    Build the diagnosis report PDF.

    Expected keys in `data` (all optional except noted):
      vehicle_label, vehicle_details (list[str])
      complaint_text
      similarity_score_pct, similarity_status
      obd_code, obd_description, fault_description, severity
      repair_solution, estimated_cost, estimated_time
      vehicle_health_score, health_status, maintenance_risk
      maintenance_history (list[str])
      preventive_maintenance (list[str])
      ai_explanation (list[str])
      generated_at (str)
    """
    styles = _styles()
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=16 * mm,
        bottomMargin=16 * mm,
        title="AutoIntel AI Diagnosis Report",
    )

    story = []

    story.append(Paragraph("AutoIntel AI — Vehicle Diagnosis Report", styles["title"]))
    story.append(Paragraph(f"Generated: {data.get('generated_at', '')}", styles["subtitle"]))
    story.append(HRFlowable(width="100%", thickness=0.8, color=BORDER))

    # Vehicle & Complaint
    story.append(Paragraph("Vehicle Details", styles["h2"]))
    vehicle_pairs = [("Vehicle", data.get("vehicle_label"))]
    for line in data.get("vehicle_details", []):
        if ":" in line:
            k, v = line.split(":", 1)
            vehicle_pairs.append((k.strip(), v.strip()))
    story.append(_kv_table(vehicle_pairs))

    story.append(Paragraph("Complaint", styles["h2"]))
    story.append(Paragraph(data.get("complaint_text", "N/A"), styles["body"]))

    # Similarity Score
    story.append(Paragraph("Similarity Score", styles["h2"]))
    story.append(
        _kv_table(
            [
                ("Similarity Score", f"{data.get('similarity_score_pct', 0):.0f}%"),
                ("Status", data.get("similarity_status", "N/A")),
            ]
        )
    )

    # Detected Fault
    story.append(Paragraph("Detected Fault", styles["h2"]))
    story.append(
        _kv_table(
            [
                ("OBD Code", data.get("obd_code")),
                ("Description", data.get("obd_description")),
                ("Fault Description", data.get("fault_description")),
                ("Severity", data.get("severity")),
            ]
        )
    )

    # Repair Solution
    story.append(Paragraph("Repair Solution", styles["h2"]))
    story.append(Paragraph(data.get("repair_solution", "N/A"), styles["body"]))
    story.append(Spacer(1, 4))
    story.append(
        _kv_table(
            [
                ("Estimated Cost", data.get("estimated_cost")),
                ("Estimated Time", data.get("estimated_time")),
            ]
        )
    )

    # Vehicle Health
    story.append(Paragraph("Vehicle Health", styles["h2"]))
    story.append(
        _kv_table(
            [
                ("Vehicle Health Score", data.get("vehicle_health_score")),
                ("Health Status", data.get("health_status")),
                ("Maintenance Risk", data.get("maintenance_risk")),
            ]
        )
    )

    # Maintenance History
    story.append(Paragraph("Maintenance History", styles["h2"]))
    story.append(_bullet_list(data.get("maintenance_history", [])))

    # Preventive Maintenance
    story.append(Paragraph("Preventive Maintenance", styles["h2"]))
    story.append(_bullet_list(data.get("preventive_maintenance", [])))

    # AI Explanation
    story.append(Paragraph("AI Explanation", styles["h2"]))
    story.append(_bullet_list(data.get("ai_explanation", [])))

    story.append(Spacer(1, 16))
    story.append(HRFlowable(width="100%", thickness=0.6, color=BORDER))
    story.append(Spacer(1, 4))
    story.append(Paragraph("Generated by AutoIntel AI", styles["footer"]))

    doc.build(story)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes
