# test_pipeline.py
import pytest
from classifier import classifier, scores
from models import ReportType
from parsers import PARSERS


def test_classifier_type_b():
    # בדיקה לדוגמה לזיהוי טקסט של סוג B
    sample_text = "Attendance Report - Type B"
    rtype = classifier(sample_text)
    assert rtype == ReportType.B

    # בדיקת ניקוד (scores מחזירה טאפל של ניקוד A ו-B)
    _, score_b = scores(sample_text)
    assert score_b > 0


def test_parsers_registration():
    # וידוא שכל סוגי הדוחות הנתמכים רשומים במילון הפרסרים
    assert ReportType.A in PARSERS
    assert ReportType.B in PARSERS


def test_parser_parsing_structure():
    # בדיקה בסיסית שהפרסר של סוג B מחזיר אובייקט עם השדות הנדרשים
    parser = PARSERS[ReportType.B]
    dummy_text = "Attendance Report - Type B\nTotal Days: 12\nTotal Hours: 33.05"

    # הרצת הפרסור על טקסט דמה או טקסט אמיתי
    report = parser.parse(dummy_text)
    assert hasattr(report, "rows")
    assert hasattr(report, "total_hours")
    assert report.total_hours == 33.05
    assert report.days == 12