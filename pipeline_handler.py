from genorater.generate import generate_pdf, generate_pdf_b
from models import ReportType
from parser.parsers import PARSERS
from parser.source_a import truth_card_a
from transformer.transform import make_variation, make_variation_b


def run_pipeline(rtype, txt, CONDITIONS, OUT_DIR, HOW_MANY):
    if rtype == ReportType.A:
        truth = truth_card_a()
        if USE_TRUTH:
            src = truth
        else:
            src = PARSERS[rtype].parse(txt)
            ok = sum(1 for a, b in zip(src.rows, truth.rows)
                     if (a.start, a.end) == (b.start, b.end))
            print(f"דיוק ה-OCR: {ok}/{len(truth.rows)} שורות זהות לאמת")

        print("מקור (סוג A):", src.work_days, "ימים |", src.total_hours, "שעות |",
              src.hourly_rate, "לשעה |", src.total_pay, "לתשלום")
        print("בעיות במקור:", src.validate(check_min_day=False) or "אין")

        # שלבים 2 ו-3: הגרלה ויצירה עבור סוג A
        for seed in range(1, HOW_MANY + 1):
            new = make_variation(src, seed, CONDITIONS)
            problems = new.validate()
            if problems:
                print(f"seed {seed}: לא נוצר, בעיות:", problems)
                continue
            out = generate_pdf(new, OUT_DIR / f"card_a_{CONDITIONS.year}_{CONDITIONS.month:02d}_seed{seed}.pdf")
            print(f"seed {seed}: {new.work_days} ימים, {new.total_hours} שעות, "
                  f"{new.total_pay} לתשלום -> {out.name}")

    elif rtype == ReportType.B:
        parser = PARSERS[rtype]
        src = parser.parse(txt)
        print(f"מקור (סוג B): {src.days} ימים | {src.total_hours} שעות")

        for seed in range(1, HOW_MANY + 1):
            new = make_variation_b(src, seed, CONDITIONS)
            problems = new.validate()
            if problems:
                print(f"seed {seed}: לא נוצר, בעיות:", problems)
                continue
            out = generate_pdf_b(new, OUT_DIR / f"card_b_seed{seed}.pdf")
            print(f"seed {seed}: {new.days} ימים, {new.total_hours} שעות -> {out.name}")
    else:
        raise SystemExit("סוג הדו\"ח אינו מוכר או לא זוהה")
