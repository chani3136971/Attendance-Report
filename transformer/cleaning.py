import re

BIDI = re.compile(r"[\u200e\u200f\u202a-\u202e\u2066-\u2069]")
ROW = re.compile(
    r"(\d{2}:\d{2})\s+(\d{2}:\d{2})\s+(\d{2}:\d{2})\s+"
    r"(\d+\.\d+)\s+(\d+\.\d+)\s+(\d+\.\d+)\s+(\d+\.\d+)\s+(\d+\.\d+)"
)
DATE = re.compile(r"\d{2}/\d{2}/\d{4}")


def clean(txt: str) -> str:
    txt = BIDI.sub("", txt)
    return txt.replace("\t", " ")


def to_min(hhmm: str) -> int:
    h, m = hhmm.split(":")
    return int(h) * 60 + int(m)


def parse_rows(txt: str) -> list[dict]:
    rows = []
    for line in clean(txt).splitlines():
        m = ROW.search(line)
        if not m:
            continue
        d = DATE.search(line)
        start, end, brk, *nums = m.groups()
        total, h100, h125, h150, shabbat = (round(float(x), 2) for x in nums)
        rows.append({
            "date": d.group() if d else None,   # עלול להיות חסר
            "start": start, "end": end, "break": brk,
            "total": total, "100": h100, "125": h125,
            "150": h150, "shabbat": shabbat,
        })
    return rows
