import os
import sys
import argparse
from pathlib import Path
from typing import Optional
from PIL import Image
import pytesseract
from pdf2image import convert_from_path

# ==============================================================================
# תשתית OCR לחילוץ טקסט גולמי מ-PDF (דוחות נוכחות סרוקים)
# ==============================================================================

def extract_raw_text_from_pdf(
    pdf_path: str | Path,
    dpi: int = 300,
    lang: str = "heb+eng",
    tesseract_cmd: Optional[str] = None,
    poppler_path: Optional[str] = None,
) -> str:
    """
    ממירה את העמוד הראשון של קובץ PDF לתמונה ומבצעת עליה OCR באמצעות Tesseract.

    :param pdf_path: נתיב לקובץ ה-PDF.
    :param dpi: רזולוציית התמונה המופקת (ברירת מחדל: 300 DPI, מומלץ ל-OCR איכותי).
    :param lang: שפות הזיהוי של Tesseract (ברירת מחדל: 'heb+eng').
    :param tesseract_cmd: נתיב מפורש לקובץ ההפעלה tesseract.exe (רלוונטי ב-Windows אם לא ב-PATH).
    :param poppler_path: נתיב מפורש לתיקיית ה-bin של Poppler (רלוונטי ב-Windows אם לא ב-PATH).
    :return: מחרוזת המכילה את הטקסט הגולמי כפי שחולץ מהעמוד הראשון.
    """
    pdf_file = Path(pdf_path)
    if not pdf_file.exists():
        raise FileNotFoundError(f"הקובץ לא נמצא: {pdf_path}")

    import shutil

    if tesseract_cmd:
        pytesseract.pytesseract.tesseract_cmd = tesseract_cmd
    elif os.environ.get("TESSERACT_CMD"):
        pytesseract.pytesseract.tesseract_cmd = os.environ["TESSERACT_CMD"]
    elif not shutil.which("tesseract"):
        default_tess = Path(r"C:\Program Files\Tesseract-OCR\tesseract.exe")
        if default_tess.exists():
            pytesseract.pytesseract.tesseract_cmd = str(default_tess)

    if not poppler_path and os.environ.get("POPPLER_PATH"):
        poppler_path = os.environ["POPPLER_PATH"]
    elif not poppler_path and not shutil.which("pdftoppm"):
        local_app_data = os.environ.get("LOCALAPPDATA", "")
        if local_app_data:
            winget_poppler = list(Path(local_app_data).glob("Microsoft/WinGet/Packages/*Poppler*/**/bin"))
            for p in winget_poppler:
                if (p / "pdftoppm.exe").exists():
                    poppler_path = str(p)
                    break

    images = convert_from_path(
        str(pdf_file),
        dpi=dpi,
        first_page=1,
        last_page=1,
        poppler_path=poppler_path,
    )

    if not images:
        raise ValueError("לא הצלחנו לחלץ עמודים מקובץ ה-PDF.")

    first_page_image: Image.Image = images[0]
    raw_text: str = pytesseract.image_to_string(first_page_image, lang=lang)
    return raw_text


def main():
    parser = argparse.ArgumentParser(
        description="תשתית OCR לחילוץ טקסט גולמי מעמוד ראשון של PDF (דוחות נוכחות)"
    )
    parser.add_argument("pdf_path", help="נתיב לקובץ ה-PDF לעיבוד")
    parser.add_argument(
        "--lang",
        default="heb+eng",
        help="שפות עבור Tesseract (ברירת מחדל: heb+eng)",
    )
    parser.add_argument(
        "--tesseract-cmd",
        default=None,
        help="נתיב לקובץ ההפעלה tesseract (אופציונלי במידה ואינו ב-PATH)",
    )
    parser.add_argument(
        "--poppler-path",
        default=None,
        help="נתיב לספריית bin של Poppler (אופציונלי במידה ואינה ב-PATH)",
    )
    parser.add_argument(
        "--bidi",
        action="store_true",
        help="היפוך סדר ויזואלי לתצוגת עברית תקינה בטרמינלים של LTR (באמצעות python-bidi)",
    )

    args = parser.parse_args()

    print(f"--- מתחיל עיבוד OCR עבור: {args.pdf_path} ---")
    try:
        raw_text = extract_raw_text_from_pdf(
            pdf_path=args.pdf_path,
            lang=args.lang,
            tesseract_cmd=args.tesseract_cmd,
            poppler_path=args.poppler_path,
        )
        print("=== תוכן הטקסט הגולמי שחולץ (Raw OCR Output) ===")
        if args.bidi:
            try:
                from bidi.algorithm import get_display
                lines = [get_display(line) for line in raw_text.splitlines()]
                print("\n".join(lines))
            except ImportError:
                print(raw_text)
        else:
            print(raw_text)
        print("=== סיום פלט ===")
    except Exception as e:
        print(f"שגיאה במהלך ביצוע ה-OCR: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
