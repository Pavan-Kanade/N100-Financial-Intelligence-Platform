"""
Financial Ratios Module for Nifty 100 Financial Intelligence Platform.
Implements Profitability, Leverage, and Efficiency ratios with edge-case handling.
"""

from typing import Optional, Tuple, Any


# ==============================================================================
# Profitability Ratios
# ==============================================================================

def compute_net_profit_margin(net_profit: Any, sales: Any) -> Optional[float]:
    """
    Computes Net Profit Margin (%): (net_profit / sales) * 100.
    Returns None if sales is 0 or invalid/missing.
    """
    if net_profit is None or sales is None:
        return None
    try:
        np_val = float(net_profit)
        sales_val = float(sales)
        if sales_val == 0:
            return None
        return round((np_val / sales_val) * 100.0, 4)
    except (ValueError, TypeError):
        return None


def compute_operating_profit_margin(operating_profit: Any, sales: Any) -> Optional[float]:
    """
    Computes Operating Profit Margin (%): (operating_profit / sales) * 100.
    Returns None if sales is 0 or invalid/missing.
    """
    if operating_profit is None or sales is None:
        return None
    try:
        op_val = float(operating_profit)
        sales_val = float(sales)
        if sales_val == 0:
            return None
        return round((op_val / sales_val) * 100.0, 4)
    except (ValueError, TypeError):
        return None


def compute_return_on_equity(net_profit: Any, equity_capital: Any, reserves: Any) -> Optional[float]:
    """
    Computes Return on Equity (%): (net_profit / (equity_capital + reserves)) * 100.
    Returns None if equity_capital + reserves <= 0 (negative/zero total equity).
    """
    if net_profit is None or equity_capital is None:
        return None
    try:
        np_val = float(net_profit)
        eq_val = float(equity_capital)
        res_val = float(reserves) if reserves is not None else 0.0
        total_equity = eq_val + res_val
        if total_equity <= 0:
            return None
        return round((np_val / total_equity) * 100.0, 4)
    except (ValueError, TypeError):
        return None


def compute_return_on_capital_employed(
    operating_profit: Any, depreciation: Any, equity_capital: Any, reserves: Any, borrowings: Any
) -> Optional[float]:
    """
    Computes Return on Capital Employed (%): (EBIT / (equity + reserves + borrowings)) * 100.
    EBIT = operating_profit - depreciation.
    Returns None if total capital employed <= 0.
    """
    if operating_profit is None or equity_capital is None:
        return None
    try:
        op_val = float(operating_profit)
        dep_val = float(depreciation) if depreciation is not None else 0.0
        ebit = op_val - dep_val

        eq_val = float(equity_capital)
        res_val = float(reserves) if reserves is not None else 0.0
        bor_val = float(borrowings) if borrowings is not None else 0.0

        capital_employed = eq_val + res_val + bor_val
        if capital_employed <= 0:
            return None
        return round((ebit / capital_employed) * 100.0, 4)
    except (ValueError, TypeError):
        return None


def compute_return_on_assets(net_profit: Any, total_assets: Any) -> Optional[float]:
    """
    Computes Return on Assets (%): (net_profit / total_assets) * 100.
    Returns None if total_assets <= 0.
    """
    if net_profit is None or total_assets is None:
        return None
    try:
        np_val = float(net_profit)
        ta_val = float(total_assets)
        if ta_val <= 0:
            return None
        return round((np_val / ta_val) * 100.0, 4)
    except (ValueError, TypeError):
        return None


# ==============================================================================
# Leverage Ratios
# ==============================================================================

def compute_debt_to_equity(borrowings: Any, equity_capital: Any, reserves: Any) -> Optional[float]:
    """
    Computes Debt-to-Equity Ratio: borrowings / (equity_capital + reserves).
    Returns 0.0 if borrowings == 0 (debt-free).
    Returns None if total equity <= 0.
    """
    if borrowings is None or equity_capital is None:
        return None
    try:
        bor_val = float(borrowings)
        eq_val = float(equity_capital)
        res_val = float(reserves) if reserves is not None else 0.0
        total_equity = eq_val + res_val

        if bor_val == 0:
            return 0.0
        if total_equity <= 0:
            return None
        return round(bor_val / total_equity, 4)
    except (ValueError, TypeError):
        return None


def check_high_leverage_flag(de_ratio: Optional[float], broad_sector: str) -> bool:
    """
    Sets high_leverage_flag = True if D/E > 5 and company is NOT in Financials sector.
    """
    if de_ratio is None:
        return False
    if "Financial" in str(broad_sector):
        return False
    return de_ratio > 5.0


def compute_interest_coverage(operating_profit: Any, other_income: Any, interest: Any) -> Optional[float]:
    """
    Computes Interest Coverage Ratio: (operating_profit + other_income) / interest.
    Returns None if interest == 0 or interest is None/missing.
    """
    if interest is None or operating_profit is None:
        return None
    try:
        int_val = float(interest)
        if int_val <= 0:
            return None
        op_val = float(operating_profit)
        oi_val = float(other_income) if other_income is not None else 0.0
        return round((op_val + oi_val) / int_val, 4)
    except (ValueError, TypeError):
        return None


def get_icr_label_and_warning(
    icr_val: Optional[float], interest: Any
) -> Tuple[Optional[str], bool]:
    """
    Returns (icr_label, icr_warning_flag).
    - If interest == 0 or interest is None/missing -> icr_label = 'Debt Free'
    - If icr_val < 1.5 (and not None) -> icr_warning_flag = True
    """
    label = None
    warning_flag = False

    try:
        int_val = float(interest) if interest is not None else 0.0
        if int_val == 0:
            label = "Debt Free"
    except (ValueError, TypeError):
        label = "Debt Free"

    if icr_val is not None and icr_val < 1.5:
        warning_flag = True

    return label, warning_flag


def compute_net_debt(borrowings: Any, investments: Any) -> Optional[float]:
    """
    Computes Net Debt (Cr): borrowings - investments.
    Uses investments as liquid asset proxy.
    """
    if borrowings is None:
        return None
    try:
        bor_val = float(borrowings)
        inv_val = float(investments) if investments is not None else 0.0
        return round(bor_val - inv_val, 2)
    except (ValueError, TypeError):
        return None


# ==============================================================================
# Efficiency Ratios
# ==============================================================================

def compute_asset_turnover(sales: Any, total_assets: Any) -> Optional[float]:
    """
    Computes Asset Turnover: sales / total_assets.
    Returns None if total_assets <= 0.
    """
    if sales is None or total_assets is None:
        return None
    try:
        sales_val = float(sales)
        ta_val = float(total_assets)
        if ta_val <= 0:
            return None
        return round(sales_val / ta_val, 4)
    except (ValueError, TypeError):
        return None
