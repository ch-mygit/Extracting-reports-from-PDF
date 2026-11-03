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


class TypeBTransformationStrategy(BaseTransformationStrategy):
    """
    אסטרטגיית טרנספורמציה ייעודית עבור דוחות מסוג B (כרטיס עובד לחודש).
    """

    def __init__(self, target_row_count: int = 5):
        self.target_row_count = target_row_count

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

        shabbat_rows = [r for r in transformed.rows if r.day_of_week == "שבת"]
        working_rows = [r for r in transformed.rows if r.day_of_week != "שבת" and (r.total_hours > 0 or r.entry_time)]
        other_rows = [r for r in transformed.rows if r not in shabbat_rows and r not in working_rows]

        selected_rows: List[AttendanceRow] = []

        if shabbat_rows:
            selected_rows.append(rng.choice(shabbat_rows))

        needed_work = min(self.target_row_count - len(selected_rows), len(working_rows))
        if working_rows and needed_work > 0:
            selected_rows.extend(rng.sample(working_rows, k=needed_work))

        remaining = self.target_row_count - len(selected_rows)
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


def transform_type_b_report(report: AttendanceReport, target_row_count: int = 5) -> AttendanceReport:
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


run_unit_tests = test_type_b_deterministic_behavior

if __name__ == "__main__":
    test_type_b_deterministic_behavior()
