import sys
import argparse
from pathlib import Path
from dataclasses import dataclass
from typing import Optional

# הוספת תיקיית השורש ו-src ל-sys.path
_root = Path(__file__).resolve().parent
_src = _root / "src"
for p in [_root, _src]:
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from src.ocr import extract_raw_text_from_pdf, classify_report, ReportType
from src.parsers import BaseParser, TypeAParser, TypeBParser
from src.strategies import (
    BaseTransformationStrategy,
    TypeATransformationStrategy,
    TypeBTransformationStrategy,
)
from src.generation import PDFBuilder
from src.generation.generator import SyntheticReportGenerator


# ==============================================================================
# תבנית עיצוב: Factory Method
# ==============================================================================

@dataclass
class PipelineComponents:
    """
    אוגדן הרכיבים הדרושים לעיבוד דוח מסוג מסוים (Factory Product).
    כולל את המפענח (Parser), אסטרטגיית הטרנספורמציה (Strategy) ותבנית ה-HTML (Template).
    """
    parser: BaseParser
    strategy: BaseTransformationStrategy
    template_name: str
    report_type: ReportType


class ReportPipelineFactory:
    """
    מפעל פולימורפי (Factory Method) לייצור רכיבי הצינור המתאימים לכל סוג דוח.
    מרכז את כל ההבדלים הספציפיים לסוג הדוח במקום אחד בלבד, כך ששאר המערכת
    פועלת באופן אגנוסטי לחלוטין.
    """

    @staticmethod
    def create_pipeline(report_type: ReportType, target_row_count: int = 5) -> PipelineComponents:
        if report_type == ReportType.TYPE_A:
            return PipelineComponents(
                parser=TypeAParser(),
                strategy=TypeATransformationStrategy(target_row_count=target_row_count),
                template_name="type_a_report.html",
                report_type=report_type,
            )
        elif report_type == ReportType.TYPE_B:
            return PipelineComponents(
                parser=TypeBParser(),
                strategy=TypeBTransformationStrategy(target_row_count=target_row_count),
                template_name="type_b_report.html",
                report_type=report_type,
            )
        else:
            raise ValueError(
                f"סוג דוח אינו נתמך במערכת: '{report_type.value}'. "
                "המערכת תומכת כעת בדוחות מסוג A ומסוג B."
            )


# ==============================================================================
# Facade מרכזי - אגנוסטי לחלוטין לסוג הדו"ח
# ==============================================================================

class AttendancePipelineFacade:
    """
    Facade מרכזי המנהל את כל שלבי הצינור מקצה לקצה בצורה פולימורפית ואגנוסטית:
    1. קליטת קובץ PDF (מתיקיית data/input או נתיב ישיר)
    2. חילוץ טקסט גולמי באמצעות תשתית ה-OCR (אגנוסטי)
    3. סיווג סוג הדוח באמצעות ה-Classifier
    4. שימוש ב-Factory Method לקבלת רכיבי הצינור המתאימים (Parser, Strategy, Template)
    5. פיענוח הדוח באמצעות ה-Parser הפולימורפי (אגנוסטי)
    6. הפעלת אסטרטגיית הטרנספורמציה הפולימורפית (אגנוסטי)
    7. הפקת קובץ פלט מאומת (PDF) לתיקיית data/output (אגנוסטי)
    """

    def process_pdf(self, pdf_path: str | Path, output_file: Optional[str | Path] = None) -> Path:
        # איתור הקובץ - תמיכה בנתיב ישיר או חיפוש אוטומטי ב-data/input
        path = Path(pdf_path)
        if not path.is_file():
            alt_path = _root / "data" / "input" / pdf_path
            if alt_path.is_file():
                path = alt_path
            else:
                alt_path_stem = _root / "data" / "input" / Path(pdf_path).name
                if alt_path_stem.is_file():
                    path = alt_path_stem
                else:
                    raise FileNotFoundError(
                        f"קובץ ה-PDF לא נמצא: '{pdf_path}'. "
                        f"נבדקו גם הנתיבים: '{alt_path}' ו-'{alt_path_stem}'."
                    )

        print("=" * 60)
        print(f"🚀 התחלת ריצת Pipeline פולימורפי עבור: {path.name}")
        print("=" * 60)

        # ----------------------------------------------------------------------
        # שלב 1: חילוץ טקסט גולמי באמצעות OCR (אגנוסטי)
        # ----------------------------------------------------------------------
        print(f"\n[1/5] מפעיל OCR על העמוד הראשון של '{path.name}'...")
        raw_text = extract_raw_text_from_pdf(path)
        print(f"      הושלם! חולצו {len(raw_text)} תווים.")

        # ----------------------------------------------------------------------
        # שלב 2: סיווג סוג הדוח (Classifier)
        # ----------------------------------------------------------------------
        print("\n[2/5] מסווג את סוג הדוח (Classifier)...")
        report_type = classify_report(raw_text)
        print(f"      סוג הדוח שזוהה: >>> {report_type.value} <<<")

        # ----------------------------------------------------------------------
        # שלב 3: הפעלת ה-Factory Method לקבלת רכיבי הצינור הרלוונטיים
        # ----------------------------------------------------------------------
        components = ReportPipelineFactory.create_pipeline(report_type, target_row_count=5)
        print(f"      Factory הפיק רכיבים עבור {report_type.value}:")
        print(f"      * Parser:   {components.parser.__class__.__name__}")
        print(f"      * Strategy: {components.strategy.__class__.__name__}")
        print(f"      * Template: {components.template_name}")

        # ----------------------------------------------------------------------
        # שלב 4: פיענוח נתונים (פולימורפי - אגנוסטי לחלוטין!)
        # ----------------------------------------------------------------------
        print(f"\n[3/5] מפענח נתונים ומאכלס את ה-Dataclass ({components.parser.__class__.__name__})...")
        report = components.parser.parse(raw_text)
        if not report.employee_name:
            report.employee_name = f"עובד ({path.stem})"
        if not report.employee_id:
            report.employee_id = f"EMP-{path.stem.upper()}"
        print(f"      חולצו בהצלחה {len(report.rows)} שורות נוכחות.")
        print(f"      כותרת/מעסיק: {report.company_name or 'לא זוהה'}")
        print(f"      שם עובד: {report.employee_name} | מזהה: {report.employee_id}")
        month_str = report.report_month.strftime('%m/%Y') if report.report_month else 'לא זוהה'
        print(f"      חודש דוח: {month_str}")
        print(f"      סך שעות מקורי: {report.total_hours:.2f}")

        # ----------------------------------------------------------------------
        # שלב 5: הפעלת אסטרטגיית הטרנספורמציה (פולימורפי - אגנוסטי לחלוטין!)
        # ----------------------------------------------------------------------
        print(f"\n[4/5] מפעיל טרנספורמציה דטרמיניסטית ({components.strategy.__class__.__name__})...")
        modified_report = components.strategy.transform(report)
        print(f"      כמות השורות צומצמה מ-{len(report.rows)} ל-{len(modified_report.rows)} שורות.")
        print(f"      שעות כניסה ויציאה עודכנו (exit_time > entry_time מאומת לוגית).")
        print(f"      סך שעות מעודכן: {modified_report.total_hours:.2f} (ימי עבודה: {modified_report.total_work_days})")

        # ----------------------------------------------------------------------
        # שלב 6: יצירת פלט (פולימורפי - אגנוסטי לחלוטין!)
        # ----------------------------------------------------------------------
        if not output_file:
            out_dir = _root / "data" / "output"
            out_dir.mkdir(parents=True, exist_ok=True)
            output_file = out_dir / f"output_{path.stem}_verified.pdf"
        else:
            output_file = Path(output_file)
            output_file.parent.mkdir(parents=True, exist_ok=True)

        print(f"\n[5/5] מייצר קובץ פלט מאומת ({output_file.name}) בתבנית {components.template_name}...")
        builder = PDFBuilder(template_name=components.template_name)
        out_result = builder.build(modified_report, output_file)
        print(f"      קובץ הפלט נוצר בהצלחה בנתיב:")
        print(f"      -> {out_result.resolve()}")

        print("\n" + "=" * 60)
        print("✅ הצינור הפולימורפי (Pipeline) הסתיים בהצלחה מלאה מקצה לקצה!")
        print("=" * 60)
        return out_result


# ==============================================================================
# ממשק שורת פקודה (CLI)
# ==============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="מערכת עיבוד וייצור דוחות נוכחות חודשיים: קליטת PDF קיים או ייצור דוח חדש מאפס"
    )
    parser.add_argument(
        "pdf_path",
        nargs="?",
        default=None,
        help="נתיב לקובץ PDF סרוק לעיבוד (למשל: a_r_9.pdf). אופציונלי אם משתמשים ב---new",
    )
    parser.add_argument(
        "--new",
        "--generate",
        dest="generate_type",
        choices=["A", "B", "a", "b"],
        default=None,
        help="ייצור קובץ PDF חדש לחלוטין מאפס בפורמט A או פורמט B (ללא תלות בקובץ סריקה קיים)",
    )
    parser.add_argument(
        "--output",
        "-o",
        default=None,
        help="נתיב לקובץ הפלט המבוקש (ברירת מחדל: data/output/...)",
    )
    parser.add_argument(
        "--name",
        "-n",
        default="ישראל ישראלי",
        help="שם העובד (בעת ייצור דוח חדש)",
    )
    parser.add_argument(
        "--month",
        "-m",
        type=int,
        default=1,
        help="חודש הדוח (1 עד 12, בעת ייצור דוח חדש)",
    )
    parser.add_argument(
        "--year",
        "-y",
        type=int,
        default=2023,
        help="שנת הדוח (בעת ייצור דוח חדש)",
    )

    args = parser.parse_args()

    # מצב 1: ייצור דוח חדש מאפס ללא קובץ קיים
    if args.generate_type:
        rep_type = args.generate_type.upper()
        if not args.output:
            out_dir = _root / "data" / "output"
            out_dir.mkdir(parents=True, exist_ok=True)
            output_file = out_dir / f"new_report_{rep_type}.pdf"
        else:
            output_file = Path(args.output)
            output_file.parent.mkdir(parents=True, exist_ok=True)

        print("=" * 60)
        print(f"✨ מייצר דוח PDF חדש לחלוטין בפורמט {rep_type}")
        print(f"   * שם עובד: {args.name}")
        print(f"   * חודש/שנה: {args.month:02d}/{args.year}")
        print("=" * 60)

        generator = SyntheticReportGenerator()
        created_file = generator.create_pdf(
            report_type=rep_type,
            output_path=output_file,
            employee_name=args.name,
            month=args.month,
            year=args.year,
        )

        print(f"\n✅ הקובץ החדש נוצר בהצלחה:")
        print(f"👉 {created_file.resolve()}")
        print("\nלצפייה בקובץ:")
        print(f'Start-Process "{created_file}"')
        return

    # מצב 2: עיבוד קובץ סריקה קיים
    target_pdf = args.pdf_path or "a_r_9.pdf"
    facade = AttendancePipelineFacade()
    try:
        facade.process_pdf(target_pdf, args.output)
    except Exception as e:
        print(f"\n❌ שגיאה בהרצת הצינור: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
