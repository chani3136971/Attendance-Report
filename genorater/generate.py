from datetime import date
from pathlib import Path

from bidi.algorithm import get_display
from reportlab import rl_config

from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from models import ReportA
from reportlab.platypus import SimpleDocTemplate, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from models import ReportB


rl_config.invariant = 1      # בלי חותמת זמן ומזהה אקראי בתוך ה-PDF, כדי שהפלט יהיה זהה בין הרצות

pdfmetrics.registerFont(TTFont("Heb", r"C:\Windows\Fonts\arial.ttf"))
pdfmetrics.registerFont(TTFont("HebBold", r"C:\Windows\Fonts\arialbd.ttf"))

GREY = colors.Color(0.82, 0.82, 0.82)


def h(s) -> str:
    return get_display(str(s))


def _d(d: date) -> str:
    return f"{d.day}/{d.month}/{d.year % 100}"      # 1/1/23


def _t(t) -> str:
    return f"{t.hour}:{t.minute:02d}"               # 8:01


def _table(data, widths, header=False, extra=()):
    style = [
        ("FONT", (0, 0), (-1, -1), "Heb", 9),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("TOPPADDING", (0, 0), (-1, -1), 1),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
    ]
    if header:
        style.append(("BACKGROUND", (0, 0), (-1, 0), GREY))
    t = Table(data, colWidths=widths, hAlign="RIGHT")   # הכול מיושר לקצה הימני
    t.setStyle(TableStyle(style + list(extra)))
    return t


def generate_pdf(r: ReportA, out_path: Path) -> Path:
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # העמודות משמאל לימין, כך שהתאריך יוצא בצד ימין
    header = ["הערות", "סה\"כ שעות", "שעת יציאה", "שעת כניסה", "יום בשבוע", "תאריך"]
    data = [[h(c) for c in header]]
    shaded = []
    for i, x in enumerate(r.rows, 1):
        data.append([
            h(x.notes) if x.notes else "",
            f"{x.total_hours:.2f}" if x.is_work_day else "",
            _t(x.end) if x.is_work_day else "",
            _t(x.start) if x.is_work_day else "",
            h(x.weekday), _d(x.date),
        ])
        if x.weekday == "שבת":
            shaded.append(("BACKGROUND", (0, i), (-1, i), GREY))

    summary = [
        [h(r.employee_name), h("שם העובד:")],
        [r.work_days, h("סה\"כ ימי עבודה לחודש")],
        [f"{r.total_hours:.2f}", h("סה\"כ שעות חודשיות")],
        [f"₪ {r.hourly_rate:.2f}", h("מחיר לשעה")],
        [f"₪ {r.total_pay:,.2f}", h("סה\"כ לתשלום")],
    ]
    summary_extra = [
        ("FONT", (1, 0), (1, -1), "HebBold", 9),          # תוויות מודגשות
        ("BACKGROUND", (1, 0), (1, 0), GREY),             # תווית שם העובד באפור
    ]
    title = [[r.card_label, h("כרטיס עובד לחודש:")]]
    title_extra = [("BACKGROUND", (0, 0), (-1, 0), GREY),
                   ("FONT", (0, 0), (-1, -1), "HebBold", 9)]

    doc = SimpleDocTemplate(str(out_path), pagesize=A4, topMargin=30, bottomMargin=30)
    doc.build([
        _table(summary, [90, 170], extra=summary_extra), Spacer(1, 10),
        _table(title, [90, 170], extra=title_extra), Spacer(1, 10),
        _table(data, [70, 60, 60, 60, 60, 60], header=True, extra=shaded),
    ])
    return out_path


from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle


def generate_pdf_b(r: ReportB, out_path: Path) -> Path:
    out_path.parent.mkdir(parents=True, exist_ok=True)

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'TitleStyle',
        parent=styles['Normal'],
        fontName='HebBold',
        fontSize=16,
        alignment=1,  # מרכז
        spaceAfter=6
    )
    sub_style = ParagraphStyle(
        'SubStyle',
        parent=styles['Normal'],
        fontName='Heb',
        fontSize=11,
        alignment=1,  # מרכז
        spaceAfter=15
    )
    summary_title_style = ParagraphStyle(
        'SummaryTitle',
        parent=styles['Normal'],
        fontName='HebBold',
        fontSize=11,
        alignment=2,  # ימין
        spaceAfter=5
    )
    summary_text_style = ParagraphStyle(
        'SummaryText',
        parent=styles['Normal'],
        fontName='Heb',
        fontSize=10,
        alignment=2,  # ימין
        spaceAfter=3
    )

    story = []

    # כותרת ראשית ושם עובד בהתאם לתבנית
    story.append(Paragraph("Attendance Report - Type B", title_style))
    emp_name = r.employee_name if r.employee_name else "לא זוהה"
    story.append(Paragraph(f"שם העובד: {emp_name}", sub_style))
    story.append(Spacer(1, 5))

    # כותרות העמודות בדיוק כמו בתבנית (משמאל לימין בטבלה)
    header = ["150%", "125%", "100%", "TOTAL", "BREAK", "EXIT", "ENTRY", "LOCATION", "DAY", "DATE"]
    data = [header]

    for x in r.rows:
        break_str = f"{x.break_minutes // 60:02d}:{x.break_minutes % 60:02d}" if hasattr(x,
                                                                                         'break_minutes') and x.break_minutes else "00:30"
        data.append([
            f"{x.hours_150:.2f}" if x.hours_150 else "",
            f"{x.hours_125:.2f}" if x.hours_125 else "",
            f"{x.hours_100:.2f}" if x.hours_100 else "",
            f"{x.total_hours:.2f}" if x.total_hours else "",
            break_str,
            _t(x.end) if x.end else "",
            _t(x.start) if x.start else "",
            str(x.workplace) if hasattr(x, 'workplace') and x.workplace else "",
            h(x.weekday) if x.weekday else "",
            _d(x.date) if x.date else "",
        ])

    # יצירת הטבלה עם רוחבי עמודות מותאמים
    table = _table(data, [45, 45, 45, 50, 50, 50, 50, 55, 50, 65], header=True)
    story.append(table)
    story.append(Spacer(1, 15))

    # חלק הסיכום בתחתית מיושר לימין בהתאם לתבנית
    story.append(Paragraph(":Summary", summary_title_style))
    story.append(Paragraph(f"Total Days: {r.days}", summary_text_style))
    story.append(Paragraph(f"Total Hours: {r.total_hours:.2f}", summary_text_style))
    story.append(Paragraph(f"Hours: {r.total_hours:.2f} 100%", summary_text_style))

    doc = SimpleDocTemplate(str(out_path), pagesize=A4, topMargin=30, bottomMargin=30)
    doc.build(story)
    return out_path