"""
CAGR Analytics Engine Module for Nifty 100 Financial Intelligence Platform.
Implements multi-period CAGR calculations with 6 edge-case flag handlers.
"""

import math
from typing import Optional, Tuple, Any, List


def calculate_cagr(
    start_val: Any, end_val: Any, n_years: int
) -> Tuple[Optional[float], str]:
    """
    Calculates Compound Annual Growth Rate (%): ((end / start) ** (1 / n_years) - 1) * 100.
    Enforces all 6 CAGR edge-case conditions:
      1. start > 0 and end > 0: Returns (cagr_val, 'NORMAL')
      2. start > 0 and end < 0: Returns (None, 'DECLINE_TO_LOSS')
      3. start < 0 and end > 0: Returns (None, 'TURNAROUND')
      4. start < 0 and end < 0: Returns (None, 'BOTH_NEGATIVE')
      5. start == 0: Returns (None, 'ZERO_BASE')
      6. Invalid/missing inputs or n_years < 1: Returns (None, 'INSUFFICIENT')
    """
    if start_val is None or end_val is None or n_years is None or n_years < 1:
        return None, "INSUFFICIENT"

    try:
        s = float(start_val)
        e = float(end_val)
    except (ValueError, TypeError):
        return None, "INSUFFICIENT"

    if s == 0:
        return None, "ZERO_BASE"

    if s > 0 and e > 0:
        cagr = ((e / s) ** (1.0 / float(n_years)) - 1.0) * 100.0
        return round(cagr, 4), "NORMAL"

    if s > 0 and e < 0:
        return None, "DECLINE_TO_LOSS"

    if s < 0 and e > 0:
        return None, "TURNAROUND"

    if s < 0 and e < 0:
        return None, "BOTH_NEGATIVE"

    return None, "INSUFFICIENT"


def calculate_series_cagr(
    year_val_tuples: List[Tuple[str, float]], n_years: int
) -> Tuple[Optional[float], str]:
    """
    Given a sorted list of (year_str, metric_val) for a company, computes CAGR over n_years.
    Expects year_val_tuples to be sorted by year ASC.
    """
    if not year_val_tuples or len(year_val_tuples) <= n_years:
        return None, "INSUFFICIENT"

    # Take end point as the latest available year (last item)
    end_year, end_val = year_val_tuples[-1]

    # Target start year index: -1 - n_years
    start_idx = -1 - n_years
    if abs(start_idx) > len(year_val_tuples):
        return None, "INSUFFICIENT"

    start_year, start_val = year_val_tuples[start_idx]

    return calculate_cagr(start_val, end_val, n_years)
