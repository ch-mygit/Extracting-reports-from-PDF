import re
import sys
import argparse
from pathlib import Path
from enum import Enum
from difflib import SequenceMatcher
from typing import Tuple, Dict, Any


class ReportType(str, Enum):
    """סוגי הדוחות המזוהים במערכת."""
    TYPE_A = "Type A"
    TYPE_B = "Type B"
    UNKNOWN = "Unknown"


def _fuzzy_best_match(needle: str, text: str) -> float:
    needle_clean = re.sub(r"\s+", " ", needle.strip())
    if not needle_clean or not text:
        return 0.0

    if needle_clean in text:
        return 1.0

    words = text.split()
    needle_word_count = len(needle_clean.split())
    best_score = 0.0
    matcher = SequenceMatcher(None, needle_clean, "")

    min_window = max(1, needle_word_count - 1)
    max_window = needle_word_count + 3

    for window_len in range(min_window, min_window + max_window):
        if window_len > len(words):
            break
        for i in range(len(words) - window_len + 1):
            window_text = " ".join(words[i : i + window_len])
            matcher.set_seq2(window_text)
            score = matcher.ratio()
            if score > best_score:
                best_score = score
                if best_score >= 0.95:
                    return best_score

    return best_score


def classify_report_detailed(text: str, threshold: float = 0.65) -> Tuple[ReportType, Dict[str, Any]]:
    normalized_text = re.sub(r"[\|\_\\\/]", " ", text)
    normalized_text = re.sub(r"\s+", " ", normalized_text)

    # עוגנים לסוג A
    anchors_a = {
        "נ.ע. הנשר כח אדם": 35.0,
        "גליליון": 25.0,
        "הפסקה": 15.0,
    }

    score_a = 0.0
    matched_a = {}

    for anchor, weight in anchors_a.items():
        sim = _fuzzy_best_match(anchor, normalized_text)
        if sim >= threshold:
            gained = weight * sim
            score_a += gained
            matched_a[anchor] = f"{sim:.2f} (נקודות: {gained:.1f}/{weight})"

    percentage_matches = len(re.findall(r"(?:100|125|150)\s*%", text))
    if percentage_matches >= 2:
        score_a += 25.0
        matched_a["אחוזי שעות (100%/125%/150%)"] = f"{percentage_matches} התאמות (נקודות: 25.0/25)"
    elif percentage_matches == 1:
        score_a += 12.0
        matched_a["אחוזי שעות (חלקי)"] = "התאמה 1 (נקודות: 12.0/25)"

    # עוגנים לסוג B
    score_b = 0.0
    matched_b = {}

    title_b_anchors = ["כרטיס עובד לחודש", "כרטיס עובד", "ימי עבודה לחודש", "עבודה לחודש"]
    best_title_b = max([_fuzzy_best_match(a, normalized_text) for a in title_b_anchors])
    if best_title_b >= threshold:
        gained = 30.0 * best_title_b
        score_b += gained
        matched_b["כותרת כרטיס עובד/ימי עבודה"] = f"{best_title_b:.2f} (נקודות: {gained:.1f}/30.0)"

    entry_b_score = max(_fuzzy_best_match("שעת כניסה", normalized_text), _fuzzy_best_match("כניסה", normalized_text))
    if entry_b_score >= threshold:
        gained = 15.0 * entry_b_score
        score_b += gained
        matched_b["שעת כניסה"] = f"{entry_b_score:.2f} (נקודות: {gained:.1f}/15.0)"

    exit_b_score = max(_fuzzy_best_match("שעת יציאה", normalized_text), _fuzzy_best_match("יציאה", normalized_text))
    if exit_b_score >= threshold:
        gained = 15.0 * exit_b_score
        score_b += gained
        matched_b["שעת יציאה"] = f"{exit_b_score:.2f} (נקודות: {gained:.1f}/15.0)"

    notes_score = _fuzzy_best_match("הערות", normalized_text)
    if notes_score >= threshold:
        gained = 15.0 * notes_score
        score_b += gained
        matched_b["הערות"] = f"{notes_score:.2f} (נקודות: {gained:.1f}/15.0)"

    pay_b_anchors = ["סה\"כ לתשלום", "לתשלום", "שעות עבודה"]
    best_pay_b = max([_fuzzy_best_match(a, normalized_text) for a in pay_b_anchors])
    if best_pay_b >= threshold:
        gained = 25.0 * best_pay_b
        score_b += gained
        matched_b["סיכום שכר/שעות עבודה"] = f"{best_pay_b:.2f} (נקודות: {gained:.1f}/25.0)"

    min_score = 20.0

    if score_a >= min_score and score_a > (score_b + 10.0):
        decision = ReportType.TYPE_A
    elif score_b >= min_score and score_b > score_a:
        decision = ReportType.TYPE_B
    elif score_a >= min_score and score_a > score_b:
        decision = ReportType.TYPE_A
    else:
        decision = ReportType.UNKNOWN

    details = {
        "score_a": round(score_a, 2),
        "score_b": round(score_b, 2),
        "matched_a": matched_a,
        "matched_b": matched_b,
    }

    return decision, details


def classify_report(text: str) -> ReportType:
    decision, _ = classify_report_detailed(text)
    return decision


def classify_file(file_path: str) -> Tuple[ReportType, Dict[str, Any]]:
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"הקובץ לא נמצא: {file_path}")

    if path.suffix.lower() == ".pdf":
        try:
            from .ocr_infrastructure import extract_raw_text_from_pdf
        except ImportError:
            from ocr_infrastructure import extract_raw_text_from_pdf
        print(f"--- מזהה קובץ PDF: מחלץ OCR מהעמוד הראשון של '{path.name}'... ---")
        content = extract_raw_text_from_pdf(path)
    else:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()

    return classify_report_detailed(content)


def main():
    parser = argparse.ArgumentParser(description="מסווג סוגי דוחות נוכחות (Type A מול Type B)")
    parser.add_argument(
        "file",
        nargs="?",
        default=None,
        help="נתיב לקובץ PDF או קובץ טקסט (אופציונלי).",
    )
    args = parser.parse_args()

    if args.file:
        try:
            report_type, details = classify_file(args.file)
            print("=" * 50)
            print(f"תוצאת סיווג עבור '{args.file}': >>> {report_type.value} <<<")
            print("=" * 50)
            print(f"ניקוד: סוג A = {details['score_a']} | סוג B = {details['score_b']}")
        except Exception as e:
            print(f"שגיאה בעיבוד הקובץ: {e}", file=sys.stderr)
            sys.exit(1)
        return

    print("נא לספק נתיב לקובץ PDF או טקסט לסיווג.")


if __name__ == "__main__":
    main()
