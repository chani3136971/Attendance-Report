import pymupdf

from main import CARD_PATH   # אותו קובץ ש-main.py קורא

print("קובץ:", CARD_PATH)
doc = pymupdf.open(str(CARD_PATH))
print("עמודים:", len(doc))
for i, page in enumerate(doc, 1):
    t = page.get_text()
    print(f"--- עמוד {i}: {len(t)} תווים בשכבת טקסט ---")
    print(t[:400])
