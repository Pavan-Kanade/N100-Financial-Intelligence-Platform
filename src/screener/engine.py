"""
Stock Screener Engine for Nifty 100 Financial Intelligence Platform.
Filters companies based on YAML configuration or custom metric thresholds,
handles sector carve-outs, and calculates composite quality scores.
"""

import os
import sqlite3
import yaml
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional


class ScreenerEngine:
    def __init__(self, db_path: str = "data/nifty100.db", config_path: str = "config/screener_config.yaml"):
        self.db_path = db_path
        self.config_path = config_path
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        if os.path.exists(self.config_path):
            with open(self.config_path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f)
        return {}

    def get_merged_dataset(self, year: str = "2023-03") -> pd.DataFrame:
        """
        Loads and merges financial_ratios, market_cap, companies, sectors, and profitandloss.
        """
        conn = sqlite3.connect(self.db_path)

        ratios_df = pd.read_sql(f"SELECT * FROM financial_ratios WHERE year='{year}'", conn)

        # Fallback to latest year if year has 0 rows
        if ratios_df.empty:
            max_yr = pd.read_sql("SELECT MAX(year) FROM financial_ratios", conn).iloc[0, 0]
            ratios_df = pd.read_sql(f"SELECT * FROM financial_ratios WHERE year='{max_yr}'", conn)

        comp_df = pd.read_sql("SELECT id as company_id, company_name, face_value, book_value FROM companies", conn)
        sec_df = pd.read_sql("SELECT company_id, broad_sector, sub_sector FROM sectors", conn)
        mcap_df = pd.read_sql("SELECT company_id, year, market_cap_crore, enterprise_value_crore, pe_ratio, pb_ratio, ev_ebitda, dividend_yield_pct FROM market_cap ORDER BY year ASC", conn)
        mcap_df = mcap_df.groupby("company_id").last().reset_index()

        pnl_df = pd.read_sql("SELECT company_id, year, sales, net_profit FROM profitandloss", conn)

        # Merge datasets
        df = pd.merge(ratios_df, comp_df, on="company_id", how="inner")
        df = pd.merge(df, sec_df, on="company_id", how="left")
        df = pd.merge(df, mcap_df[["company_id", "market_cap_crore", "enterprise_value_crore", "pe_ratio", "pb_ratio", "ev_ebitda", "dividend_yield_pct"]], on="company_id", how="left")

        # Merge sales & net_profit for sales/profit filters
        pnl_yr = df[["company_id", "year"]].merge(pnl_df, on=["company_id", "year"], how="left")
        df["sales"] = pnl_yr["sales"]
        df["net_profit"] = pnl_yr["net_profit"]

        conn.close()
        return df

    def apply_filters(self, df: pd.DataFrame, filters: Dict[str, Dict[str, float]]) -> pd.DataFrame:
        """
        Applies filter thresholds to DataFrame.
        Enforces:
          - D/E filter carve-out for Financials sector (when max_val > 0)
          - ICR 'Debt Free' bypass (always passes ICR min)
        """
        filtered = df.copy()

        for metric, bounds in filters.items():
            if metric not in filtered.columns:
                continue

            min_val = bounds.get("min")
            max_val = bounds.get("max")

            # 1. Special D/E Filter Handling with Financials Carve-out
            if metric == "debt_to_equity":
                is_financial = filtered["broad_sector"].astype(str).str.contains("Financial", case=False, na=False)
                meets_max = pd.Series(True, index=filtered.index)
                meets_min = pd.Series(True, index=filtered.index)

                if max_val is not None:
                    meets_max = filtered["debt_to_equity"].notnull() & (filtered["debt_to_equity"] <= max_val)
                if min_val is not None:
                    meets_min = filtered["debt_to_equity"].notnull() & (filtered["debt_to_equity"] >= min_val)

                if max_val is not None and max_val > 0:
                    filtered = filtered[is_financial | (meets_min & meets_max)]
                else:
                    filtered = filtered[meets_min & meets_max]

            # 2. Special ICR Filter Handling with Debt Free Bypass
            elif metric == "interest_coverage" and min_val is not None:
                is_debt_free = filtered["icr_label"] == "Debt Free"
                meets_icr = filtered["interest_coverage"].notnull() & (filtered["interest_coverage"] >= min_val)
                filtered = filtered[is_debt_free | meets_icr]

            # 3. Standard Numeric Min/Max Filtering
            else:
                if min_val is not None:
                    filtered = filtered[filtered[metric].notnull() & (filtered[metric] >= min_val)]
                if max_val is not None:
                    filtered = filtered[filtered[metric].notnull() & (filtered[metric] <= max_val)]

        # Recalculate sector-relative composite score for filtered set
        filtered["composite_quality_score"] = self.compute_sector_relative_composite(filtered)

        # Sort descending by composite quality score
        return filtered.sort_values(by="composite_quality_score", ascending=False).reset_index(drop=True)

    def compute_sector_relative_composite(self, df: pd.DataFrame) -> pd.Series:
        """
        Computes sector-relative composite quality score (0-100) using P10/P90 winsorisation.
        """
        if df.empty:
            return pd.Series(dtype=float)

        def winsorise_and_scale(s: pd.Series, ascending=True) -> pd.Series:
            clean = s.dropna()
            if clean.empty:
                return pd.Series(50.0, index=s.index)
            p10 = clean.quantile(0.10)
            p90 = clean.quantile(0.90)
            clipped = s.clip(lower=p10, upper=p90)
            if p90 == p10:
                return pd.Series(50.0, index=s.index)
            scaled = ((clipped - p10) / (p90 - p10)) * 100.0
            if not ascending:
                scaled = 100.0 - scaled
            return scaled.fillna(50.0)

        # Group by broad_sector and scale within sector
        roe_sc = df.groupby("broad_sector", group_keys=False)["return_on_equity_pct"].apply(winsorise_and_scale)
        fcf_sc = df.groupby("broad_sector", group_keys=False)["free_cash_flow_cr"].apply(winsorise_and_scale)
        gro_sc = df.groupby("broad_sector", group_keys=False)["revenue_cagr_5yr"].apply(winsorise_and_scale)
        de_sc = df.groupby("broad_sector", group_keys=False)["debt_to_equity"].apply(lambda s: winsorise_and_scale(s, ascending=False))

        comp = 0.35 * roe_sc + 0.30 * fcf_sc + 0.20 * gro_sc + 0.15 * de_sc
        return comp.round(2)

    def run_preset(self, preset_name: str, year: str = "2024-03") -> pd.DataFrame:
        """
        Executes a named preset screener.
        """
        presets = self.config.get("presets", {})
        if preset_name not in presets:
            raise ValueError(f"Unknown preset name: {preset_name}")

        filters = presets[preset_name].get("filters", {})
        df_base = self.get_merged_dataset(year)
        return self.apply_filters(df_base, filters)

    def run_all_presets(self, year: str = "2024-03") -> Dict[str, pd.DataFrame]:
        """
        Runs all 6 preset screeners and returns dictionary mapping preset_name -> DataFrame.
        """
        presets = self.config.get("presets", {})
        results = {}
        for p_name in presets.keys():
            results[p_name] = self.run_preset(p_name, year)
        return results
