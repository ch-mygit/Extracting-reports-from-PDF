import sys
from pathlib import Path
import pytest
from datetime import date, time

# הגדרת נתיבי ייבוא
root_dir = Path(__file__).resolve().parent.parent
src_dir = root_dir / "src"
for p in [root_dir, src_dir]:
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from src.ocr.classifier import ReportType, classify_report
from src.parsers import TypeAParser, TypeBParser
from src.strategies import TypeATransformationStrategy, TypeBTransformationStrategy
from src.models import AttendanceReport, AttendanceRow
from src.utils import TerminalUI
from main import ReportPipelineFactory


def test_pipeline_factory_type_a():
    """בודק ייצור רכיבים עבור דוח מסוג A."""
    comps = ReportPipelineFactory.create_pipeline(ReportType.TYPE_A, target_row_count=8)
    assert isinstance(comps.parser, TypeAParser)
    assert isinstance(comps.strategy, TypeATransformationStrategy)
    assert comps.strategy.target_row_count == 8
    assert comps.template_name == "type_a_report.html"
    assert comps.report_type == ReportType.TYPE_A


def test_pipeline_factory_type_b():
    """בודק ייצור רכיבים עבור דוח מסוג B."""
    comps = ReportPipelineFactory.create_pipeline(ReportType.TYPE_B, target_row_count=6)
    assert isinstance(comps.parser, TypeBParser)
    assert isinstance(comps.strategy, TypeBTransformationStrategy)
    assert comps.strategy.target_row_count == 6
    assert comps.template_name == "type_b_report.html"
    assert comps.report_type == ReportType.TYPE_B


def test_pipeline_factory_unsupported_type():
    """בודק טיפול בסוג דוח שאינו נתמך."""
    with pytest.raises(ValueError) as excinfo:
        ReportPipelineFactory.create_pipeline(ReportType.UNKNOWN)
    assert "אינו נתמך" in str(excinfo.value)


def test_report_recalculate_totals_type_a():
    """בודק את מתודת recalculate_totals עבור דוח סוג A."""
    row1 = AttendanceRow(
        date=date(2023, 1, 1),
        day_of_week="ראשון",
        total_hours=10.0,
        hours_100=8.0,
        hours_125=2.0,
        hours_150=0.0,
        shabbat_hours=0.0,
    )
    row2 = AttendanceRow(
        date=date(2023, 1, 7),
        day_of_week="שבת",
        total_hours=6.0,
        hours_100=0.0,
        hours_125=0.0,
        hours_150=0.0,
        shabbat_hours=6.0,
    )
    report = AttendanceReport(rows=[row1, row2])
    report.recalculate_totals(is_type_b=False)

    assert report.total_hours == 16.0
    assert report.total_hours_100 == 8.0
    assert report.total_hours_125 == 2.0
    assert report.total_hours_150 == 0.0
    assert report.total_shabbat_hours == 6.0
    assert report.total_work_days == 2


def test_report_recalculate_totals_type_b():
    """בודק את מתודת recalculate_totals עבור דוח סוג B כולל אי-ספירת שבת וחג."""
    row_work = AttendanceRow(
        date=date(2023, 1, 1),
        day_of_week="ראשון",
        total_hours=8.0,
    )
    row_holiday = AttendanceRow(
        date=date(2023, 1, 2),
        day_of_week="שני",
        total_hours=0.0,
        notes="ראש השנה",
    )
    row_shabbat = AttendanceRow(
        date=date(2023, 1, 7),
        day_of_week="שבת",
        total_hours=0.0,
    )
    report = AttendanceReport(rows=[row_work, row_holiday, row_shabbat], hourly_rate=30.0)
    report.recalculate_totals(is_type_b=True)

    assert report.total_hours == 8.0
    assert report.total_work_days == 1
    assert report.total_payment == 240.0


def test_terminal_ui_renders_without_errors():
    """בודק שרכיבי ה-UI הטרמינלי עובדים ללא שגיאות."""
    TerminalUI.banner("בדיקת טרמינל", "תת כותרת לבדיקה")
    TerminalUI.step(1, 1, "שלב בדיקה")
    TerminalUI.info("מפתח", "ערך")
    TerminalUI.success("הצלחה בבדיקה")
    TerminalUI.warning("אזהרה בבדיקה")
    TerminalUI.summary_table("טבלה", [("שורה 1", "ערך 1")])
    TerminalUI.comparison_table("השוואה", ("עמודה 1", "עמודה 2", "עמודה 3"), [("A", "B", "C")])
