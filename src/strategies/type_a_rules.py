import copy
import random
import hashlib
import sys
from pathlib import Path
from abc import ABC, abstractmethod
from datetime import date, time, timedelta
from typing import List, Optional

_src_dir = Path(__file__).resolve().parent.parent
if str(_src_dir) not in sys.path:
    sys.path.insert(0, str(_src_dir))

try:
    from models import AttendanceReport, AttendanceRow
except ImportError:
    from models.models import AttendanceReport, AttendanceRow


class BaseTransformationStrategy(ABC):
    """
    ממשק מופשט לתבנית Strategy עבור טרנספורמציות ושינויים בדוחות נוכחות.
    """

    @abstractmethod
    def transform(self, report: AttendanceReport) -> AttendanceReport:
        """מבצעת שינויים דטרמיניסטיים בדוח ומחזירה דוח מעודכן."""
        pass


class TypeATransformationStrategy(BaseTransformationStrategy):
    """
    אסטרטגיית טרנספורמציה ייעודית עבור דוחות מסוג A.
    
    עקרונות המימוש:
    1. דטרמיניזם מלא: אתחול random.seed על בסיס נתוני הדוח המקורי (SHA-256 יציב).
    2. צמצום כמות השורות לגודל יעד (ברירת מחדל: 5 שורות).
    3. יצירת זמני כניסה ויציאה חדשים עם ערובה לוגית: exit_time > entry_time.
    4. חישוב מתמטי מדויק מאפס של שעות בסיס (100%), שעות נוספות (125%, 150%), שבת וסיכומים חודשיים.
    """

    def __init__(self, target_row_count: int = 5):
        self.target_row_count = target_row_count

    def _generate_seed(self, report: AttendanceReport) -> int:
        """
        מייצרת seed שלם ויציב מנתוני הדוח המקורי באמצעות SHA-256.
        מבטיח תוצאה זהה לחלוטין בכל הרצה מחדש על אותו קובץ/דוח.
        """
        seed_parts = [
            str(report.company_name or ""),
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

        shabbat_indices = [i for i, r in enumerate(transformed.rows) if r.day_of_week == "שבת" or (r.shabbat_hours and r.shabbat_hours > 0)]
        weekday_indices = [i for i, r in enumerate(transformed.rows) if i not in shabbat_indices]

        chosen = []
        if shabbat_indices:
            chosen.append(rng.choice(shabbat_indices))

        needed = min(self.target_row_count, len(transformed.rows)) - len(chosen)
        if weekday_indices and needed > 0:
            chosen.extend(rng.sample(weekday_indices, k=min(needed, len(weekday_indices))))

        chosen_indices = sorted(chosen)
        selected_rows = [transformed.rows[i] for i in chosen_indices]

        new_rows: List[AttendanceRow] = []
        for row in selected_rows:
            self._update_row_times_and_hours(row, rng)
            new_rows.append(row)

        transformed.rows = new_rows

        transformed.total_hours = round(sum(r.total_hours for r in transformed.rows), 2)
        transformed.total_hours_100 = round(sum(r.hours_100 for r in transformed.rows), 2)
        transformed.total_hours_125 = round(sum(r.hours_125 for r in transformed.rows), 2)
        transformed.total_hours_150 = round(sum(r.hours_150 for r in transformed.rows), 2)
        transformed.total_shabbat_hours = round(sum(r.shabbat_hours or 0.0 for r in transformed.rows), 2)
        transformed.total_work_days = len(transformed.rows)

        return transformed

    def _update_row_times_and_hours(self, row: AttendanceRow, rng: random.Random):
        """
        משנה את שעות הכניסה והיציאה של שורה בודדת ומחשבת את כל עמודות השעות מאפס.
        """
        entry_hour = rng.choice([7, 8, 9])
        entry_minute = rng.choice([0, 15, 30, 45])
        if entry_hour == 7 and entry_minute < 30:
            entry_minute = 30
        row.entry_time = time(hour=entry_hour, minute=entry_minute)

        shift_duration_hours = rng.choice([6.5, 7.0, 8.5, 9.0, 9.5, 10.5])
        duration_minutes = int(shift_duration_hours * 60)

        entry_total_minutes = entry_hour * 60 + entry_minute
        exit_total_minutes = entry_total_minutes + duration_minutes

        exit_hour = exit_total_minutes // 60
        exit_minute = exit_total_minutes % 60
        row.exit_time = time(hour=exit_hour, minute=exit_minute)

        if shift_duration_hours >= 6.0:
            row.break_time = timedelta(minutes=30)
            break_hours = 0.5
        else:
            row.break_time = timedelta(minutes=0)
            break_hours = 0.0

        net_hours = round(shift_duration_hours - break_hours, 2)
        row.total_hours = net_hours

        if row.day_of_week == "שבת":
            row.hours_100 = 0.0
            row.hours_125 = 0.0
            row.hours_150 = 0.0
            row.shabbat_hours = net_hours
        else:
            row.shabbat_hours = 0.0
            if net_hours <= 8.0:
                row.hours_100 = net_hours
                row.hours_125 = 0.0
                row.hours_150 = 0.0
            elif net_hours <= 10.0:
                row.hours_100 = 8.0
                row.hours_125 = round(net_hours - 8.0, 2)
                row.hours_150 = 0.0
            else:
                row.hours_100 = 8.0
                row.hours_125 = 2.0
                row.hours_150 = round(net_hours - 10.0, 2)


def transform_type_a_report(report: AttendanceReport, target_row_count: int = 5) -> AttendanceReport:
    strategy = TypeATransformationStrategy(target_row_count=target_row_count)
    return strategy.transform(report)


def test_deterministic_behavior():
    test_rows: List[AttendanceRow] = []
    base_date = date(2022, 10, 1)

    for i in range(20):
        curr_date = base_date + timedelta(days=i)
        is_shabbat = (i % 7 == 6)
        day_str = "שבת" if is_shabbat else "ראשון"
        test_rows.append(
            AttendanceRow(
                date=curr_date,
                day_of_week=day_str,
                entry_time=time(8, 0),
                exit_time=time(15, 0),
                break_time=timedelta(minutes=30),
                hours_100=0.0 if is_shabbat else 6.5,
                hours_150=6.5 if is_shabbat else 0.0,
                shabbat_hours=6.5 if is_shabbat else 0.0,
                total_hours=6.5,
                location="גליליון",
            )
        )

    sample_report = AttendanceReport(
        company_name='נ.ע. הנשר כח אדם בע"מ',
        report_month=date(2022, 10, 1),
        rows=test_rows,
        total_hours=130.0,
        total_hours_100=110.5,
        total_shabbat_hours=19.5,
        total_work_days=20,
    )

    result_1 = transform_type_a_report(sample_report, target_row_count=5)
    result_2 = transform_type_a_report(sample_report, target_row_count=5)

    assert len(result_1.rows) == 5
    assert len(result_2.rows) == 5

    for i, (r1, r2) in enumerate(zip(result_1.rows, result_2.rows), 1):
        assert r1.date == r2.date
        assert r1.entry_time == r2.entry_time
        assert r1.exit_time == r2.exit_time
        assert r1.total_hours == r2.total_hours
        entry_minutes = r1.entry_time.hour * 60 + r1.entry_time.minute
        exit_minutes = r1.exit_time.hour * 60 + r1.exit_time.minute
        assert exit_minutes > entry_minutes

    assert result_1.total_hours == result_2.total_hours
    assert result_1.total_work_days == 5

    print("============================================================")
    print("✅ Unit Test (Type A) עבר בהצלחה מלאה!")
    print(f"  - כמות השורות צומצמה מ-20 ל-{len(result_1.rows)}")
    print("  - דטרמיניזם מוחלט אומת בין שתי ההרצות")
    print("  - שעות היציאה מאוחרות משעות הכניסה (exit > entry)")
    print("============================================================")


run_unit_tests = test_deterministic_behavior

if __name__ == "__main__":
    test_deterministic_behavior()
