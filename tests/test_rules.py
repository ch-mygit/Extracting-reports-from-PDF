import sys
from pathlib import Path

# הוספת נתיבי המערכת
root_dir = Path(__file__).resolve().parent.parent
src_dir = root_dir / "src"
for p in [root_dir, src_dir]:
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

try:
    from src.strategies.type_a_rules import (
        test_deterministic_behavior as run_type_a_det,
        test_separation_of_150_and_shabbat as run_type_a_sep,
    )
except (ImportError, AttributeError):
    from strategies.type_a_rules import (
        test_deterministic_behavior as run_type_a_det,
        test_separation_of_150_and_shabbat as run_type_a_sep,
    )

try:
    from src.strategies.type_b_rules import (
        test_type_b_deterministic_behavior as run_type_b_det,
        test_type_b_holiday_notes as run_type_b_hol,
    )
except (ImportError, AttributeError):
    from strategies.type_b_rules import (
        test_type_b_deterministic_behavior as run_type_b_det,
        test_type_b_holiday_notes as run_type_b_hol,
    )


def test_type_a_transformation():
    """בדיקת דטרמיניזם וצמצום שורות בסוג A."""
    run_type_a_det()


def test_type_a_150_shabbat_separation():
    """בדיקת הפרדה מוחלטת בין שעות 150% לשעות שבת (3 + 3 = 6)."""
    run_type_a_sep()


def test_type_b_transformation():
    """בדיקת דטרמיניזם וצמצום שורות בסוג B."""
    run_type_b_det()


def test_type_b_holiday_notes():
    """בדיקת הכללת שורות חג ריקות עם שמות חגים בסוג B."""
    run_type_b_hol()


def run_all():
    print("=== בדיקות יחידה: כללי שינוי סוג A ===")
    test_type_a_transformation()
    test_type_a_150_shabbat_separation()
    print("\n=== בדיקות יחידה: כללי שינוי סוג B ===")
    test_type_b_transformation()
    test_type_b_holiday_notes()
    print("\n[V] כל בדיקות החוקים והטרנספורמציות עברו בהצלחה!")


if __name__ == "__main__":
    run_all()
