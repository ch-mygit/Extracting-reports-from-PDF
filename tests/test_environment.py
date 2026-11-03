import os
import shutil
import subprocess
import sys
from pathlib import Path


def check_python_packages():
    print("[1/3] בודק ספריות פייתון...")
    packages = ["pytesseract", "pdf2image", "PIL", "jinja2"]
    all_ok = True
    for pkg in packages:
        try:
            __import__(pkg)
            print(f"  [V] ספריית {pkg} מותקנת בהצלחה.")
        except ImportError:
            print(f"  [X] ספריית {pkg} אינה מותקנת. הרץ: pip install -r requirements.txt")
            all_ok = False
    return all_ok


def check_poppler():
    print("\n[2/3] בודק את Poppler (המרה מ-PDF לתמונה)...")
    pdftoppm_path = shutil.which("pdftoppm")
    if pdftoppm_path:
        print(f"  [V] pdftoppm נמצא ב-PATH: {pdftoppm_path}")
        return True

    # בדיקת משתנה סביבה POPPLER_PATH
    if os.environ.get("POPPLER_PATH"):
        p_path = Path(os.environ["POPPLER_PATH"])
        if (p_path / "pdftoppm.exe").exists() or (p_path / "pdftoppm").exists():
            print(f"  [V] Poppler נמצא דרך משתנה סביבה POPPLER_PATH: {p_path}")
            return True

    # בדיקת התקנת WinGet
    local_app_data = os.environ.get("LOCALAPPDATA", "")
    if local_app_data:
        winget_poppler = list(Path(local_app_data).glob("Microsoft/WinGet/Packages/*Poppler*/**/bin"))
        for p in winget_poppler:
            if (p / "pdftoppm.exe").exists():
                print(f"  [V] Poppler נמצא בהתקנת WinGet: {p}")
                return True

    # בדיקת נתיבים נפוצים
    common_poppler_paths = [
        Path(r"C:\Program Files\poppler\bin"),
        Path(r"C:\Program Files (x86)\poppler\bin"),
        Path(r"C:\poppler\bin"),
    ]
    for cp in common_poppler_paths:
        if (cp / "pdftoppm.exe").exists():
            print(f"  [V] Poppler נמצא בנתיב: {cp}")
            return True

    print("  [!] pdftoppm אינו ב-PATH של המערכת או בנתיבים הסטנדרטיים.")
    print("      * pdf2image דורשת את Poppler כדי לפתוח PDF.")
    print("      * להתקנה קלה ב-Windows דרך PowerShell:")
    print("        winget install osdn.poppler")
    print("      * או להורדה מ: https://github.com/oschwartz10612/poppler-windows/releases")
    return False


def check_tesseract():
    print("\n[3/3] בודק את Tesseract OCR ותמיכה בעברית...")
    tesseract_path = shutil.which("tesseract")
    
    # בדיקת נתיב ברירת מחדל ב-Windows אם לא ב-PATH
    default_win_path = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
    if not tesseract_path and shutil.which(default_win_path):
        tesseract_path = default_win_path

    if not tesseract_path:
        print("  [!] מנוע Tesseract לא נמצא ב-PATH או במיקום ברירת המחדל.")
        print("      * יש להתקין את Tesseract (למשל מ: https://github.com/UB-Mannheim/tesseract/wiki).")
        print("      * חשוב: במהלך ההתקנה לסמן ב-Additional script data את עברית (Hebrew).")
        return False

    print(f"  [V] Tesseract נמצא: {tesseract_path}")

    # בדיקת שפות מותקנות
    try:
        res = subprocess.run([tesseract_path, "--list-langs"], capture_output=True, text=True, check=True)
        langs = res.stdout.splitlines()
        print("  שפות זמינות:", ", ".join([l.strip() for l in langs[1:] if l.strip()]))
        if "heb" in res.stdout:
            print("  [V] מודל עברית (heb) מותקן ותקין!")
            return True
        else:
            print("  [X] מודל עברית (heb) חסר! יש להוריד את heb.traineddata לתיקיית tessdata.")
            return False
    except Exception as e:
        print(f"  [!] שגיאה בבדיקת שפות מול Tesseract: {e}")
        return False


def main():
    print("=== בדיקת סביבה למערכת הדוחות ===")
    ok_pkgs = check_python_packages()
    ok_poppler = check_poppler()
    ok_tesseract = check_tesseract()

    print("\n=== סיכום ===")
    if ok_pkgs and ok_poppler and ok_tesseract:
        print("מעולה! הסביבה מוכנה להרצה מלאה.")
    else:
        print("ישנן הגדרות/תוכנות שדורשות השלמה (ראה פירוט למעלה).")


if __name__ == "__main__":
    main()
