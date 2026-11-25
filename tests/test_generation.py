import sys
from pathlib import Path
from datetime import date

# הגדרת נתיבי ייבוא
root_dir = Path(__file__).resolve().parent.parent
src_dir = root_dir / "src"
for p in [root_dir, src_dir]:
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from src.generation.generator import SyntheticReportGenerator
from src.generation.pdf_builder import PDFBuilder
from src.models import AttendanceReport


def test_synthetic_type_a_generation():
    """בודק ייצור דוח סינתטי מסוג A, כולל חישובי שעות והפרדת שעות שבת."""
    gen = SyntheticReportGenerator()
    report = gen.generate_report(
        report_type="A",
        employee_name="דנה לוי",
        employee_id="987654321",
        year=2023,
        month=1,
    )

    assert isinstance(report, AttendanceReport)
    assert report.employee_name == "דנה לוי"
    assert len(report.rows) > 0
    assert report.total_hours > 0

    # וידוא הפרדה: סה"כ שעות שווה לסכום כל הקטגוריות
    expected_sum = round(
        report.total_hours_100
        + report.total_hours_125
        + report.total_hours_150
        + (report.total_shabbat_hours or 0.0),
        2,
    )
    assert report.total_hours == expected_sum

    # וידוא שורות בודדות
    for r in report.rows:
        if r.day_of_week == "שבת" and r.total_hours > 0:
            assert r.shabbat_hours == r.total_hours
            assert r.hours_150 == 0.0
            assert r.hours_100 == 0.0


def test_synthetic_type_b_generation_and_holidays():
    """בודק ייצור דוח סינתטי מסוג B עבור חודש ניסן (פסח) ומוודא הכללת שורות חג ריקות."""
    gen = SyntheticReportGenerator()
    # חודש 4 (אפריל - פסח)
    report = gen.generate_report(
        report_type="B",
        employee_name="אברהם כהן",
        employee_id="112233445",
        year=2023,
        month=4,
    )

    assert isinstance(report, AttendanceReport)
    assert len(report.rows) > 0

    holiday_rows = [r for r in report.rows if r.notes and "פסח" in r.notes]
    assert len(holiday_rows) >= 1

    for h in holiday_rows:
        # שורות חג חייבות להיות ריקות משעות
        assert h.entry_time is None
        assert h.exit_time is None
        assert h.total_hours == 0.0
        assert h.hours_100 == 0.0

    # ימי חג אינם נספרים כימי עבודה
    assert report.total_work_days == len([r for r in report.rows if r.total_hours > 0 and r.day_of_week != "שבת"])


def test_pdf_builder_render_and_build(tmp_path):
    """בודק הפקת HTML ו-PDF תקינים בעזרת PDFBuilder."""
    gen = SyntheticReportGenerator()
    report = gen.generate_report(report_type="B", month=9, year=2023)

    builder = PDFBuilder(template_name="type_b_report.html")
    html_content = builder.render_html(report)

    assert "<html" in html_content
    assert "כרטיס עובד לחודש" in html_content

    pdf_out = tmp_path / "test_output.pdf"
    result_path = builder.build(report, pdf_out)

    assert result_path.exists()
    assert result_path.stat().st_size > 0
    # קובץ ה-HTML הנלווה נוצר אף הוא
    html_out = result_path.with_suffix(".html")
    assert html_out.exists()
