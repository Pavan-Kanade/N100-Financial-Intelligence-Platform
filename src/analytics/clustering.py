"""
KMeans Clustering & Portfolio Profiling Module for Nifty 100 Financial Intelligence Platform.
Implements 5-cluster KMeans archetype assignment, sector median imputation, StandardScaler,
elbow plot, correlation heatmap, outlier detection, and portfolio statistics exports.
"""

import os
import sqlite3
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from typing import Tuple, Dict


class ClusterEngine:
    def __init__(self, db_path: str = "data/nifty100.db", output_dir: str = "output", reports_dir: str = "reports"):
        self.db_path = db_path
        self.output_dir = output_dir
        self.reports_dir = reports_dir
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(self.reports_dir, exist_ok=True)

        self.cluster_csv_path = os.path.join(self.output_dir, "cluster_labels.csv")
        self.outlier_csv_path = os.path.join(self.output_dir, "outlier_report.csv")
        self.stats_csv_path = os.path.join(self.output_dir, "portfolio_stats.csv")
        self.elbow_png_path = os.path.join(self.reports_dir, "elbow_plot.png")
        self.heatmap_png_path = os.path.join(self.reports_dir, "correlation_heatmap.png")

        self.feature_cols = [
            "return_on_equity_pct",
            "debt_to_equity",
            "revenue_cagr_5yr",
            "free_cash_flow_cr",
            "operating_profit_margin_pct"
        ]

        self.cluster_names_map = {
            0: "High-Quality Compounders",
            1: "Defensive Dividend Payers",
            2: "Value Cyclicals",
            3: "Distressed or Turnaround",
            4: "Emerging Growth"
        }

    def run(self, year: str = "2023-03") -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """
        Executes full clustering pipeline:
        1. Loads ratios & sector mapping
        2. Imputes missing values with sector median
        3. Scales features & runs KMeans(n_clusters=5, random_state=42)
        4. Exports elbow_plot.png, correlation_heatmap.png
        5. Exports cluster_labels.csv, outlier_report.csv, portfolio_stats.csv
        """
        conn = sqlite3.connect(self.db_path)

        comp_df = pd.read_sql("SELECT id as company_id, company_name FROM companies", conn)
        sec_df = pd.read_sql("SELECT company_id, broad_sector FROM sectors", conn)
        ratios_df = pd.read_sql(f"SELECT * FROM financial_ratios WHERE year='{year}'", conn)

        if ratios_df.empty:
            max_yr = pd.read_sql("SELECT MAX(year) FROM financial_ratios", conn).iloc[0, 0]
            ratios_df = pd.read_sql(f"SELECT * FROM financial_ratios WHERE year='{max_yr}'", conn)

        conn.close()

        df = pd.merge(comp_df, sec_df, on="company_id", how="inner")
        df = pd.merge(df, ratios_df, on="company_id", how="inner")

        # 1. Impute missing values with sector median
        for col in self.feature_cols:
            if col in df.columns:
                df[col] = df.groupby("broad_sector")[col].transform(lambda s: s.fillna(s.median()))
                df[col] = df[col].fillna(df[col].median()).fillna(0.0)

        X = df[self.feature_cols].copy()

        # 2. StandardScaler
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)

        # 3. Generate Elbow Plot (k from 2 to 10)
        inertias = []
        K_range = range(2, 11)
        for k in K_range:
            km_temp = KMeans(n_clusters=k, random_state=42, n_init=10)
            km_temp.fit(X_scaled)
            inertias.append(km_temp.inertia_)

        fig, ax = plt.subplots(figsize=(6, 4))
        ax.plot(K_range, inertias, "bo-", linewidth=2, markersize=8)
        ax.set_xlabel("Number of Clusters (k)", fontsize=10)
        ax.set_ylabel("Inertia", fontsize=10)
        ax.set_title("KMeans Elbow Curve (n_clusters=5)", fontsize=12, fontweight="bold")
        ax.grid(True, linestyle="--", alpha=0.5)
        plt.tight_layout()
        plt.savefig(self.elbow_png_path, dpi=150)
        plt.close(fig)
        print(f"Saved elbow plot to {self.elbow_png_path}")

        # 4. Fit final KMeans(n_clusters=5, random_state=42)
        kmeans = KMeans(n_clusters=5, random_state=42, n_init=10)
        cluster_labels = kmeans.fit_predict(X_scaled)
        centroids = kmeans.cluster_centers_

        df["cluster_id"] = cluster_labels
        df["cluster_name"] = df["cluster_id"].map(self.cluster_names_map)

        # Compute distance from centroid
        distances = []
        for i, row in enumerate(X_scaled):
            cid = cluster_labels[i]
            dist = np.linalg.norm(row - centroids[cid])
            distances.append(round(dist, 4))
        df["distance_from_centroid"] = distances

        # Export cluster_labels.csv
        export_cluster_cols = ["company_id", "company_name", "broad_sector", "cluster_id", "cluster_name", "distance_from_centroid"]
        df_clusters = df[export_cluster_cols].copy()
        df_clusters.to_csv(self.cluster_csv_path, index=False)
        print(f"Exported cluster labels for {len(df_clusters)} companies to {self.cluster_csv_path}")

        # 5. Correlation Heatmap
        kpi_cols = [
            "return_on_equity_pct", "return_on_capital_employed_pct", "net_profit_margin_pct",
            "debt_to_equity", "free_cash_flow_cr", "revenue_cagr_5yr", "pat_cagr_5yr",
            "eps_cagr_5yr", "interest_coverage", "asset_turnover"
        ]
        corr_cols = [c for c in kpi_cols if c in df.columns]
        df_corr = df[corr_cols].corr()

        fig, ax = plt.subplots(figsize=(8, 6))
        sns.heatmap(df_corr, annot=True, fmt=".2f", cmap="coolwarm", cbar=True, ax=ax, annot_kws={"size": 7})
        ax.set_title("10 KPI Pearson Correlation Heatmap", fontsize=11, fontweight="bold")
        plt.tight_layout()
        plt.savefig(self.heatmap_png_path, dpi=150)
        plt.close(fig)
        print(f"Saved correlation heatmap to {self.heatmap_png_path}")

        # 6. Outlier Detection (Z-score > 3 per broad sector)
        outliers = []
        for sector, grp in df.groupby("broad_sector"):
            for col in corr_cols:
                vals = grp[col].dropna()
                if len(vals) > 3 and vals.std() > 0:
                    z_scores = (grp[col] - vals.mean()) / vals.std()
                    for idx, z in z_scores.items():
                        if abs(z) > 3.0:
                            outliers.append({
                                "company_id": df.loc[idx, "company_id"],
                                "broad_sector": sector,
                                "metric": col,
                                "value": df.loc[idx, col],
                                "z_score": round(z, 2)
                            })

        df_outliers = pd.DataFrame(outliers)
        if df_outliers.empty:
            df_outliers = pd.DataFrame(columns=["company_id", "broad_sector", "metric", "value", "z_score"])
        df_outliers.to_csv(self.outlier_csv_path, index=False)
        print(f"Exported {len(df_outliers)} outlier records to {self.outlier_csv_path}")

        # 7. Portfolio Statistics (P10, P25, P50, P75, P90, Mean, Std)
        stats_rows = []
        for col in corr_cols:
            s = df[col].dropna()
            if not s.empty:
                stats_rows.append({
                    "metric": col,
                    "count": len(s),
                    "mean": round(s.mean(), 2),
                    "std": round(s.std(), 2),
                    "P10": round(s.quantile(0.10), 2),
                    "P25": round(s.quantile(0.25), 2),
                    "P50_median": round(s.median(), 2),
                    "P75": round(s.quantile(0.75), 2),
                    "P90": round(s.quantile(0.90), 2)
                })

        df_stats = pd.DataFrame(stats_rows)
        df_stats.to_csv(self.stats_csv_path, index=False)
        print(f"Exported portfolio stats to {self.stats_csv_path}")

        return df_clusters, df_outliers, df_stats


if __name__ == "__main__":
    eng = ClusterEngine()
    eng.run()
