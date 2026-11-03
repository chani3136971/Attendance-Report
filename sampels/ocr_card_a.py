from pathlib import Path
from PIL import Image

from classifier.classifier import classifier, scores
from ocr.ocr_reader import pdf_page_to_image, preprocess, read, pdf_text

# שני לשם הקובץ האמיתי
CARD_PATH = Path(r"E:\פרקטיקות\lesson2\data\outputs\n_r_10_n_NEW.pdf")
OUT_PATH = Path("ocr_card_a.txt")
#עוזר להדפסת פרטים על הקובץ שהתקבל
def get_text1(path: Path) -> tuple[str, str]:
    if path.suffix.lower() == ".pdf":
        txt = pdf_text(str(path))
        if txt:
            return txt, "שכבת טקסט"
        return read(preprocess(pdf_page_to_image(str(path), page=1))), "OCR"
    return read(preprocess(Image.open(path))), "OCR"

#מחזיר את הקובץ pdf בטקסט
def get_text(path: Path) -> str:
    if path.suffix.lower() == ".pdf":
        return pdf_text(str(path)) or read(preprocess(pdf_page_to_image(str(path), page=1)))
    return read(preprocess(Image.open(path)))  # type: ignore

txt, source = get_text1(CARD_PATH)
OUT_PATH.write_text(txt, encoding="utf-8")

print("מקור הטקסט:", source)
print("מספר תווים:", len(txt))
print("סיווג:", classifier(txt).value, "| ניקוד (A, B):", scores(txt))
print("-" * 40)
print(txt)