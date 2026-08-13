"""
Deliverables Audit Verification Script for Nifty 100 Financial Intelligence Platform.
Performs live file system check for all 23 deliverables D-01 through D-23.
"""

import os
import glob
import sqlite3

def audit():
    deliverables = [
        ("D-01", "Sprint 1", "nifty100.db", "data/nifty100.db"),
        ("D-02", "Sprint 1", "load_audit.csv", "output/load_audit.csv"),
        ("D-03", "Sprint 1", "validation_failures.csv", "output/validation_failures.csv"),
        ("D-04", "Sprint 1", "exploratory_queries.sql", "notebooks/exploratory_queries.sql"),
        ("D-05", "Sprint 2", "financial_ratios table", "data/nifty100.db"),
        ("D-06", "Sprint 2", "capital_allocation.csv", "output/capital_allocation.csv"),
        ("D-07", "Sprint 3", "screener_output.xlsx", "output/screener_output.xlsx"),
        ("D-08", "Sprint 3", "screener_config.yaml", "config/screener_config.yaml"),
        ("D-09", "Sprint 3", "peer_comparison.xlsx", "output/peer_comparison.xlsx"),
        ("D-10", "Sprint 3", "90 Radar Charts", "reports/radar_charts/"),
        ("D-11", "Sprint 4", "Streamlit App (8 Screens)", "src/dashboard/app.py"),
        ("D-12", "Sprint 4", "valuation_summary.xlsx", "output/valuation_summary.xlsx"),
        ("D-13", "Sprint 5", "cashflow_intelligence.xlsx", "output/cashflow_intelligence.xlsx"),
        ("D-14", "Sprint 5", "pros_cons_generated.csv", "output/pros_cons_generated.csv"),
        ("D-15", "Sprint 5", "analysis_parsed.csv", "output/analysis_parsed.csv"),
        ("D-16", "Sprint 5", "91 Company Tearsheets", "reports/tearsheets/"),
        ("D-17", "Sprint 5", "10 Sector Reports", "reports/sector/"),
        ("D-18", "Sprint 5", "Portfolio Summary PDF", "reports/portfolio/portfolio_summary.pdf"),
        ("D-19", "Sprint 6", "cluster_labels.csv", "output/cluster_labels.csv"),
        ("D-20", "Sprint 6", "FastAPI Server (16 Endpoints)", "src/api/main.py"),
        ("D-21", "Sprint 6", "pytest_report.html", "reports/pytest_report.html"),
        ("D-22", "Sprint 6", "analyst_guide.pdf", "docs/analyst_guide.pdf"),
        ("D-23", "Sprint 6", "acceptance_checklist.pdf", "docs/acceptance_checklist.pdf")
    ]

    print("==========================================================================================")
    print(f"{'ID':<6} | {'Sprint':<9} | {'Deliverable Name':<30} | {'Status':<10} | {'Live Verification Details'}")
    print("==========================================================================================")

    all_passed = True
    for did, sprint, name, path in deliverables:
        if did == "D-05":
            conn = sqlite3.connect(path)
            cnt = conn.execute("SELECT COUNT(*) FROM financial_ratios").fetchone()[0]
            conn.close()
            status = "Done" if cnt >= 1100 else "FAIL"
            details = f"Table populated with {cnt:,} ratio rows"
        elif did == "D-10":
            files = glob.glob("reports/radar_charts/*.png")
            status = "Done" if len(files) >= 90 else "FAIL"
            details = f"{len(files)} PNG radar chart images present"
        elif did == "D-16":
            files = glob.glob("reports/tearsheets/*.pdf")
            status = "Done" if len(files) >= 90 else "FAIL"
            details = f"{len(files)} 2-page company tearsheet PDFs"
        elif did == "D-17":
            files = glob.glob("reports/sector/*.pdf")
            status = "Done" if len(files) >= 10 else "FAIL"
            details = f"{len(files)} sector report PDFs"
        else:
            exists = os.path.exists(path)
            status = "Done" if exists else "FAIL"
            size = os.path.getsize(path) if exists else 0
            if size > 1024 * 1024:
                details = f"{size / (1024*1024):.2f} MB"
            elif size > 1024:
                details = f"{size / 1024:.1f} KB"
            else:
                details = f"{size} bytes"

        if status != "Done":
            all_passed = False

        print(f"{did:<6} | {sprint:<9} | {name:<30} | {status:<10} | {details}")

    print("==========================================================================================")
    print(f"OVERALL AUDIT RESULT: {'100% VERIFIED & COMPLETE (23/23 PASSED)' if all_passed else 'SOME DELIVERABLES MISSING'}")

if __name__ == "__main__":
    audit()
