import re

from models import ReportType

BIDI = re.compile(r"[\u200e\u200f\u202a-\u202e\u2066-\u2069]")
TIME = r"\d{1,2}:\d{2}"
SP = r"[ \t]+"      # רווח באותה שורה בלבד, כדי לא לחבר שורות שונות

# B: שלוש שעות ברצף (כניסה, יציאה, הפסקה) ואחריהן מספר עשרוני
ROW_B = re.compile(rf"{TIME}{SP}{TIME}{SP}{TIME}{SP}\d+\.\d+")
# A: שתי שעות עם מספר עשרוני צמוד (מכל צד, בגלל כיוון הכתיבה)
ROW_A = re.compile(rf"{TIME}{SP}{TIME}{SP}\d+\.\d+|\d+\.\d+{SP}{TIME}{SP}{TIME}")

B_WORDS = [r"Type\s*B", r"Attendance\s*Report", r"LOCATION", r"BREAK",
           r"125\s*%", r"150\s*%", r"נסיעות", r"בונוס", r"כח\s*אדם", r"הנשר"]
A_WORDS = [r"כרטיס\s*עובד", r"מחיר\s*לשעה", r"הערות", r"לתשלום", r"ימי\s*עבודה"]


def scores(txt: str) -> tuple[int, int]:
    """מחזיר (ניקוד A, ניקוד B). מבנה השורות שווה יותר ממילה בודדת."""
    t = BIDI.sub("", txt)
    has_b_rows = bool(ROW_B.search(t))
    rest = ROW_B.sub(" ", t)            # שורות B מכילות גם תבנית של שתי שעות, מסירים אותן קודם

    b = (3 if has_b_rows else 0) + sum(bool(re.search(w, t, re.I)) for w in B_WORDS)
    a = (3 if ROW_A.search(rest) else 0) + sum(bool(re.search(w, t)) for w in A_WORDS)
    return a, b


def classifier(txt: str) -> ReportType:
    a, b = scores(txt)
    if b > a:
        return ReportType.B
    if a > b:
        return ReportType.A
    return ReportType.UNKNOWN