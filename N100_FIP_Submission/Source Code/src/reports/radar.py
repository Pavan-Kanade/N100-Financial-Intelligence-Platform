"""
Radar Chart Generator Module for Nifty 100 Financial Intelligence Platform.
Generates 8-axis PNG polar radar charts with peer group average overlays saved to reports/radar_charts/.
"""

import os
import sqlite3
import numpy as np
import matplotlib
matplotlib.use("Agg")  # Non-interactive backend
import matplotlib.pyplot as plt
import pandas as pd
from typing import Dict, List, Optional


class RadarChartGenerator:
    def __init__(self, db_path: str = "data/nifty100.db", output_dir: str = "reports/radar_charts"):
        self.db_path = db_path
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        self.axes_labels = [
            "ROE", "ROCE", "NPM", "D/E", "FCF", "PAT CAGR 5Y", "Rev CAGR 5Y", "Composite Score"
        ]

    def generate_all_charts(self, year: str = "2023-03"):
        """
        Generates radar PNG charts for all companies in nifty100.db.
        """
        conn = sqlite3.connect(self.db_path)

        peers_df = pd.read_sql("SELECT * FROM peer_groups", conn)
        ratios_df = pd.read_sql(f"SELECT * FROM financial_ratios WHERE year='{year}'", conn)
        comp_df = pd.read_sql("SELECT id as company_id, company_name FROM companies", conn)

        if ratios_df.empty:
            max_yr = pd.read_sql("SELECT MAX(year) FROM financial_ratios", conn).iloc[0, 0]
            ratios_df = pd.read_sql(f"SELECT * FROM financial_ratios WHERE year='{max_yr}'", conn)

        merged = pd.merge(ratios_df, comp_df, on="company_id", how="inner")
        merged = pd.merge(merged, peers_df, on="company_id", how="left")

        # Map metrics to 0-100 scale for radar axes
        metrics = [
            "return_on_equity_pct", "return_on_capital_employed_pct", "net_profit_margin_pct",
            "debt_to_equity", "free_cash_flow_cr", "pat_cagr_5yr", "revenue_cagr_5yr", "composite_quality_score"
        ]

        # Normalise metrics 0-100 for radar rendering
        norm_df = merged.copy()
        for m in metrics:
            if m in norm_df.columns:
                s = norm_df[m].fillna(0.0)
                p10, p90 = s.quantile(0.10), s.quantile(0.90)
                if p90 == p10:
                    norm_df[m + "_norm"] = 50.0
                else:
                    clipped = s.clip(lower=p10, upper=p90)
                    scaled = ((clipped - p10) / (p90 - p10)) * 100.0
                    if m == "debt_to_equity":
                        scaled = 100.0 - scaled
                    norm_df[m + "_norm"] = scaled

        norm_cols = [m + "_norm" for m in metrics]

        # Group by peer group to compute group average
        peer_groups = norm_df.groupby("peer_group_name")
        peer_avg_map = {}
        for pg_name, group_data in peer_groups:
            peer_avg_map[pg_name] = group_data[norm_cols].mean().values

        count = 0
        for _, row in norm_df.iterrows():
            cid = row["company_id"]
            cname = row.get("company_name", cid)
            pg_name = row.get("peer_group_name")

            comp_vals = row[norm_cols].values.astype(float)
            peer_avg_vals = peer_avg_map.get(pg_name) if pg_name in peer_avg_map else None

            self.create_radar_chart(cid, cname, comp_vals, peer_avg_vals, pg_name)
            count += 1

        conn.close()
        print(f"Generated {count} radar PNG charts in {self.output_dir}/")

    def create_radar_chart(
        self,
        company_id: str,
        company_name: str,
        comp_vals: np.ndarray,
        peer_avg_vals: Optional[np.ndarray],
        peer_group_name: Optional[str]
    ):
        """
        Creates a single polar radar chart PNG file for a company.
        """
        num_vars = len(self.axes_labels)
        angles = np.linspace(0, 2 * np.pi, num_vars, endpoint=False).tolist()

        # Complete the loop
        comp_vals_loop = np.concatenate((comp_vals, [comp_vals[0]]))
        angles_loop = angles + [angles[0]]

        fig, ax = plt.subplots(figsize=(6, 6), subplot_kw=dict(polar=True))

        # Draw company polygon
        ax.plot(angles_loop, comp_vals_loop, color="#1F4E78", linewidth=2, label=company_id)
        ax.fill(angles_loop, comp_vals_loop, color="#1F4E78", alpha=0.25)

        # Draw peer average if available
        if peer_avg_vals is not None:
            peer_loop = np.concatenate((peer_avg_vals, [peer_avg_vals[0]]))
            ax.plot(angles_loop, peer_loop, color="#D9534F", linewidth=1.5, linestyle="--", label=f"Peer Avg ({peer_group_name})")

        # Set category labels
        ax.set_xticks(angles)
        ax.set_xticklabels(self.axes_labels, size=9, fontweight="bold")

        # Set radial bounds & grid
        ax.set_ylim(0, 100)
        ax.set_yticks([25, 50, 75, 100])
        ax.set_yticklabels(["25", "50", "75", "100"], color="gray", size=8)

        title = f"{company_name} ({company_id})\nPerformance vs {peer_group_name if peer_group_name else 'Nifty 100'}"
        ax.set_title(title, size=11, fontweight="bold", pad=20)
        ax.legend(loc="upper right", bbox_to_anchor=(1.2, 1.1), fontsize=8)

        plt.tight_layout()
        out_file = os.path.join(self.output_dir, f"{company_id}_radar.png")
        plt.savefig(out_file, dpi=150, bbox_inches="tight")
        plt.close(fig)


if __name__ == "__main__":
    gen = RadarChartGenerator()
    gen.generate_all_charts()
