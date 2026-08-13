"""
ETL Normaliser Module for Nifty 100 Financial Intelligence Platform.
Provides ticker normalisation and year label standardisation.
"""

import re
from typing import Union, Any


def normalize_ticker(val: Any) -> str:
    """
    Normalises NSE ticker string.
    - Strips whitespace
    - Converts to UPPERCASE
    - Preserves hyphens (BAJAJ-AUTO) and ampersands (M&M)
    - Returns empty string for None or empty inputs
    """
    if val is None:
        return ""
    s = str(val).strip()
    return s.upper()


def normalize_year(val: Any) -> str:
    """
    Standardises diverse financial year labels into uniform 'YYYY-MM' string.
    Supports formats:
      - 'Mar-23', 'Mar 23', 'March-2023', 'Mar-2023', 'Mar 2023', 'Mar 2023 15' -> '2023-03'
      - 'FY23', 'FY2023', '2023', 2023 -> '2023-03'
      - 'Dec-22', 'Dec 22', 'December-2022' -> '2022-12'
      - 'Jun-23', 'Jun 23', 'June-2023' -> '2023-06'
      - 'TTM' -> '2024-03'
      - '2023-03' -> '2023-03'
    Returns 'PARSE_ERROR' for invalid/unparseable values.
    """
    if val is None:
        return "PARSE_ERROR"

    s = str(val).strip()
    if not s:
        return "PARSE_ERROR"

    # Handle TTM
    if s.upper() == "TTM":
        return "2024-03"

    # 1. Check if already formatted as YYYY-MM
    if re.match(r"^\d{4}-\d{2}$", s):
        return s

    # Month map for short and full month names
    months = {
        "JAN": "01", "JANUARY": "01",
        "FEB": "02", "FEBRUARY": "02",
        "MAR": "03", "MARCH": "03",
        "APR": "04", "APRIL": "04",
        "MAY": "05",
        "JUN": "06", "JUNE": "06",
        "JUL": "07", "JULY": "07",
        "AUG": "08", "AUGUST": "08",
        "SEP": "09", "SEPT": "09", "SEPTEMBER": "09",
        "OCT": "10", "OCTOBER": "10",
        "NOV": "11", "NOVEMBER": "11",
        "DEC": "12", "DECEMBER": "12"
    }

    # Handle month string + year (e.g. 'Mar 2023', 'Mar 2023 15', 'Mar-23', 'March-2023', 'Mar 2016 9m')
    m_month_year = re.search(r"([A-Za-z]+)[\s\-]?(\d{4}|\d{2})", s)
    if m_month_year:
        month_str = m_month_year.group(1).upper()
        year_str = m_month_year.group(2)
        if month_str in months:
            mm = months[month_str]
            if len(year_str) == 2:
                yyyy = f"20{year_str}"
            else:
                yyyy = year_str
            return f"{yyyy}-{mm}"

    # Handle FY prefix: 'FY23', 'FY 23', 'FY2023', 'FY 2023'
    m_fy = re.search(r"FY[\s\-]?(\d{4}|\d{2})", s, re.IGNORECASE)
    if m_fy:
        year_str = m_fy.group(1)
        if len(year_str) == 2:
            yyyy = f"20{year_str}"
        else:
            yyyy = year_str
        return f"{yyyy}-03"

    # Handle integer or pure numeric year: '2023', 2023
    if re.match(r"^\d{4}$", s):
        return f"{s}-03"

    # Handle 2-digit year numeric: '23'
    if re.match(r"^\d{2}$", s):
        return f"20{s}-03"

    return "PARSE_ERROR"
