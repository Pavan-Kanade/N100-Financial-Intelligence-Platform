"""
Analysis Text Parser Module for Nifty 100 Financial Intelligence Platform.
Parses qualitative text fields in analysis table using regex pattern: (\\d+)\\s*Years?:?\\s*([\\d.]+)%
Cross-validates parsed values against computed financial ratios and logs parse failures.
"""

import os
import re
import sqlite3
import pandas as pd
from typing import Dict, List, Tuple


class AnalysisTextParser:
    def __init__(self, db_path: str = "data/nifty100.db", output_dir: str = "output"):
        self.db_path = db_path
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        self.parsed_csv_path = os.path.join(self.output_dir, "analysis_parsed.csv")
        self.failures_csv_path = os.path.join(self.output_dir, "parse_failures.csv")
        self.pattern = re.compile(r"(\d+)\s*Years?:?\s*([\d.]+)%", re.IGNORECASE)

    def parse(self) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Parses analysis table columns: compounded_sales_growth, compounded_profit_growth,
        stock_price_cagr, roe. Cross-validates against financial_ratios table.
        """
        conn = sqlite3.connect(self.db_path)

        analysis_df = pd.read_sql("SELECT * FROM analysis", conn)
        ratios_df = pd.read_sql("SELECT * FROM financial_ratios WHERE year='2023-03'", conn)

        conn.close()

        target_columns = [
            "compounded_sales_growth",
            "compounded_profit_growth",
            "stock_price_cagr",
            "roe"
        ]

        parsed_rows = []
        failure_rows = []

        for _, row in analysis_df.iterrows():
            cid = row["company_id"]

            for col in target_columns:
                text_val = row.get(col)
                if pd.isna(text_val) or not str(text_val).strip():
                    continue

                lines = str(text_val).split("\n")

                for line in lines:
                    line_clean = line.strip()
                    if not line_clean:
                        continue

                    match = self.pattern.search(line_clean)
                    if match:
                        period_yrs = int(match.group(1))
                        val_pct = float(match.group(2))

                        parsed_rows.append({
                            "company_id": cid,
                            "metric_type": col,
                            "period_years": period_yrs,
                            "value_pct": val_pct,
                            "raw_text": line_clean
                        })
                    else:
                        failure_rows.append({
                            "company_id": cid,
                            "column": col,
                            "raw_text": line_clean,
                            "reason": "Regex pattern mismatch"
                        })

        df_parsed = pd.DataFrame(parsed_rows)
        df_failures = pd.DataFrame(failure_rows)

        # Cross-validate parsed CAGRs against computed financial_ratios
        if not df_parsed.empty and not ratios_df.empty:
            divergences = []
            for _, p_row in df_parsed.iterrows():
                cid = p_row["company_id"]
                mtype = p_row["metric_type"]
                yrs = p_row["period_years"]
                parsed_val = p_row["value_pct"]

                comp_match = ratios_df[ratios_df["company_id"] == cid]
                if not comp_match.empty:
                    comp_row = comp_match.iloc[0]
                    target_ratio_col = None
                    if mtype == "compounded_sales_growth" and yrs == 5:
                        target_ratio_col = "revenue_cagr_5yr"
                    elif mtype == "compounded_profit_growth" and yrs == 5:
                        target_ratio_col = "pat_cagr_5yr"
                    elif mtype == "roe" and yrs == 5:
                        target_ratio_col = "return_on_equity_pct"

                    if target_ratio_col and target_ratio_col in comp_row:
                        calc_val = comp_row[target_ratio_col]
                        if pd.notna(calc_val):
                            diff = abs(parsed_val - float(calc_val))
                            if diff > 5.0:
                                divergences.append({
                                    "company_id": cid,
                                    "metric": target_ratio_col,
                                    "parsed_val": parsed_val,
                                    "calc_val": calc_val,
                                    "divergence_pct": round(diff, 2)
                                })

            if divergences:
                df_div = pd.DataFrame(divergences)
                df_div.to_csv(os.path.join(self.output_dir, "cagr_divergences.csv"), index=False)
                print(f"Logged {len(df_div)} CAGR divergence entries (>5%) to output/cagr_divergences.csv")

        # Save CSV outputs
        df_parsed.to_csv(self.parsed_csv_path, index=False)
        df_failures.to_csv(self.failures_csv_path, index=False)

        print(f"Parsed {len(df_parsed)} metric entries -> {self.parsed_csv_path}")
        print(f"Logged {len(df_failures)} parse failures -> {self.failures_csv_path}")

        return df_parsed, df_failures


if __name__ == "__main__":
    parser = AnalysisTextParser()
    parser.parse()
