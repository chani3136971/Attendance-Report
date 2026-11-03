import io
import pymupdf
import pytesseract
from PIL import Image, ImageOps
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

def pdf_page_to_image(pdf_path: str, page: int = 1, dpi: int = 300) -> Image.Image:
    """ממיר עמוד בודד (מספור מ-1) מה-PDF לתמונה."""
    doc = pymupdf.open(pdf_path)  # במקום: fitz.open(pdf_path)
    pix = doc[page - 1].get_pixmap(dpi=dpi)
    img = Image.open(io.BytesIO(pix.tobytes("png")))
    doc.close()
    return img


def preprocess(img: Image.Image) -> Image.Image:
    """גווני אפור + ניגודיות."""
    img = img.convert("L")
    return ImageOps.autocontrast(img)


def read(img: Image.Image) -> str:
    """מריץ Tesseract על התמונה ומחזיר טקסט."""
    return pytesseract.image_to_string(img, lang="heb+eng", config="--oem 1 --psm 6")

def pdf_text(pdf_path: str, min_chars: int = 200) -> str:
    """שכבת הטקסט של ה-PDF. מחזיר ריק אם ה-PDF סרוק."""
    doc = pymupdf.open(pdf_path)
    text = "\n".join(page.get_text() for page in doc)
    doc.close()
    return text if len(text.strip()) >= min_chars else ""