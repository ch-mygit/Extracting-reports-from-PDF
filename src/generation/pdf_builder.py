import os
import sys
import shutil
import subprocess
from pathlib import Path
from typing import Optional

from jinja2 import Environment, FileSystemLoader, select_autoescape

_src_dir = Path(__file__).resolve().parent.parent
if str(_src_dir) not in sys.path:
    sys.path.insert(0, str(_src_dir))

try:
    from models import AttendanceReport
except ImportError:
    from models.models import AttendanceReport


# בדיקת זמינות של מנועי ההמרה WeasyPrint ו-pdfkit
try:
    import weasyprint
    HAS_WEASYPRINT = True
except (ImportError, OSError):
    HAS_WEASYPRINT = False

try:
    import pdfkit
    HAS_PDFKIT = True
except ImportError:
    HAS_PDFKIT = False


class PDFBuilder:
    """
    מייצרת מסמך PDF דינמי חדש מתוך אובייקט הנתונים AttendanceReport.
    מזריקה את הנתונים לתבנית Jinja2 (HTML/CSS) וממירה ל-PDF בעזרת WeasyPrint או pdfkit.

    כלל הפרדת רשויות:
    מחלקה זו אינה מכילה שום ייבוא (import) או ידע לגבי שלבי ה-OCR, תמונות או הפרסור.
    היא פועלת אך ורק מול מודל הנתונים הסופי.
    """

    def __init__(self, template_dir: Optional[str | Path] = None, template_name: str = "type_a_report.html"):
        if template_dir is None:
            # 1. חיפוש בתיקיית templates הצמודה למודל ה-generation
            local_templates = Path(__file__).resolve().parent / "templates"
            if local_templates.exists():
                self.template_dir = local_templates
            else:
                # 2. גיבוי: חיפוש בשורש הפרויקט
                self.template_dir = Path(__file__).resolve().parent.parent.parent / "templates"
        else:
            self.template_dir = Path(template_dir)

        self.template_name = template_name

        # אתחול סביבת Jinja2
        self.jinja_env = Environment(
            loader=FileSystemLoader(str(self.template_dir)),
            autoescape=select_autoescape(["html", "xml"]),
        )

    def render_html(self, report: AttendanceReport) -> str:
        """מזריקה את אובייקט ה-AttendanceReport לתבנית ה-HTML ומחזירה מחרוזת HTML מעוצבת."""
        template = self.jinja_env.get_template(self.template_name)
        heb_months = {
            1: "ינו", 2: "פבר", 3: "מרץ", 4: "אפר", 5: "מאי", 6: "יונ",
            7: "יול", 8: "אוג", 9: "ספט", 10: "אוק", 11: "נוב", 12: "דצמ"
        }
        month_label = ""
        if report.report_month:
            m_heb = heb_months.get(report.report_month.month, str(report.report_month.month))
            y_2d = str(report.report_month.year)[2:]
            month_label = f"{m_heb}-{y_2d}"
        return template.render(report=report, month_hebrew_str=month_label)

    def build(self, report: AttendanceReport, output_path: str | Path) -> Path:
        """
        מייצרת את קובץ ה-PDF החדש מתוך הדוח.

        :param report: אובייקט ה-AttendanceReport המעודכן.
        :param output_path: נתיב לקובץ ה-PDF שייווצר.
        :return: Path לקובץ ה-PDF שנוצר.
        """
        out_path = Path(output_path).resolve()
        out_path.parent.mkdir(parents=True, exist_ok=True)

        # 1. יצירת ה-HTML המעוצב
        html_content = self.render_html(report)

        # שמירת עותק HTML לתצוגה מקדימה ודיבאג
        html_debug_path = out_path.with_suffix(".html")
        with open(html_debug_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        # 2. המרה ל-PDF באמצעות WeasyPrint
        if HAS_WEASYPRINT:
            weasyprint.HTML(
                string=html_content,
                base_url=str(self.template_dir),
            ).write_pdf(str(out_path))
            return out_path

        # 3. המרה ל-PDF באמצעות pdfkit (אם מותקן)
        if HAS_PDFKIT:
            options = {
                "encoding": "UTF-8",
                "enable-local-file-access": None,
                "page-size": "A4",
                "orientation": "Portrait",
                "margin-top": "10mm",
                "margin-bottom": "10mm",
                "margin-left": "15mm",
                "margin-right": "15mm",
            }
            pdfkit.from_string(html_content, str(out_path), options=options)
            return out_path

        # 4. מנגנון גיבוי מובנה ב-Windows: הדפסה ל-PDF באמצעות מנוע הדפדפן (Edge/Chrome Headless)
        edge_browser = self._find_headless_browser()
        if edge_browser:
            cmd = [
                edge_browser,
                "--headless",
                "--disable-gpu",
                "--run-all-compositor-stages-before-draw",
                f"--print-to-pdf={str(out_path)}",
                str(html_debug_path.as_uri()),
            ]
            subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return out_path

        raise RuntimeError(
            "לא נמצא מנוע המרה ל-PDF. יש להתקין WeasyPrint (pip install weasyprint) "
            "או pdfkit (pip install pdfkit)."
        )

    def _find_headless_browser(self) -> Optional[str]:
        """מאתרת דפדפן Chromium מובנה במערכת (Edge או Chrome) לצורך המרת HTML ל-PDF נקייה."""
        common_paths = [
            r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
            r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
            shutil.which("msedge"),
            shutil.which("chrome"),
        ]
        for p in common_paths:
            if p and os.path.exists(p):
                return p
        return None
