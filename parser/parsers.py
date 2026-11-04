import calendar
import re
from abc import ABC, abstractmethod
from datetime import date, time

from transformer.calc import MONTHS, row_hours
from models import ReportType, ReportA, ReportB, AttendanceRowA, AttendanceRowB
from parser.parsing import parse_time, parse_date

BIDI = re.compile(r"[\u200e\u200f\u202a-\u202e\u2066-\u2069]")
DATE = re.compile(r"\d{1,2}/\d{1,2}/\d{2,4}")


class BaseParser(ABC):
    """מחלקת בסיס אבסטרקטית לפרסרים, המרכזת את הלוגיקה המשותפת (כגון ניקוי BIDI)."""
    def parse(self, txt: str):
        cleaned_txt = BIDI.sub("", txt)
        return self._parse(cleaned_txt)

    @abstractmethod
    def _parse(self, txt: str):
        pass


# ---------------------------- סוג B ----------------------------

ROW_TEXT_LAYER = re.compile(
    r"(\d{2}/\d{2}/\d{4})\s*[א-ת]+\s*([א-ת]*)\s*"
    r"(\d{2}:\d{2})\s+(\d{2}:\d{2})\s+(\d{2}:\d{2})"
    r"((?:\s+\d+\.\d+){1,5})"
)
ROW_OCR = re.compile(
    r"(\d{1,2}:\d{2})[ \t]+(\d{1,2}:\d{2})[ \t]+(\d{1,2}:\d{2})((?:[ \t]+\d+\.\d+){1,5})"
)


def _make_row(row_date, workplace, start, end, brk, nums_str) -> AttendanceRowB:
    nums = [round(float(x), 2) for x in nums_str.split()]
    total, h100, h125, h150, shabbat = (nums + [0.0] * 5)[:5]
    b = parse_time(brk)
    return AttendanceRowB(
        date=row_date, start=parse_time(start), end=parse_time(end),
        break_minutes=b.hour * 60 + b.minute, total_hours=total,
        hours_100=h100, hours_125=h125, hours_150=h150,
        workplace=workplace, shabbat_hours=shabbat,
    )


def _rows_text_layer(txt: str) -> list[AttendanceRowB]:
    return [
        _make_row(parse_date(m.group(1)), m.group(2), m.group(3), m.group(4), m.group(5), m.group(6))
        for m in ROW_TEXT_LAYER.finditer(txt)
    ]


def _rows_ocr(txt: str) -> list[AttendanceRowB]:
    rows, last_date = [], None
    for line in txt.splitlines():
        m = ROW_OCR.search(line)
        if not m:
            continue
        d = DATE.search(line)
        if d:
            last_date = parse_date(d.group())
        row_date = last_date or date.today().replace(day=1)
        rows.append(_make_row(row_date, "", *m.groups()))
    return rows


class ParserB(BaseParser):
    def _parse(self, txt: str) -> ReportB:
        rows = _rows_text_layer(txt) or _rows_ocr(txt)
        if not rows:
            raise ValueError("לא נמצאו שורות נוכחות בטקסט. בדקי את ocr_output.txt")

        dates = [r.date for r in rows]
        return ReportB(
            employee_name="",
            period_start=min(dates), period_end=max(dates),
            rows=rows, days=len(rows),
            total_hours=round(sum(r.total_hours for r in rows), 2),
            hours_100=round(sum(r.hours_100 for r in rows), 2),
            hours_125=round(sum(r.hours_125 for r in rows), 2),
            hours_150=round(sum(r.hours_150 for r in rows), 2),
            shabbat_150=round(sum(r.shabbat_hours for r in rows), 2),
        )


# ---------------------------- סוג A ----------------------------

_DATE = re.compile(r"(?<!\d)(\d{1,2})/(\d{1,2})/(\d{2,4})(?!\d)")
_TIME = re.compile(r"(?<!\d)(\d{1,2}):(\d{2})(?!\d)")
_MONEY = re.compile(r"\d{1,3}(?:,\d{3})+\.\d{2}|\d+\.\d{2}")


def _to_date(m):
    d, mo, y = (int(g) for g in m.groups())
    try:
        return date(y + 2000 if y < 100 else y, mo, d)
    except ValueError:
        return None


def _row(d, text):
    ts = [time(int(h), int(mi)) for h, mi in _TIME.findall(text)
          if int(h) < 24 and int(mi) < 60]
    if len(ts) < 2:
        return AttendanceRowA(d)
    start, end = sorted(ts[:2])
    return AttendanceRowA(d, start, end, row_hours(start, end))


def _rows_by_line(txt):
    rows = []
    for line in txt.splitlines():
        m = _DATE.search(line)
        d = _to_date(m) if m else None
        if d:
            rows.append(_row(d, line[:m.start()] + " " + line[m.end():]))
    return rows


def _rows_by_chunk(txt):
    ms = list(_DATE.finditer(txt))
    rows = []
    for i, m in enumerate(ms):
        d = _to_date(m)
        end = ms[i + 1].start() if i + 1 < len(ms) else len(txt)
        if d:
            rows.append(_row(d, txt[m.end():end]))
    return rows


def _full_month(rows):
    by = {}
    for r in rows:
        if r.date not in by or (r.is_work_day and not by[r.date].is_work_day):
            by[r.date] = r
    first = min(by)
    y, m = first.year, first.month
    last = calendar.monthrange(y, m)[1]
    return [by.get(date(y, m, d)) or AttendanceRowA(date(y, m, d)) for d in range(1, last + 1)]


def _summary(txt, row_sum):
    nums = [float(x.replace(",", "")) for x in _MONEY.findall(txt)]
    if not nums:
        return round(row_sum, 2), 0.0, 0.0
    pay = max(nums)
    rest = [n for n in nums if n != pay]
    for h in rest:
        for r in rest:
            if h != r and abs(h - row_sum) <= 1 and abs(h * r - pay) < 1.0:
                return h, r, pay
    hours = round(row_sum, 2)
    return hours, (round(pay / hours, 2) if hours else 0.0), pay


class ParserA(BaseParser):
    def _parse(self, txt: str) -> ReportA:
        rows = _rows_by_line(txt)
        if not any(r.is_work_day for r in rows):
            rows = _rows_by_chunk(txt)
        if not any(r.is_work_day for r in rows):
            raise ValueError("לא נמצאו שורות בכרטיס A. בדקי את ocr_card_a.txt")

        rows = _full_month(rows)
        hours, rate, pay = _summary(txt, sum(r.total_hours or 0 for r in rows))
        first = rows[0].date
        return ReportA(
            employee_name="",
            card_label=f"{MONTHS[first.month - 1]}-{first.year % 100}",
            period_start=rows[0].date, period_end=rows[-1].date, rows=rows,
            work_days=sum(r.is_work_day for r in rows),
            total_hours=hours, hourly_rate=rate, total_pay=pay,
        )


def get_parser(report_type: ReportType) -> BaseParser:
    """פונקציית מפעל המחזירה את הפרסר המתאים לסוג הדו"ח ללא תנאי if."""
    parsers = {
        ReportType.A: ParserA(),
        ReportType.B: ParserB(),
    }
    if report_type not in parsers:
        raise ValueError(f"סוג דו\"ח לא מוכר: {report_type}")
    return parsers[report_type]


PARSERS = {
    ReportType.A: ParserA(),
    ReportType.B: ParserB(),
}