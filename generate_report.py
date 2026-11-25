import sys
import argparse
from pathlib import Path

# הוספת נתיבי המערכת
root_dir = Path(__file__).resolve().parent
src_dir = root_dir / "src"
for p in [root_dir, src_dir]:
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from src.generation.generator import SyntheticReportGenerator
from src.utils import TerminalUI


def main():
    parser = argparse.ArgumentParser(
        description="מחולל דוחות נוכחות חדשים לחלוטין (מאפס) בפורמט A או פורמט B ללא צורך בסריקה או OCR"
    )
    parser.add_argument(
        "--type",
        "-t",
        choices=["A", "B", "a", "b"],
        default="A",
        help="פורמט הדוח המבוקש (A או B). ברירת מחדל: A",
    )
    parser.add_argument(
        "--output",
        "-o",
        default=None,
        help="נתיב לקובץ ה-PDF שייווצר (ברירת מחדל: data/output/new_report_<type>.pdf)",
    )
    parser.add_argument(
        "--name",
        "-n",
        default="ישראל ישראלי",
        help="שם העובד (ברירת מחדל: ישראל ישראלי)",
    )
    parser.add_argument(
        "--id",
        default="123456789",
        help="מזהה/תעודת זהות של העובד",
    )
    parser.add_argument(
        "--company",
        "-c",
        default=None,
        help="שם החברה/המעסיק (ברירת מחדל: שם תקני לפי הפורמט)",
    )
    parser.add_argument(
        "--year",
        "-y",
        type=int,
        default=2023,
        help="שנת הדוח (למשל: 2023)",
    )
    parser.add_argument(
        "--month",
        "-m",
        type=int,
        default=1,
        help="חודש הדוח (1 עד 12, למשל: 1)",
    )
    parser.add_argument(
        "--days",
        type=int,
        default=None,
        help="הגבלת כמות ימי עבודה מפורשת (אופציונלי)",
    )
    parser.add_argument(
        "--rate",
        type=float,
        default=35.0,
        help="תעריף לשעה (רלוונטי במיוחד לפורמט B, ברירת מחדל: 35.0 ש\"ח)",
    )

    args = parser.parse_args()

    rep_type = args.type.upper()
    if not args.output:
        out_dir = root_dir / "data" / "output"
        out_dir.mkdir(parents=True, exist_ok=True)
        output_file = out_dir / f"new_synthetic_report_{rep_type}.pdf"
    else:
        output_file = Path(args.output)
        output_file.parent.mkdir(parents=True, exist_ok=True)

    TerminalUI.banner(
        title=f"מחולל דוחות נוכחות חדשים: פורמט {rep_type}",
        subtitle=f"עובד: {args.name} ({args.id}) | חודש: {args.month:02d}/{args.year}",
    )

    generator = SyntheticReportGenerator()
    created_path = generator.create_pdf(
        report_type=rep_type,
        output_path=output_file,
        employee_name=args.name,
        employee_id=args.id,
        company_name=args.company,
        year=args.year,
        month=args.month,
        work_days_count=args.days,
        hourly_rate=args.rate,
    )

    TerminalUI.file_box(created_path, label=f"קובץ PDF חדש שנוצר (פורמט {rep_type})")
    TerminalUI.success(f"קובץ ה-PDF החדש בפורמט {rep_type} נוצר בהצלחה רבה!")


if __name__ == "__main__":
    main()
