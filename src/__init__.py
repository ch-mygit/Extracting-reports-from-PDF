"""
חבילת מערכת עיבוד, טרנספורמציה והפקת דוחות נוכחות חודשיים.
"""

from .models import AttendanceReport, AttendanceRow
from .parsers import BaseParser, TypeAParser, TypeBParser
from .strategies import (
    BaseTransformationStrategy,
    TypeATransformationStrategy,
    TypeBTransformationStrategy,
    transform_type_a_report,
    transform_type_b_report,
)
from .ocr import (
    extract_raw_text_from_pdf,
    classify_report,
    classify_report_detailed,
    ReportType,
)
from .generation import PDFBuilder
from .generation.generator import SyntheticReportGenerator
from .utils import TerminalUI

__all__ = [
    "AttendanceReport",
    "AttendanceRow",
    "BaseParser",
    "TypeAParser",
    "TypeBParser",
    "BaseTransformationStrategy",
    "TypeATransformationStrategy",
    "TypeBTransformationStrategy",
    "transform_type_a_report",
    "transform_type_b_report",
    "extract_raw_text_from_pdf",
    "classify_report",
    "classify_report_detailed",
    "ReportType",
    "PDFBuilder",
    "SyntheticReportGenerator",
    "TerminalUI",
]
