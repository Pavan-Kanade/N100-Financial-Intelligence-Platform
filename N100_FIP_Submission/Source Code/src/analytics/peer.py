"""
Peer Comparison Engine Module for Nifty 100 Financial Intelligence Platform.
Computes within-group percentile ranks across 11 peer groups and populates peer_percentiles SQLite table.
"""

import os
import sqlite3
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple


class PeerEngine:
    def __init__(self, db_path: str = "data/nifty100.db", schema_path: str = "db/schema.sql"):
        self.db_path = db_path
        self.schema_path = schema_path
        self.metrics_to_rank = [
            "return_on_equity_pct",
            "return_on_capital_employed_pct",
            "net_profit_margin_pct",
            "debt_to_equity",
            "free_cash_flow_cr",
            "pat_cagr_5yr",
            "revenue_cagr_5yr",
            "eps_cagr_5yr",
            "interest_coverage",
            "asset_turnover"
        ]

    def init_table(self, conn: sqlite3.Connection):
        """Creates peer_percentiles table if not exists."""
        with open(self.schema_path, "r", encoding="utf-8") as f:
            ddl = f.read()
        conn.executescript(ddl)

    def compute_percentiles(self, year: str = "2023-03") -> pd.DataFrame:
        """
        Computes intra-group percentile ranks for all 11 peer groups and populates SQLite.
        """
        conn = sqlite3.connect(self.db_path)

        self.init_table(conn)

        peers_df = pd.read_sql("SELECT * FROM peer_groups", conn)
        ratios_df = pd.read_sql(f"SELECT * FROM financial_ratios WHERE year='{year}'", conn)
        comp_df = pd.read_sql("SELECT id as company_id, company_name FROM companies", conn)

        if ratios_df.empty:
            max_yr = pd.read_sql("SELECT MAX(year) FROM financial_ratios", conn).iloc[0, 0]
            ratios_df = pd.read_sql(f"SELECT * FROM financial_ratios WHERE year='{max_yr}'", conn)

        # Merge peer mapping with financial ratios
        merged = pd.merge(peers_df, ratios_df, on="company_id", how="inner")
        merged = pd.merge(merged, comp_df, on="company_id", how="left")

        percentile_rows = []

        # Group by peer_group_name
        grouped = merged.groupby("peer_group_name")

        for group_name, group_data in grouped:
            n_members = len(group_data)

            for metric in self.metrics_to_rank:
                if metric not in group_data.columns:
                    continue

                for _, row in group_data.iterrows():
                    val = row.get(metric)
                    cid = row["company_id"]
                    yr = row.get("year", year)

                    pct_rank = None
                    if pd.notna(val):
                        # Extract valid metric values in this peer group
                        valid_vals = group_data[metric].dropna()

                        if len(valid_vals) <= 1:
                            pct_rank = 1.0
                        else:
                            # Standard PERCENT_RANK: count values <= val / (total - 1)
                            if metric == "debt_to_equity":
                                # Inverted for D/E: lower is better -> count values >= val
                                count_better = (valid_vals >= val).sum() - 1
                            else:
                                count_better = (valid_vals <= val).sum() - 1

                            pct_rank = round(float(count_better) / float(len(valid_vals) - 1), 4)

                    percentile_rows.append({
                        "company_id": cid,
                        "peer_group_name": group_name,
                        "metric": metric,
                        "value": val,
                        "percentile_rank": pct_rank,
                        "year": yr
                    })

        df_percentiles = pd.DataFrame(percentile_rows)

        # Populate SQLite table peer_percentiles
        conn.execute("DELETE FROM peer_percentiles;")
        df_percentiles.to_sql("peer_percentiles", conn, if_exists="append", index=False)
        conn.commit()
        conn.close()

        print(f"Populated peer_percentiles table with {len(df_percentiles)} records across 11 peer groups.")
        return df_percentiles

    def get_company_peer_info(self, company_id: str) -> Dict[str, Any]:
        """
        Retrieves peer group assignment and percentiles for a given company_id.
        Returns message 'No peer group assigned' if company is unmapped.
        """
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()

        pg_row = cur.execute("SELECT peer_group_name, is_benchmark FROM peer_groups WHERE company_id = ?", (company_id,)).fetchone()
        if not pg_row:
            conn.close()
            return {"status": "unmapped", "message": "No peer group assigned", "company_id": company_id}

        group_name, is_bench = pg_row
        pct_rows = cur.execute(
            "SELECT metric, value, percentile_rank FROM peer_percentiles WHERE company_id = ?", (company_id,)
        ).fetchall()
        conn.close()

        pct_map = {r[0]: {"value": r[1], "percentile_rank": r[2]} for r in pct_rows}
        return {
            "status": "mapped",
            "company_id": company_id,
            "peer_group_name": group_name,
            "is_benchmark": bool(is_bench),
            "percentiles": pct_map
        }


if __name__ == "__main__":
    engine = PeerEngine()
    engine.compute_percentiles()
