import calendar
import random
from dataclasses import dataclass
from datetime import date, time

from transformer.calc import MONTHS, row_hours
from models import MIN_DAY_HOURS, AttendanceRowA, ReportA, minutes
from collections import defaultdict

from datetime import timedelta
from models import ReportB, AttendanceRowB

@dataclass
class Conditions:
    """התנאים להגרלה. ערך None = לקחת מהמקור."""
    year: int
    month: int
    name: str = ""
    work_days: int | None = None                   # כמה ימי עבודה בחודש
    weekdays: set[int] | None = None               # Python: שני=0 ... שבת=5, ראשון=6
    start_range: tuple[int, int] | None = None     # טווח שעת כניסה, בדקות מחצות
    duration_range: tuple[int, int] | None = None  # טווח אורך משמרת, בדקות
    rate: float | None = None                      # מחיר לשעה


def _hm(mins: int) -> time:
    return time(mins // 60, mins % 60)


def recalc(r: ReportA) -> ReportA:
    """מחשבת מחדש הכול מהכניסה והיציאה: שעות לשורה, סה"כ, ימי עבודה ותשלום.
    חובה לקרוא לה אחרי כל שינוי בשעות."""
    for x in r.rows:
        if x.start is not None and x.end is not None:      # לא לפי total_hours, שעוד לא חושב
            x.total_hours = row_hours(x.start, x.end)
        else:
            x.total_hours = None
    r.total_hours = round(sum(x.total_hours or 0 for x in r.rows), 2)
    r.work_days = sum(x.is_work_day for x in r.rows)
    r.total_pay = round(r.total_hours * r.hourly_rate, 2)
    return r


def make_variation(src: ReportA, seed: int, c: Conditions) -> ReportA:
    rng = random.Random(seed)              # תמיד עם seed: אותו seed נותן אותו דו"ח
    work = [r for r in src.rows if r.is_work_day]
    if not work:
        raise ValueError("במקור אין ימי עבודה להסיק מהם ברירות מחדל")

    starts = [minutes(r.start) for r in work]
    durs = [minutes(r.end) - minutes(r.start) for r in work]
    start_lo, start_hi = c.start_range or (min(starts), max(starts))
    dur_lo, dur_hi = c.duration_range or (min(durs), max(durs))

    # הכלל: יום עבודה לא קצר מ-6 שעות
    dur_lo = max(dur_lo, int(MIN_DAY_HOURS * 60))
    if dur_hi < dur_lo:
        raise ValueError(
            f"אורך משמרת מקסימלי קצר מ-{MIN_DAY_HOURS:g} שעות. הגדירי duration_range בתנאים")

    weekdays = (c.weekdays or {r.date.weekday() for r in work}) - {5}    # בלי שבת
    n_days = c.work_days or len(work)
    rate = c.rate if c.rate is not None else src.hourly_rate

    last = calendar.monthrange(c.year, c.month)[1]
    if date(c.year, c.month, last) >= date.today():
        raise ValueError("החודש שנבחר עדיין לא הסתיים. בחרי חודש שעבר")
    candidates = [date(c.year, c.month, d) for d in range(1, last + 1)
                  if date(c.year, c.month, d).weekday() in weekdays]
    chosen = set(rng.sample(candidates, min(n_days, len(candidates))))

    rows = []
    for d in range(1, last + 1):               # מעבר לפי סדר הימים, לא לפי סדר ה-set
        day = date(c.year, c.month, d)
        if day in chosen:
            start = _hm(rng.randint(start_lo, start_hi))
            end = _hm(minutes(start) + rng.randint(dur_lo, dur_hi))
            rows.append(AttendanceRowA(day, start, end))
        else:
            rows.append(AttendanceRowA(day))

    report = ReportA(
        employee_name=c.name,
        card_label=f"{MONTHS[c.month - 1]}-{c.year % 100}",
        period_start=rows[0].date, period_end=rows[-1].date, rows=rows,
        work_days=0, total_hours=0.0, hourly_rate=rate, total_pay=0.0,
    )
    return recalc(report) # כל הסכומים נגזרים מהשורות




def make_variation_b(src: ReportB, seed: int, conditions) -> ReportB:
    rng = random.Random(seed)

    # קיבוץ לפי תאריך כדי לטפל במשמרות באותו היום
    by_date = defaultdict(list)
    for r in src.rows:
        by_date[r.date].append(r)

    processed_rows = []
    for d, d_rows in sorted(by_date.items()):
        # מיון המשמרות באותו יום לפי שעת התחלה
        d_rows.sort(key=lambda x: minutes(x.start))

        last_end_mins = -1
        for r in d_rows:
            start_mins = minutes(r.start)
            end_mins = minutes(r.end)

            # הוספת שינוי אקראי קל (ג'יטר) של עד 5 דקות
            jitter = rng.randint(-5, 5)
            start_mins += jitter
            end_mins += jitter

            if end_mins <= start_mins:
                end_mins = start_mins + 120  # מינימום שעתיים משמרת

            # מניעת חפיפה עם המשמרת הקודמת באותו היום
            if start_mins < last_end_mins:
                start_mins = last_end_mins + 15  # רווח של 15 דקות
                if end_mins <= start_mins:
                    end_mins = start_mins + 120

            new_start = time(start_mins // 60, start_mins % 60)
            new_end = time(end_mins // 60, end_mins % 60)

            break_h = r.break_minutes / 60.0
            calc_total = round((end_mins - start_mins) / 60.0 - break_h, 2)
            if calc_total < 0:
                calc_total = 0.0

            # חלוקה למדרגות שעות (100%, 125%, 150%)
            h100 = min(calc_total, 8.0)
            rem = max(0.0, calc_total - 8.0)
            h125 = min(rem, 2.0)
            h150 = max(0.0, rem - 2.0)

            new_row = AttendanceRowB(
                date=r.date,
                start=new_start,
                end=new_end,
                break_minutes=r.break_minutes,
                total_hours=calc_total,
                hours_100=round(h100, 2),
                hours_125=round(h125, 2),
                hours_150=round(h150, 2),
                workplace=r.workplace,
                shabbat_hours=r.shabbat_hours
            )
            processed_rows.append(new_row)
            last_end_mins = end_mins

    # מיון כללי של כל השורות לפי תאריך ושעה
    processed_rows.sort(key=lambda x: (x.date, x.start))

    total_h = round(sum(r.total_hours for r in processed_rows), 2)
    h100 = round(sum(r.hours_100 for r in processed_rows), 2)
    h125 = round(sum(r.hours_125 for r in processed_rows), 2)
    h150 = round(sum(r.hours_150 for r in processed_rows), 2)
    shabbat = round(sum(r.shabbat_hours for r in processed_rows), 2)

    return ReportB(
        employee_name=src.employee_name,
        period_start=src.period_start,
        period_end=src.period_end,
        rows=processed_rows,
        days=len(processed_rows),
        total_hours=total_h,
        hours_100=h100,
        hours_125=h125,
        hours_150=h150,
        shabbat_150=shabbat,
        bonus=src.bonus,
        travel=src.travel,
        company_name=src.company_name
    )