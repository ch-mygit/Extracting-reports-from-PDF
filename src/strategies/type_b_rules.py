import copy
import random
import hashlib
import sys
from pathlib import Path
from datetime import date, time, timedelta
from typing import List, Optional

_src_dir = Path(__file__).resolve().parent.parent
if str(_src_dir) not in sys.path:
    sys.path.insert(0, str(_src_dir))

try:
    from models import AttendanceReport, AttendanceRow
    from strategies.type_a_rules import BaseTransformationStrategy
except ImportError:
    from models.models import AttendanceReport, AttendanceRow
    from type_a_rules import BaseTransformationStrategy


HEBREW_HOLIDAYS_BY_MONTH = {
    1: ["חנוכה", "חופשה"],
    2: ["פורים", "תענית אסתר"],
    3: ["פורים", "שושן פורים"],
    4: ["ערב פסח", "פסח", "חול המועד פסח", "שביעי של פסח"],
    5: ["יום העצמאות", "ל״ג בעומר", "שבועות"],
    6: ["שבועות", "ערב שבועות"],
    7: ["צום י״ז בתמוז"],
    8: ["צום תשעה באב"],
    9: ["ערב ראש השנה", "ראש השנה", "יום כיפור"],
    10: ["ערב סוכות", "סוכות", "חול המועד סוכות", "שמחת תורה", "יום כיפור"],
    11: ["ערב חנוכה", "חנוכה"],
    12: ["חנוכה"],
}
DEFAULT_HOLIDAYS = ["ראש השנה", "ערב ראש השנה", "יום כיפור", "סוכות", "פסח", "פורים", "שבועות", "חנוכה"]


class TypeBTransformationStrategy(BaseTransformationStrategy):
    """
    אסטרטגיית טרנספורמציה ייעודית עבור דוחות מסוג B (כרטיס עובד לחודש).
    כוללת תמיכה בשבתות מוצללות ובשורות חג ריקות עם הערות (פסח, ר"ה, פורים וכו').
    """

    def __init__(self, target_row_count: Optional[int] = None):
        self.target_row_count = target_row_count

    @classmethod
    def _get_holiday_for_month(cls, month: Optional[int], rng: random.Random) -> str:
        if month and month in HEBREW_HOLIDAYS_BY_MONTH:
            return rng.choice(HEBREW_HOLIDAYS_BY_MONTH[month])
        return rng.choice(DEFAULT_HOLIDAYS)

    def _generate_seed(self, report: AttendanceReport) -> int:
        seed_parts = [
            str(report.company_name or "type_b"),
            str(report.employee_name or ""),
            str(report.report_month or ""),
            str(len(report.rows)),
            f"{report.total_hours:.2f}",
        ]
        for r in report.rows[:5]:
            seed_parts.append(f"{r.date}_{r.day_of_week}_{r.entry_time}_{r.total_hours}")

        raw_string = "|".join(seed_parts)
        sha_hash = hashlib.sha256(raw_string.encode("utf-8")).hexdigest()
        return int(sha_hash[:8], 16)

    def transform(self, report: AttendanceReport) -> AttendanceReport:
        if not report.rows:
            return copy.deepcopy(report)

        transformed = copy.deepcopy(report)
        seed_val = self._generate_seed(report)
        rng = random.Random(seed_val)

        # קביעת כמות שורות: אם לא הוגדרה במפורש, נבחרת כמות רנדומלית יציבה
        target_count = self.target_row_count
        if target_count is None:
            n_rows = len(transformed.rows)
            min_r = min(4, n_rows)
            max_r = min(n_rows, 16)
            target_count = rng.randint(min_r, max_r) if min_r < max_r else n_rows

        shabbat_rows = [r for r in transformed.rows if r.day_of_week == "שבת"]
        holiday_rows = [
            r for r in transformed.rows
            if r.day_of_week != "שבת" and r.notes and r.notes.strip() not in ["", "רגיל", "יום עבודה", "יום שישי"]
        ]
        working_rows = [
            r for r in transformed.rows
            if r.day_of_week != "שבת" and (r.total_hours > 0 or r.entry_time) and r not in holiday_rows
        ]
        other_rows = [
            r for r in transformed.rows
            if r not in shabbat_rows and r not in working_rows and r not in holiday_rows
        ]

        selected_rows: List[AttendanceRow] = []

        # 1. שורת שבת מוצללת באפור
        if shabbat_rows:
            selected_rows.append(rng.choice(shabbat_rows))

        # 2. הוספת שורת חג ריקה עם שם החג בהערות (פסח, ר"ה, פורים וכו')
        month_val = transformed.report_month.month if transformed.report_month else None
        holiday_name = self._get_holiday_for_month(month_val, rng)

        if holiday_rows:
            # אם כבר הייתה שורת חג קיימת במקור - בוחרים אותה
            chosen_h = rng.choice(holiday_rows)
            chosen_h.entry_time = None
            chosen_h.exit_time = None
            chosen_h.total_hours = 0.0
            chosen_h.hours_100 = 0.0
            selected_rows.append(chosen_h)
        elif working_rows or other_rows:
            # הוספת שורת חג מתוך הימים הזמינים
            cand_pool = other_rows if other_rows else working_rows
            if cand_pool:
                h_row = rng.choice(cand_pool)
                h_row.entry_time = None
                h_row.exit_time = None
                h_row.total_hours = 0.0
                h_row.hours_100 = 0.0
                h_row.notes = holiday_name
                selected_rows.append(h_row)
                if h_row in working_rows:
                    working_rows.remove(h_row)
                if h_row in other_rows:
                    other_rows.remove(h_row)

        # 3. מילוי שאר השורות בימי עבודה עד הגעה ל-target_count
        needed_work = min(target_count - len(selected_rows), len(working_rows))
        if working_rows and needed_work > 0:
            selected_rows.extend(rng.sample(working_rows, k=needed_work))

        remaining = target_count - len(selected_rows)
        if other_rows and remaining > 0:
            selected_rows.extend(rng.sample(other_rows, k=min(remaining, len(other_rows))))

        selected_rows.sort(key=lambda r: (r.date or date.min))

        new_rows: List[AttendanceRow] = []
        for row in selected_rows:
            self._update_row_times_and_hours(row, rng)
            new_rows.append(row)

        transformed.rows = new_rows

        transformed.total_hours = round(sum(r.total_hours for r in transformed.rows if r.day_of_week != "שבת"), 2)
        transformed.total_hours_100 = transformed.total_hours
        transformed.total_work_days = len([r for r in transformed.rows if r.total_hours > 0 and r.day_of_week != "שבת"])

        hourly_rate = report.hourly_rate if report.hourly_rate and report.hourly_rate > 0 else 30.65
        transformed.hourly_rate = hourly_rate
        transformed.total_payment = round(transformed.total_hours * hourly_rate, 2)

        return transformed

    def _update_row_times_and_hours(self, row: AttendanceRow, rng: random.Random):
        if row.day_of_week == "שבת":
            row.entry_time = None
            row.exit_time = None
            row.total_hours = 0.0
            row.hours_100 = 0.0
            row.notes = ""
            return

        # שורת חג: שורה ריקה שרק מציגה את שם החג בעמודת ההערות
        if row.notes and row.notes.strip() not in ["", "רגיל", "יום עבודה", "יום שישי"]:
            row.entry_time = None
            row.exit_time = None
            row.total_hours = 0.0
            row.hours_100 = 0.0
            return

        entry_hour = rng.choice([8, 8, 8, 9])
        entry_minute = rng.choice([0, 5, 10, 15, 30])
        row.entry_time = time(hour=entry_hour, minute=entry_minute)

        shift_duration_hours = rng.choice([3.0, 3.25, 3.5, 3.75, 4.0])
        duration_minutes = int(shift_duration_hours * 60)

        entry_total_minutes = entry_hour * 60 + entry_minute
        exit_total_minutes = entry_total_minutes + duration_minutes

        exit_hour = exit_total_minutes // 60
        exit_minute = exit_total_minutes % 60
        row.exit_time = time(hour=exit_hour, minute=exit_minute)

        row.total_hours = round(shift_duration_hours, 2)
        row.hours_100 = row.total_hours

        if row.notes in ["רגיל", "יום עבודה"]:
            row.notes = ""


def transform_type_b_report(report: AttendanceReport, target_row_count: Optional[int] = None) -> AttendanceReport:
    strategy = TypeBTransformationStrategy(target_row_count=target_row_count)
    return strategy.transform(report)


def test_type_b_deterministic_behavior():
    test_rows: List[AttendanceRow] = []
    base_date = date(2022, 9, 1)

    for i in range(15):
        curr_date = base_date + timedelta(days=i)
        is_shabbat = (curr_date.weekday() == 5)
        day_str = "שבת" if is_shabbat else "ראשון"
        test_rows.append(
            AttendanceRow(
                date=curr_date,
                day_of_week=day_str,
                entry_time=None if is_shabbat else time(8, 30),
                exit_time=None if is_shabbat else time(12, 0),
                total_hours=0.0 if is_shabbat else 3.5,
                notes="",
            )
        )

    sample_report = AttendanceReport(
        company_name="כרטיס עובד לחודש",
        employee_name="כהן משה",
        report_month=date(2022, 9, 1),
        rows=test_rows,
        total_hours=45.5,
        total_work_days=13,
        hourly_rate=30.65,
    )

    result_1 = transform_type_b_report(sample_report, target_row_count=5)
    result_2 = transform_type_b_report(sample_report, target_row_count=5)

    assert len(result_1.rows) == 5
    assert len(result_2.rows) == 5

    for i, (r1, r2) in enumerate(zip(result_1.rows, result_2.rows), 1):
        assert r1.date == r2.date
        assert r1.day_of_week == r2.day_of_week
        assert r1.entry_time == r2.entry_time
        assert r1.exit_time == r2.exit_time
        assert r1.total_hours == r2.total_hours

        if r1.entry_time and r1.exit_time:
            entry_min = r1.entry_time.hour * 60 + r1.entry_time.minute
            exit_min = r1.exit_time.hour * 60 + r1.exit_time.minute
            assert exit_min > entry_min

    assert result_1.total_hours == result_2.total_hours
    assert result_1.total_payment == result_2.total_payment
    assert result_1.total_work_days == result_2.total_work_days

    print("============================================================")
    print("✅ Unit Test (Type B) עבר בהצלחה מלאה!")
    print(f"  - כמות השורות צומצמה ל-{len(result_1.rows)}")
    print("  - דטרמיניזם מוחלט אומת בין שתי ההרצות")
    print("  - כל שעות היציאה מאוחרות משעות הכניסה (exit > entry)")
    print("============================================================")


def test_type_b_holiday_notes():
    """
    בדיקה ייעודית המוודאת שבסוג B נכללות שורות חג ריקות (ללא שעות כניסה ויציאה)
    עם שם החג בעמודת ההערות (כגון 'ראש השנה', 'פסח', 'פורים').
    """
    test_rows: List[AttendanceRow] = []
    base_date = date(2022, 9, 1)

    for i in range(10):
        curr_date = base_date + timedelta(days=i)
        is_shabbat = (curr_date.weekday() == 5)
        day_str = "שבת" if is_shabbat else "ראשון"
        test_rows.append(
            AttendanceRow(
                date=curr_date,
                day_of_week=day_str,
                entry_time=None if is_shabbat else time(8, 30),
                exit_time=None if is_shabbat else time(12, 0),
                total_hours=0.0 if is_shabbat else 3.5,
                notes="ראש השנה" if i == 6 else "",
            )
        )

    sample_report = AttendanceReport(
        company_name="כרטיס עובד לחודש",
        employee_name="כהן משה",
        report_month=date(2022, 9, 1),
        rows=test_rows,
        total_hours=31.5,
        total_work_days=9,
        hourly_rate=30.65,
    )

    transformed = transform_type_b_report(sample_report, target_row_count=5)
    assert len(transformed.rows) == 5

    # בדיקה שקיימת לפחות שורת חג אחת עם הערה ושעות ריקות
    holiday_rows = [r for r in transformed.rows if r.notes and r.notes not in ["", "רגיל", "יום עבודה", "שבת"]]
    assert len(holiday_rows) >= 1
    for h in holiday_rows:
        assert h.entry_time is None
        assert h.exit_time is None
        assert h.total_hours == 0.0
        assert h.notes in ["ראש השנה", "ערב ראש השנה", "יום כיפור", "סוכות", "פסח", "פורים", "שבועות", "חנוכה"]

    print("============================================================")
    print("✅ Unit Test: שורות חג בסוג B (הערות חג ללא שעות) עברה בהצלחה!")
    print(f"  - נמצאה שורת חג: '{holiday_rows[0].notes}' ביום {holiday_rows[0].day_of_week} ({holiday_rows[0].date})")
    print(f"  - כניסה ויציאה ריקות (None), וסה\"כ שעות: {holiday_rows[0].total_hours}")
    print("============================================================")


def run_unit_tests():
    test_type_b_deterministic_behavior()
    test_type_b_holiday_notes()


if __name__ == "__main__":
    run_unit_tests()
