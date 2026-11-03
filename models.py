from dataclasses import dataclass
from datetime import date, time, timedelta
from enum import Enum
from typing import ClassVar

WEEKDAYS_HE = ["שני", "שלישי", "רביעי", "חמישי", "שישי", "שבת", "ראשון"]  # לפי date.weekday()
TOL = 0.01
MAX_DAYS = 31              # תקופת דו"ח לא ארוכה מחודש (בכרטיס A יש 31 שורות לספטמבר)
DAILY_100_LIMIT = 8.0      # להתאים לתלוש
OVERTIME_125_LIMIT = 2.0   # להתאים לתלוש
MIN_DAY_HOURS = 6.0        # יום עבודה לא יכול להיות קצר מ-6 שעות  <-- חדש


class ReportType(Enum):
    A = "A"
    B = "B"
    UNKNOWN = "UNKNOWN"


def weekday_he(d: date) -> str:
    return WEEKDAYS_HE[d.weekday()]


def minutes(t: time) -> int:
    return t.hour * 60 + t.minute


def check_times(i, start, end, break_min, total) -> list[str]:
    if end <= start:
        return [f"שורה {i}: היציאה לא מאוחרת מהכניסה"]
    calc = (minutes(end) - minutes(start) - break_min) / 60
    if abs(calc - total) > TOL:
        return [f"שורה {i}: סה\"כ {total}, אבל יציאה פחות כניסה פחות הפסקה = {calc:.2f}"]
    return []


def check_period(rows, start: date, end: date) -> list[str]:
    errs, today = [], date.today()
    if end < start or (end - start).days + 1 > MAX_DAYS:
        errs.append("תקופת הדו\"ח הפוכה או ארוכה מחודש")
    for i, r in enumerate(rows, 1):
        if not (start <= r.date <= end):
            errs.append(f"שורה {i}: התאריך מחוץ לתקופת הדו\"ח")
        if r.date > today:
            errs.append(f"שורה {i}: תאריך עתידי")
    return errs


# ================= סוג A: כרטיס עובד =================

@dataclass
class AttendanceRowA:
    date: date
    start: time | None = None          # None ביום בלי עבודה (שבת / חג / יום חול ריק)
    end: time | None = None
    total_hours: float | None = None
    notes: str = ""                    # למשל "ראש השנה"

    @property
    def weekday(self) -> str:
        return weekday_he(self.date)

    @property
    def is_work_day(self) -> bool:
        return self.total_hours is not None

    def validate(self, i: int, check_min_day: bool = True) -> list[str]:      # <-- שונה
        given = [self.start, self.end, self.total_hours]
        if any(g is None for g in given) and any(g is not None for g in given):
            return [f"שורה {i}: כניסה, יציאה וסה\"כ חייבים להופיע יחד"]
        if not self.is_work_day:
            return []
        if self.weekday == "שבת":
            return [f"שורה {i}: שעות בשבת (בדוגמה אין)"]
        errs = check_times(i, self.start, self.end, 0, self.total_hours)
        if check_min_day and self.total_hours < MIN_DAY_HOURS - TOL:          # <-- חדש
            errs.append(f"שורה {i}: יום עבודה קצר מ-{MIN_DAY_HOURS:g} שעות ({self.total_hours})")
        return errs


@dataclass
class ReportA:
    report_type: ClassVar[ReportType] = ReportType.A

    employee_name: str
    card_label: str                    # "ספט-22", מודפס ליד "כרטיס עובד לחודש"
    period_start: date
    period_end: date
    rows: list[AttendanceRowA]         # כל יום בתקופה, ברצף
    work_days: int                     # "סה\"כ ימי עבודה לחודש" מהכותרת
    total_hours: float
    hourly_rate: float
    total_pay: float

    def validate(self, check_min_day: bool = True) -> list[str]:              # <-- שונה
        errs = []
        for i, r in enumerate(self.rows, 1):
            errs += r.validate(i, check_min_day)                              # <-- שונה
        errs += check_period(self.rows, self.period_start, self.period_end)
        if self.rows and (self.rows[0].date, self.rows[-1].date) != (self.period_start, self.period_end):
            errs.append("השורות לא מכסות את כל התקופה")
        for i in range(1, len(self.rows)):
            if self.rows[i].date != self.rows[i - 1].date + timedelta(days=1):
                errs.append(f"שורה {i + 1}: התאריך לא ממשיך ברצף")
        if abs(sum(r.total_hours or 0 for r in self.rows) - self.total_hours) > TOL:
            errs.append("סה\"כ השעות לא שווה לסכום השורות")
        if abs(self.total_hours * self.hourly_rate - self.total_pay) > TOL:
            errs.append("סה\"כ לתשלום לא שווה לשעות כפול מחיר לשעה")
        if not 0 < self.work_days <= len(self.rows):
            errs.append("ימי עבודה בכותרת לא סבירים ביחס למספר השורות")
        return errs


# ================= סוג B: Attendance Report - Type B =================

@dataclass
class AttendanceRowB:
    date: date
    start: time
    end: time
    break_minutes: int
    total_hours: float
    hours_100: float = 0.0
    hours_125: float = 0.0
    hours_150: float = 0.0
    workplace: str = ""                # LOCATION, ריק בדוגמה
    shabbat_hours: float = 0.0         # קיים רק בסריקה המקורית

    @property
    def weekday(self) -> str:
        return weekday_he(self.date)

    def validate(self, i: int) -> list[str]:
        errs = check_times(i, self.start, self.end, self.break_minutes, self.total_hours)
        parts = self.hours_100 + self.hours_125 + self.hours_150 + self.shabbat_hours
        if abs(parts - self.total_hours) > TOL:
            errs.append(f"שורה {i}: סכום העמודות (100/125/150/שבת) לא שווה לסה\"כ")
        if (self.hours_125 > 0 or self.hours_150 > 0) and self.hours_100 < DAILY_100_LIMIT - TOL:
            errs.append(f"שורה {i}: שעות נוספות לפני שה-100% מלא")
        if self.hours_150 > 0 and self.hours_125 < OVERTIME_125_LIMIT - TOL:
            errs.append(f"שורה {i}: 150% לפני שה-125% מלא")
        return errs


@dataclass
class ReportB:
    report_type: ClassVar[ReportType] = ReportType.B
    TITLE: ClassVar[str] = "Attendance Report - Type B"

    employee_name: str                 # "שם העובד" (בדוגמה: "לא זוהה")
    period_start: date
    period_end: date
    rows: list[AttendanceRowB]
    days: int                          # Total Days = מספר שורות, לא תאריכים שונים
    total_hours: float
    hours_100: float = 0.0
    hours_125: float = 0.0
    hours_150: float = 0.0
    shabbat_150: float = 0.0           # רק בסריקה המקורית
    bonus: float | None = None         # רק בסריקה המקורית
    travel: float | None = None        # רק בסריקה המקורית
    company_name: str | None = None    # רק בסריקה המקורית ("הנשר כח אדם")

    def validate(self) -> list[str]:
        errs = []
        for i, r in enumerate(self.rows, 1):
            errs += r.validate(i)
        errs += check_period(self.rows, self.period_start, self.period_end)
        for i in range(1, len(self.rows)):
            p, c = self.rows[i - 1], self.rows[i]
            if (c.date, c.start) < (p.date, p.start):
                errs.append(f"שורה {i + 1}: לא ממוינת לפי תאריך ושעה")
            elif c.date == p.date and minutes(c.start) < minutes(p.end):
                errs.append(f"שורה {i + 1}: חופפת למשמרת הקודמת באותו יום")
        if self.days != len(self.rows):
            errs.append("Total Days לא שווה למספר השורות")
        for name, col in [("total_hours", "total_hours"), ("hours_100", "hours_100"),
                          ("hours_125", "hours_125"), ("hours_150", "hours_150"),
                          ("shabbat_150", "shabbat_hours")]:
            if abs(sum(getattr(r, col) for r in self.rows) - getattr(self, name)) > TOL:
                errs.append(f"הסיכום של {name} לא שווה לסכום השורות")
        return errs


REPORT_CLASSES = {ReportType.A: ReportA, ReportType.B: ReportB}