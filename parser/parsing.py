from datetime import date, time


def parse_time(s: str) -> time:           # "8:30" או "08:05"
    h, m = s.split(":")
    return time(int(h), int(m))


def parse_date(s: str) -> date:           # "04/01/2023" או "1/9/22"
    d, m, y = (int(x) for x in s.split("/"))
    return date(y + 2000 if y < 100 else y, m, d)


def fmt_time_a(t: time) -> str:           # 8:30
    return f"{t.hour}:{t.minute:02d}"


def fmt_time_b(t: time) -> str:           # 08:05
    return f"{t.hour:02d}:{t.minute:02d}"


def fmt_date_a(d: date) -> str:           # 1/9/22
    return f"{d.day}/{d.month}/{d.year % 100:02d}"


def fmt_date_b(d: date) -> str:           # 04/01/2023
    return f"{d.day:02d}/{d.month:02d}/{d.year}"