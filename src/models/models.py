from dataclasses import dataclass, field
from datetime import date, time, timedelta
from typing import Optional, List


@dataclass
class AttendanceRow:
    date: Optional[date] = None
    day_of_week: Optional[str] = None
    entry_time: Optional[time] = None
    exit_time: Optional[time] = None
    break_time: Optional[timedelta | time] = None
    hours_100: float = 0.0
    hours_125: float = 0.0
    hours_150: float = 0.0
    total_hours: float = 0.0

    # שדות אופציונליים לסוגי דוחות שונים
    location: Optional[str] = None
    shabbat_hours: Optional[float] = 0.0
    daily_travel: Optional[float] = 0.0
    daily_bonus: Optional[float] = 0.0
    notes: Optional[str] = None


@dataclass
class AttendanceReport:
  

    rows: List[AttendanceRow] = field(default_factory=list)
    employee_name: Optional[str] = None
    report_month: Optional[date] = None

    # סיכומים חודשיים מצטברים
    total_hours: float = 0.0
    total_hours_100: float = 0.0
    total_hours_125: float = 0.0
    total_hours_150: float = 0.0
    total_shabbat_hours: Optional[float] = 0.0
    total_work_days: Optional[int] = 0

    # שדות אופציונליים נוספים
    company_name: Optional[str] = None
    employee_id: Optional[str] = None
    travel_expenses: Optional[float] = 0.0
    bonus: Optional[float] = 0.0
    hourly_rate: Optional[float] = 30.65
    total_payment: Optional[float] = 0.0
    notes: Optional[str] = None

    def recalculate_totals(self, is_type_b: bool = False) -> None:
        """
        מחשבת מחדש ומעדכנת באופן עקבי את כל סיכומי הדוח בהתבסס על שורות הנוכחות:
        - הפרדה מוחלטת בין שעות 150% (בימי חול) לבין שעות שבת.
        - התעלמות מימי חג ושבת בספירת ימי עבודה פעילים בסוג B.
        """
        if is_type_b:
            self.total_hours = round(sum(r.total_hours for r in self.rows if r.day_of_week != "שבת"), 2)
            self.total_hours_100 = self.total_hours
            self.total_hours_125 = 0.0
            self.total_hours_150 = 0.0
            self.total_shabbat_hours = 0.0
            self.total_work_days = len([r for r in self.rows if r.total_hours > 0 and r.day_of_week != "שבת"])
            rate = self.hourly_rate if (self.hourly_rate and self.hourly_rate > 0) else 30.65
            self.total_payment = round(self.total_hours * rate, 2)
        else:
            self.total_hours = round(sum(r.total_hours for r in self.rows), 2)
            self.total_hours_100 = round(sum(r.hours_100 for r in self.rows), 2)
            self.total_hours_125 = round(sum(r.hours_125 for r in self.rows), 2)
            self.total_hours_150 = round(sum(r.hours_150 for r in self.rows), 2)
            self.total_shabbat_hours = round(sum(r.shabbat_hours or 0.0 for r in self.rows), 2)
            self.total_work_days = len(self.rows)

    def summary(self) -> dict:
        """מחזירה מילון תמציתי של נתוני הדוח לצורכי תצוגה ודיבאג."""
        month_str = self.report_month.strftime("%m/%Y") if self.report_month else "לא צוין"
        return {
            "עובד": f"{self.employee_name or 'לא צוין'} ({self.employee_id or 'ללא מזהה'})",
            "מעסיק": self.company_name or "לא צוין",
            "חודש": month_str,
            "כמות שורות": len(self.rows),
            "ימי עבודה": self.total_work_days or 0,
            "סה\"כ שעות": f"{self.total_hours:.2f}",
            "שעות 100%": f"{self.total_hours_100:.2f}",
            "שעות 125%": f"{self.total_hours_125:.2f}",
            "שעות 150%": f"{self.total_hours_150:.2f}",
            "שעות שבת": f"{(self.total_shabbat_hours or 0.0):.2f}",
            "לתשלום": f"₪ {self.total_payment:,.2f}" if self.total_payment else "0.00",
        }
