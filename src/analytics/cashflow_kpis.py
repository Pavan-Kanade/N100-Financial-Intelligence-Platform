"""
Cash Flow KPIs & Capital Allocation Classifier Module for Nifty 100 Financial Intelligence Platform.
"""

from typing import Optional, Tuple, Any, List


def compute_free_cash_flow(operating_activity: Any, investing_activity: Any) -> Optional[float]:
    """
    Computes Free Cash Flow (Cr): operating_activity + investing_activity.
    Negative values allowed.
    """
    if operating_activity is None:
        return None
    try:
        cfo = float(operating_activity)
        cfi = float(investing_activity) if investing_activity is not None else 0.0
        return round(cfo + cfi, 2)
    except (ValueError, TypeError):
        return None


def compute_cfo_quality_score(cfo_list: List[float], pat_list: List[float]) -> Tuple[Optional[float], Optional[str]]:
    """
    Computes CFO Quality Score: CFO / PAT ratio averaged over available years (up to 5 years).
    Returns (score, category):
      - > 1.0: 'High Quality'
      - 0.5 - 1.0: 'Moderate'
      - < 0.5: 'Accrual Risk'
    """
    if not cfo_list or not pat_list or len(cfo_list) != len(pat_list):
        return None, None

    ratios = []
    for cfo, pat in zip(cfo_list[-5:], pat_list[-5:]):
        try:
            cfo_v = float(cfo)
            pat_v = float(pat)
            if pat_v != 0:
                ratios.append(cfo_v / pat_v)
        except (ValueError, TypeError):
            continue

    if not ratios:
        return None, None

    avg_score = round(sum(ratios) / len(ratios), 4)

    if avg_score > 1.0:
        cat = "High Quality"
    elif avg_score >= 0.5:
        cat = "Moderate"
    else:
        cat = "Accrual Risk"

    return avg_score, cat


def compute_capex_intensity(investing_activity: Any, sales: Any) -> Tuple[Optional[float], Optional[str]]:
    """
    Computes CapEx Intensity (%): abs(investing_activity) / sales * 100.
    Returns (intensity_pct, category):
      - < 3%: 'Asset Light'
      - 3% - 8%: 'Moderate'
      - > 8%: 'Capital Intensive'
    """
    if investing_activity is None or sales is None:
        return None, None
    try:
        cfi_val = float(investing_activity)
        sales_val = float(sales)
        if sales_val <= 0:
            return None, None
        intensity = round((abs(cfi_val) / sales_val) * 100.0, 4)

        if intensity < 3.0:
            cat = "Asset Light"
        elif intensity <= 8.0:
            cat = "Moderate"
        else:
            cat = "Capital Intensive"

        return intensity, cat
    except (ValueError, TypeError):
        return None, None


def compute_fcf_conversion_rate(fcf: Any, operating_profit: Any) -> Optional[float]:
    """
    Computes FCF Conversion Rate (%): (FCF / operating_profit) * 100.
    Returns None if operating_profit == 0.
    """
    if fcf is None or operating_profit is None:
        return None
    try:
        fcf_val = float(fcf)
        op_val = float(operating_profit)
        if op_val == 0:
            return None
        return round((fcf_val / op_val) * 100.0, 4)
    except (ValueError, TypeError):
        return None


def classify_capital_allocation(
    cfo: Any, cfi: Any, cff: Any, cfo_pat_ratio: Optional[float] = None
) -> Tuple[str, str, str, str]:
    """
    Classifies capital allocation pattern based on signs of (CFO, CFI, CFF).
    Returns (cfo_sign, cfi_sign, cff_sign, pattern_label).

    Patterns:
      - (+, -, -) & cfo_pat_ratio > 1.0 -> Shareholder Returns
      - (+, -, -) default -> Reinvestor
      - (+, +, -) -> Liquidating Assets
      - (-, +, +) -> Distress Signal
      - (-, -, +) -> Growth Funded by Debt
      - (+, +, +) -> Cash Accumulator
      - (-, -, -) -> Pre-Revenue
      - (+, -, +) -> Mixed
    """
    try:
        cfo_v = float(cfo) if cfo is not None else 0.0
        cfi_v = float(cfi) if cfi is not None else 0.0
        cff_v = float(cff) if cff is not None else 0.0
    except (ValueError, TypeError):
        cfo_v, cfi_v, cff_v = 0.0, 0.0, 0.0

    cfo_sign = "+" if cfo_v >= 0 else "-"
    cfi_sign = "+" if cfi_v >= 0 else "-"
    cff_sign = "+" if cff_v >= 0 else "-"

    pattern = (cfo_sign, cfi_sign, cff_sign)

    if pattern == ("+", "-", "-"):
        if cfo_pat_ratio is not None and cfo_pat_ratio > 1.0:
            label = "Shareholder Returns"
        else:
            label = "Reinvestor"
    elif pattern == ("+", "+", "-"):
        label = "Liquidating Assets"
    elif pattern == ("-", "+", "+"):
        label = "Distress Signal"
    elif pattern == ("-", "-", "+"):
        label = "Growth Funded by Debt"
    elif pattern == ("+", "+", "+"):
        label = "Cash Accumulator"
    elif pattern == ("-", "-", "-"):
        label = "Pre-Revenue"
    else:
        label = "Mixed"

    return cfo_sign, cfi_sign, cff_sign, label
