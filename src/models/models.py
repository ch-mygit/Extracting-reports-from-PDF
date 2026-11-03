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
