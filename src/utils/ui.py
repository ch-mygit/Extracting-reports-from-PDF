import os
import sys
from pathlib import Path
from typing import List, Tuple, Optional, Any

# תמיכה בצבעים בטרמינל (באמצעות colorama אם מותקנת)
try:
    import colorama
    colorama.init(autoreset=True)
    HAS_COLORAMA = True
except ImportError:
    HAS_COLORAMA = False


class Colors:
    """קודי צבעים ועיצוב ANSI לתצוגה עשירה ונקייה בטרמינל."""
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    CYAN = "\033[36m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    RED = "\033[31m"
    WHITE = "\033[37m"
    BG_CYAN = "\033[46m"
    BG_BLUE = "\033[44m"
    BG_GREEN = "\033[42m"


class TerminalUI:
    """
    ממשק משתמש טרמינלי עשיר (Rich CLI UX) להדפסות מעוצבות, טבלאות סיכום,
    חיווי שלבי התקדמות (Progress Steps), והתראות ויזואליות ברורות.
    """

    @classmethod
    def _c(cls, text: str, color: str) -> str:
        """עוטפת טקסט בקוד צבע ANSI אם הטרמינל תומך."""
        return f"{color}{text}{Colors.RESET}"

    @classmethod
    def banner(cls, title: str, subtitle: Optional[str] = None, width: int = 68):
        """מדפיסה כותרת ראשית מעוצבת בתוך מסגרת."""
        line = "═" * width
        print()
        print(cls._c(f"╔{line}╗", Colors.CYAN))
        print(cls._c(f"║ {title.center(width - 2)} ║", Colors.BOLD + Colors.CYAN))
        if subtitle:
            print(cls._c(f"║ {subtitle.center(width - 2)} ║", Colors.DIM + Colors.WHITE))
        print(cls._c(f"╚{line}╝", Colors.CYAN))
        print()

    @classmethod
    def step(cls, current: int, total: int, title: str, description: Optional[str] = None):
        """מדפיסה כותרת שלב התקדמות ממוספר ומעוצב."""
        badge = cls._c(f"[{current}/{total}]", Colors.BOLD + Colors.MAGENTA)
        styled_title = cls._c(title, Colors.BOLD + Colors.WHITE)
        print(f"\n{badge} {styled_title}")
        if description:
            print(cls._c(f"      {description}", Colors.DIM))

    @classmethod
    def success(cls, message: str, details: Optional[List[str]] = None):
        """מדפיסה הודעת הצלחה בולטת עם פירוט אופציונלי."""
        badge = cls._c("✔ הצלחה:", Colors.BOLD + Colors.GREEN)
        print(f"\n{badge} {cls._c(message, Colors.GREEN)}")
        if details:
            for detail in details:
                print(f"  {cls._c('•', Colors.GREEN)} {detail}")

    @classmethod
    def info(cls, label: str, value: Any, indent: int = 6):
        """מדפיסה שורת מידע נקייה עם תווית וערך."""
        spaces = " " * indent
        lbl = cls._c(f"{label}:", Colors.CYAN)
        val = cls._c(str(value), Colors.BOLD + Colors.WHITE)
        print(f"{spaces}{lbl:<24} {val}")

    @classmethod
    def warning(cls, message: str):
        """מדפיסה אזהרה צהובה בולטת."""
        badge = cls._c("⚠ אזהרה:", Colors.BOLD + Colors.YELLOW)
        print(f"{badge} {message}")

    @classmethod
    def error(cls, message: str, tip: Optional[str] = None):
        """מדפיסה הודעת שגיאה אדומה וברורה עם טיפ לפתרון."""
        badge = cls._c("✖ שגיאה:", Colors.BOLD + Colors.RED)
        print(f"\n{badge} {cls._c(message, Colors.RED)}", file=sys.stderr)
        if tip:
            tip_badge = cls._c("💡 טיפ לפתרון:", Colors.BOLD + Colors.YELLOW)
            print(f"   {tip_badge} {tip}", file=sys.stderr)

    @classmethod
    def summary_table(cls, title: str, rows: List[Tuple[str, str]], width: int = 64):
        """
        מדפיסה טבלת סיכום נתונים מעוצבת עם מסגרת נקייה.
        """
        col1_w = 26
        col2_w = width - col1_w - 7

        border_top = "┌" + "─" * (col1_w + 2) + "┬" + "─" * (col2_w + 2) + "┐"
        border_mid = "├" + "─" * (col1_w + 2) + "┼" + "─" * (col2_w + 2) + "┤"
        border_bot = "└" + "─" * (col1_w + 2) + "┴" + "─" * (col2_w + 2) + "┘"

        print("\n" + cls._c(f"📊 {title}:", Colors.BOLD + Colors.CYAN))
        print(cls._c(border_top, Colors.CYAN))
        print(
            cls._c("│ ", Colors.CYAN)
            + cls._c(f"{'פרמטר'.center(col1_w)}", Colors.BOLD + Colors.WHITE)
            + cls._c(" │ ", Colors.CYAN)
            + cls._c(f"{'ערך'.center(col2_w)}", Colors.BOLD + Colors.WHITE)
            + cls._c(" │", Colors.CYAN)
        )
        print(cls._c(border_mid, Colors.CYAN))

        for param, val in rows:
            print(
                cls._c("│ ", Colors.CYAN)
                + f"{param:<{col1_w}}"
                + cls._c(" │ ", Colors.CYAN)
                + cls._c(f"{val:<{col2_w}}", Colors.BOLD)
                + cls._c(" │", Colors.CYAN)
            )

        print(cls._c(border_bot, Colors.CYAN))

    @classmethod
    def comparison_table(cls, title: str, headers: Tuple[str, str, str], rows: List[Tuple[str, str, str]]):
        """
        מדפיסה טבלת השוואה (למשל לפני ואחרי טרנספורמציה).
        """
        w1, w2, w3 = 24, 14, 14
        border_top = "┌" + "─" * (w1 + 2) + "┬" + "─" * (w2 + 2) + "┬" + "─" * (w3 + 2) + "┐"
        border_mid = "├" + "─" * (w1 + 2) + "┼" + "─" * (w2 + 2) + "┼" + "─" * (w3 + 2) + "┤"
        border_bot = "└" + "─" * (w1 + 2) + "┴" + "─" * (w2 + 2) + "┴" + "─" * (w3 + 2) + "┘"

        print("\n" + cls._c(f"🔄 {title}:", Colors.BOLD + Colors.YELLOW))
        print(cls._c(border_top, Colors.YELLOW))
        print(
            cls._c("│ ", Colors.YELLOW)
            + cls._c(f"{headers[0]:<{w1}}", Colors.BOLD)
            + cls._c(" │ ", Colors.YELLOW)
            + cls._c(f"{headers[1]:^{w2}}", Colors.BOLD)
            + cls._c(" │ ", Colors.YELLOW)
            + cls._c(f"{headers[2]:^{w3}}", Colors.BOLD)
            + cls._c(" │", Colors.YELLOW)
        )
        print(cls._c(border_mid, Colors.YELLOW))

        for col1, col2, col3 in rows:
            print(
                cls._c("│ ", Colors.YELLOW)
                + f"{col1:<{w1}}"
                + cls._c(" │ ", Colors.YELLOW)
                + f"{col2:^{w2}}"
                + cls._c(" │ ", Colors.YELLOW)
                + cls._c(f"{col3:^{w3}}", Colors.BOLD + Colors.GREEN)
                + cls._c(" │", Colors.YELLOW)
            )

        print(cls._c(border_bot, Colors.YELLOW))

    @classmethod
    def file_box(cls, file_path: Path | str, label: str = "קובץ PDF מאומת שנוצר"):
        """מדפיסה כרטיס תוצאה עם נתיב הקובץ ופקודה לפתיחה מיידית."""
        resolved = Path(file_path).resolve()
        line = "─" * 66
        print("\n" + cls._c(f"┌{line}┐", Colors.GREEN))
        print(cls._c(f"│ 📄 {label}:".ljust(67) + "│", Colors.BOLD + Colors.GREEN))
        print(cls._c(f"│    {str(resolved)}".ljust(67) + "│", Colors.WHITE))
        print(cls._c(f"│    קישור מקומי: {resolved.as_uri()}".ljust(67) + "│", Colors.CYAN))
        print(cls._c(f"│    לפתיחה מיידית ב-PowerShell:".ljust(67) + "│", Colors.DIM))
        print(cls._c(f'│    Start-Process "{resolved.name}"'.ljust(67) + "│", Colors.BOLD + Colors.YELLOW))
        print(cls._c(f"└{line}┘", Colors.GREEN))
