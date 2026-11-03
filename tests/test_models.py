import sys
from pathlib import Path
from datetime import date, time, timedelta

# הוספת תיקיית השורש ו-src ל-sys.path
root_dir = Path(__file__).resolve().parent.parent
src_dir = root_dir / "src"
for p in [root_dir, src_dir]:
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

try:
    from src.models import AttendanceRow, AttendanceReport
except ImportError:
    from models import AttendanceRow, AttendanceReport


def test_attendance_row_creation():
    """בודק יצירת שורת נוכחות בודדת ווידוא טיפוסי נתונים בהתאם לכלל הברזל."""
    row = AttendanceRow(
        date=date(2022, 10, 2),
        day_of_week="ראשון",
        entry_time=time(8, 0),
        exit_time=time(15, 0),
        break_time=timedelta(minutes=30),
        hours_100=6.5,
        hours_125=0.0,
        hours_150=0.0,
        total_hours=6.5,
        location="גליליון",
        notes="יום רגיל",
    )

    # 1. בדיקת ערכים
    assert row.day_of_week == "ראשון"
    assert row.location == "גליליון"
    assert row.hours_100 == 6.5
    assert row.total_hours == 6.5

    # 2. בדיקת כלל הברזל - שום תאריך או שעה אינם str
    assert isinstance(row.date, date)
    assert not isinstance(row.date, str)

    assert isinstance(row.entry_time, time)
    assert not isinstance(row.entry_time, str)

    assert isinstance(row.exit_time, time)
    assert not isinstance(row.exit_time, str)

    assert isinstance(row.break_time, (timedelta, time))
    assert not isinstance(row.break_time, str)

    # בדיקת טיפוסי שעות
    assert isinstance(row.hours_100, float)
    assert isinstance(row.total_hours, float)
    print("  [V] בדיקת AttendanceRow עברה בהצלחה!")


def test_attendance_report_creation():
    """בודק יצירת דוח נוכחות חודשי מלא עם רשימת שורות וסיכומים."""
    row1 = AttendanceRow(
        date=date(2022, 10, 2),
        day_of_week="ראשון",
        entry_time=time(8, 0),
        exit_time=time(15, 0),
        break_time=timedelta(minutes=30),
        hours_100=6.5,
        total_hours=6.5,
    )
    row2 = AttendanceRow(
        date=date(2022, 10, 8),
        day_of_week="שבת",
        entry_time=time(8, 0),
        exit_time=time(15, 0),
        break_time=timedelta(minutes=30),
        hours_150=6.5,
        shabbat_hours=6.5,
        total_hours=6.5,
    )

    report = AttendanceReport(
        employee_name="ישראל ישראלי",
        employee_id="123456789",
        company_name='נ.ע. הנשר כח אדם בע"מ',
        report_month=date(2022, 10, 1),
        rows=[row1, row2],
        total_hours=13.0,
        total_hours_100=6.5,
        total_hours_150=6.5,
        total_shabbat_hours=6.5,
        total_work_days=2,
        travel_expenses=50.0,
        bonus=100.0,
    )

    # 1. בדיקת שדות
    assert report.employee_name == "ישראל ישראלי"
    assert len(report.rows) == 2
    assert report.total_hours == 13.0
    assert report.travel_expenses == 50.0
    assert report.bonus == 100.0

    # 2. בדיקת כלל הברזל עבור חודש הדוח
    assert isinstance(report.report_month, date)
    assert not isinstance(report.report_month, str)

    print("  [V] בדיקת AttendanceReport עברה בהצלחה!")


def run_all_tests():
    print("=== מתחיל הרצת בדיקות עבור models.py ===")
    test_attendance_row_creation()
    test_attendance_report_creation()
    print("=== כל הבדיקות עברו בהצלחה! מודל הנתונים תקין לחלוטין ===")


if __name__ == "__main__":
    run_all_tests()
