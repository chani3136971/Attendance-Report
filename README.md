# Attendance Report Pipeline 🗂️

מערכת Python לעיבוד אוטומטי של דוחות נוכחות — מ-PDF גולמי ועד ליצירת כרטיסי נוכחות חדשים.

---

## מה המערכת עושה?

קוראת קובץ PDF של כרטיס נוכחות, מזהה את סוגו, מפרסרת את הנתונים, ומייצרת מספר וריאציות חדשות כקובצי PDF — כולל חישוב שעות, מדרגות שכר ובקרת תקינות.

---

## זרימת העבודה (Pipeline)

```
PDF קלט
   │
   ▼
OCR / קריאת טקסט          ← ocr/ocr_reader.py
   │
   ▼
זיהוי סוג הדו"ח            ← classifier/classifier.py
(סוג A / סוג B)
   │
   ▼
פרסור לאובייקט נתונים      ← parser/parsers.py + models.py
   │
   ▼
יצירת וריאציות             ← transformer/transform.py
(הגרלה, חישוב שעות, וולידציה)
   │
   ▼
הפקת PDF                   ← genorater/generate.py
   │
   ▼
generated/card_*.pdf  ✅
```

---

## מבנה הפרויקט

```
PythonProject/
├── main.py                  # נקודת כניסה — מריץ את כל הצינור
├── models.py                # מבני נתונים (dataclasses) ולוגיקת וולידציה
├── pipeline_handler.py      # מתזמר את שלבי הצינור לפי סוג הדו"ח
│
├── classifier/
│   └── classifier.py        # מזהה את סוג הדו"ח מתוך הטקסט
│
├── ocr/
│   └── ocr_reader.py        # קריאת טקסט מ-PDF (שכבת טקסט / OCR)
│
├── parser/
│   ├── parsers.py           # פרסרים לסוג A ו-B + מילון PARSERS
│   ├── parsing.py           # פונקציות עזר לפרסור (זמן, תאריך)
│   └── source_a.py          # נתוני אמת קבועים לכרטיס A (לצורך השוואה)
│
├── transformer/
│   ├── transform.py         # יצירת וריאציות + חישוב מדרגות שעות
│   └── calc.py              # חישובי עזר (שעות, חודשים)
│
├── genorater/
│   └── generate.py          # הפקת PDF באמצעות ReportLab
│
├── sampels/
│   └── ocr_card_a.py        # סקריפט עזר לטעינת טקסט מ-PDF
│
├── generated/               # כאן נשמרים קובצי ה-PDF שנוצרו
└── inputs/                  # כאן מניחים את קובצי ה-PDF לעיבוד
```

---

## התקנה

```bash
# שכפול הפרויקט
git clone <repo-url>
cd PythonProject

# יצירת סביבה וירטואלית
python -m venv .venv
.venv\Scripts\activate

# התקנת תלויות
pip install pymupdf pillow pytesseract python-bidi reportlab
```

> **שימו לב:** `pytesseract` מצריך התקנת [Tesseract OCR](https://github.com/UB-Mannheim/tesseract/wiki) על המחשב בנפרד.

---

## הפעלה

1. העתיקו את קובץ ה-PDF לתיקיית `inputs/`
2. עדכנו את `CARD_PATH` ב-`main.py` לשם הקובץ:

```python
CARD_PATH = Path(r"C:\...\inputs\שם_הקובץ.pdf")
```

3. כוונו את הפרמטרים לפי הצורך:

```python
HOW_MANY = 3          # כמה וריאציות לייצר
CONDITIONS = Conditions(
    year=2023,
    month=2,
    work_days=20,
    ...
)
```

4. הריצו:

```bash
python main.py
```

הקבצים שנוצרו יופיעו בתיקיית `generated/`.

---

## הגדרות מתקדמות

| משתנה | מיקום | תיאור |
|-------|--------|--------|
| `USE_TRUTH` | `pipeline_handler.py` | `True` = השתמש בנתוני אמת קבועים במקום OCR |
| `CARD_PATH` | `main.py` | נתיב קובץ ה-PDF לעיבוד |
| `HOW_MANY` | `main.py` | מספר הוריאציות לייצר |
| `CONDITIONS` | `main.py` | פרמטרים לוריאציות (שנה, חודש, ימי עבודה וכו') |

---

## סוגי דוחות נתמכים

| סוג | תיאור |
|-----|--------|
| **A** | כרטיס נוכחות עם שורות כניסה/יציאה ושכר שעתי |
| **B** | דוח נוכחות עם סה"כ ימים ושעות |
