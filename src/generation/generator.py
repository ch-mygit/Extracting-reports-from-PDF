import calendar
import random
from datetime import date, time, timedelta
from pathlib import Path
from typing import Optional, List

from ..models.models import AttendanceReport, AttendanceRow
from .pdf_builder import PDFBuilder


class SyntheticReportGenerator:
    """
    מחולל דוחות נוכחות חדשים לחלוטין (מאפס) בפורמט A או פורמט B,
    ללא תלות בקובץ סריקה קיים או בשלבי OCR.
    """

    HEBREW_DAYS = ["שני", "שלישי", "רביעי", "חמישי", "שישי", "שבת", "ראשון"]

    @staticmethod
    def _get_hebrew_weekday(d: date) -> str:
       
        weekday_map = {
            6: "ראשון",
            0: "שני",
            1: "שלישי",
            2: "רביעי",
            3: "חמישי",
            4: "שישי",
            5: "שבת",
        }
        return weekday_map[d.weekday()]

    def generate_report(
        self,
        report_type: str = "A",
        employee_name: str = "ישראל ישראלי",
        employee_id: str = "123456789",
        company_name: Optional[str] = None,
        year: int = 2023,
        month: int = 1,
        work_days_count: Optional[int] = None,
        hourly_rate: float = 35.0,
        bonus: float = 150.0,
        travel_expenses: float = 120.0,
    ) -> AttendanceReport:
        """
        מייצרת אובייקט AttendanceReport מלא, עקבי וריאליסטי עבור חודש נתון.
        """
        report_type = report_type.upper().strip()
        if "B" in report_type:
            company = company_name or "חברת שירותי ניהול בע\"מ"
        else:
            company = company_name or "נ.ע. הנשר כח אדם בע\"מ"

        report_month = date(year, month, 1)
        num_days_in_month = calendar.monthrange(year, month)[1]

        rows: List[AttendanceRow] = []
        total_hours = 0.0
        total_hours_100 = 0.0
        total_hours_125 = 0.0
        total_hours_150 = 0.0
        total_shabbat = 0.0
        actual_work_days = 0

        # יצירת שורות לכל ימי החודש
        for day in range(1, num_days_in_month + 1):
            cur_date = date(year, month, day)
            day_name = self._get_hebrew_weekday(cur_date)

            is_shabbat = (day_name == "שבת")
            is_friday = (day_name == "שישי")

            # הגבלה על כמות ימי עבודה אם הוגדרה במפורש
            if work_days_count is not None and actual_work_days >= work_days_count and not is_shabbat:
                # יום חופש/מנוחה
                continue

            if report_type == "B":
                # פורמט B
                if is_shabbat:
                    # שורת שבת מוצללת באפור ללא שעות
                    rows.append(
                        AttendanceRow(
                            date=cur_date,
                            day_of_week="שבת",
                            notes="שבת",
                        )
                    )
                elif is_friday:
                    # יום שישי - מנוחה
                    rows.append(
                        AttendanceRow(
                            date=cur_date,
                            day_of_week="שישי",
                            notes="יום שישי",
                        )
                    )
                else:
                    # יום עבודה רגיל
                    entry_h = random.choice([7, 8])
                    entry_m = random.choice([0, 15, 30, 45])
                    entry = time(entry_h, entry_m)

                    duration_hours = random.choice([7.0, 7.5, 8.0, 8.5, 9.0])
                    exit_minutes_total = entry_h * 60 + entry_m + int(duration_hours * 60)
                    exit_h = (exit_minutes_total // 60) % 24
                    exit_m = exit_minutes_total % 60
                    exit_t = time(exit_h, exit_m)

                    day_hours = round(duration_hours, 2)
                    rows.append(
                        AttendanceRow(
                            date=cur_date,
                            day_of_week=day_name,
                            entry_time=entry,
                            exit_time=exit_t,
                            total_hours=day_hours,
                            notes="רגיל",
                        )
                    )
                    total_hours += day_hours
                    actual_work_days += 1

            else:
                # פורמט A
                if is_shabbat:
                    # בסוג A: לעיתים עובדים שבת עם תעריף 150%
                    work_on_shabbat = (random.random() < 0.25)  # 25% סיכוי למשמרת שבת
                    if work_on_shabbat:
                        entry = time(8, 0)
                        exit_t = time(14, 30)
                        break_t = timedelta(minutes=30)
                        shabbat_hrs = 6.0
                        rows.append(
                            AttendanceRow(
                                date=cur_date,
                                day_of_week="שבת",
                                location="גליליון",
                                entry_time=entry,
                                exit_time=exit_t,
                                break_time=break_t,
                                hours_100=0.0,
                                hours_125=0.0,
                                hours_150=shabbat_hrs,
                                shabbat_hours=shabbat_hrs,
                                total_hours=shabbat_hrs,
                                notes="עבודה בשבת",
                            )
                        )
                        total_hours += shabbat_hrs
                        total_hours_150 += shabbat_hrs
                        total_shabbat += shabbat_hrs
                        actual_work_days += 1
                elif is_friday:
                    # יום שישי
                    rows.append(
                        AttendanceRow(
                            date=cur_date,
                            day_of_week="שישי",
                            location="גליליון",
                            notes="חופש",
                        )
                    )
                else:
                    # יום רגיל בסוג A
                    entry_h = random.choice([7, 8])
                    entry_m = random.choice([0, 15, 30])
                    entry = time(entry_h, entry_m)

                    work_duration = random.choice([8.5, 9.0, 9.5, 10.0])
                    exit_minutes_total = entry_h * 60 + entry_m + int(work_duration * 60)
                    exit_t = time((exit_minutes_total // 60) % 24, exit_minutes_total % 60)
                    break_t = timedelta(minutes=30)

                    net_hours = work_duration - 0.5  # פחות חצי שעה הפסקה

                    # חלוקת שעות נוספות תקנית בישראל
                    h100 = min(net_hours, 8.0)
                    rem = max(0.0, net_hours - 8.0)
                    h125 = min(rem, 2.0)
                    h150 = max(0.0, rem - 2.0)

                    rows.append(
                        AttendanceRow(
                            date=cur_date,
                            day_of_week=day_name,
                            location="גליליון",
                            entry_time=entry,
                            exit_time=exit_t,
                            break_time=break_t,
                            hours_100=round(h100, 2),
                            hours_125=round(h125, 2),
                            hours_150=round(h150, 2),
                            shabbat_hours=0.0,
                            total_hours=round(net_hours, 2),
                        )
                    )
                    total_hours += net_hours
                    total_hours_100 += h100
                    total_hours_125 += h125
                    total_hours_150 += h150
                    actual_work_days += 1

        total_hours = round(total_hours, 2)
        total_payment = round(total_hours * hourly_rate, 2)

        return AttendanceReport(
            company_name=company,
            employee_name=employee_name,
            employee_id=employee_id,
            report_month=report_month,
            rows=rows,
            total_hours=total_hours,
            total_hours_100=round(total_hours_100, 2),
            total_hours_125=round(total_hours_125, 2),
            total_hours_150=round(total_hours_150, 2),
            total_shabbat_hours=round(total_shabbat, 2),
            total_work_days=actual_work_days,
            hourly_rate=hourly_rate,
            total_payment=total_payment,
            travel_expenses=travel_expenses if "A" in report_type else 0.0,
            bonus=bonus if "A" in report_type else 0.0,
        )

    def create_pdf(
        self,
        report_type: str = "A",
        output_path: str | Path = "data/output/new_report.pdf",
        employee_name: str = "ישראל ישראלי",
        employee_id: str = "123456789",
        company_name: Optional[str] = None,
        year: int = 2023,
        month: int = 1,
        work_days_count: Optional[int] = None,
        hourly_rate: float = 35.0,
    ) -> Path:
        """
        יוצרת דוח חדש לחלוטין ומייצאת אותו ישירות ל-PDF מעוצב בהתאם לפורמט הנבחר.
        """
        report_type = report_type.upper().strip()
        template_name = "type_b_report.html" if "B" in report_type else "type_a_report.html"

        report = self.generate_report(
            report_type=report_type,
            employee_name=employee_name,
            employee_id=employee_id,
            company_name=company_name,
            year=year,
            month=month,
            work_days_count=work_days_count,
            hourly_rate=hourly_rate,
        )

        builder = PDFBuilder(template_name=template_name)
        out_file = Path(output_path)
        out_file.parent.mkdir(parents=True, exist_ok=True)
        return builder.build(report, out_file)
