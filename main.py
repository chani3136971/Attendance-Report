from pathlib import Path
from classifier.classifier import classifier
from models import ReportType
from sampels.ocr_card_a import get_text
from transformer.transform import Conditions
from pipeline_handler import run_pipeline

CARD_PATH = Path(r"E:\פרקטיקות\lesson2\data\outputs\n_r_10_n_NEW.pdf")
OUT_DIR = Path(__file__).parent / "generated"
HOW_MANY = 3
CONDITIONS = Conditions(
    year=2023,
    month=2,
    name="שם לדוגמה",
    work_days=20,
    start_range=(475, 490),
    duration_range=(360, 390),
    rate=None,
)



def main() -> None:
    txt = get_text(CARD_PATH)
    rtype = classifier(txt)
    if rtype not in (ReportType.A, ReportType.B):
        raise SystemExit("סוג הדו\"ח אינו מוכר")
    run_pipeline(rtype, txt, CONDITIONS, OUT_DIR, HOW_MANY)

if __name__ == "__main__":
    main()