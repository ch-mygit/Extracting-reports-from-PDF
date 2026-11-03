import sys
from pathlib import Path

# הוספת נתיבי המערכת
root_dir = Path(__file__).resolve().parent.parent
src_dir = root_dir / "src"
for p in [root_dir, src_dir]:
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

try:
    from src.strategies.type_a_rules import test_deterministic_behavior as run_type_a_tests
except (ImportError, AttributeError):
    try:
        from src.strategies.type_a_rules import run_unit_tests as run_type_a_tests
    except (ImportError, AttributeError):
        from strategies.type_a_rules import test_deterministic_behavior as run_type_a_tests

try:
    from src.strategies.type_b_rules import test_type_b_deterministic_behavior as run_type_b_tests
except (ImportError, AttributeError):
    try:
        from src.strategies.type_b_rules import run_unit_tests as run_type_b_tests
    except (ImportError, AttributeError):
        from strategies.type_b_rules import test_type_b_deterministic_behavior as run_type_b_tests


def run_all():
    print("=== בדיקות יחידה: כללי שינוי סוג A ===")
    run_type_a_tests()
    print("\n=== בדיקות יחידה: כללי שינוי סוג B ===")
    run_type_b_tests()
    print("\n[V] כל בדיקות החוקים והטרנספורמציות עברו בהצלחה!")


if __name__ == "__main__":
    run_all()
