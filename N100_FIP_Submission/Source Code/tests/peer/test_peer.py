"""
Unit tests for Peer Comparison Engine (src/analytics/peer.py).
Tests percentiles calculation, D/E inversion, unmapped company message, and database population.
"""

import pytest
import sqlite3
import pandas as pd
from src.analytics.peer import PeerEngine


@pytest.fixture(scope="module")
def peer_engine():
    engine = PeerEngine()
    engine.compute_percentiles()
    return engine


def test_peer_percentiles_populated(peer_engine):
    conn = sqlite3.connect(peer_engine.db_path)
    count = conn.execute("SELECT COUNT(*) FROM peer_percentiles").fetchone()[0]
    conn.close()
    assert count > 0


def test_it_services_highest_roe_has_highest_rank(peer_engine):
    conn = sqlite3.connect(peer_engine.db_path)
    df_pct = pd.read_sql("SELECT * FROM peer_percentiles WHERE peer_group_name = 'IT Services' AND metric = 'return_on_equity_pct'", conn)
    conn.close()

    assert not df_pct.empty
    max_val_row = df_pct.loc[df_pct["value"].idxmax()]
    max_rank_row = df_pct.loc[df_pct["percentile_rank"].idxmax()]

    assert max_val_row["company_id"] == max_rank_row["company_id"]
    assert max_rank_row["percentile_rank"] == 1.0


def test_de_percentile_inverted(peer_engine):
    conn = sqlite3.connect(peer_engine.db_path)
    df_pct = pd.read_sql("SELECT * FROM peer_percentiles WHERE peer_group_name = 'IT Services' AND metric = 'debt_to_equity'", conn)
    conn.close()

    assert not df_pct.empty
    min_val_row = df_pct.loc[df_pct["value"].idxmin()]
    max_rank_row = df_pct.loc[df_pct["percentile_rank"].idxmax()]

    # Lower D/E should have highest rank (1.0)
    assert min_val_row["company_id"] == max_rank_row["company_id"]
    assert max_rank_row["percentile_rank"] == 1.0


def test_unmapped_company_handling(peer_engine):
    info = peer_engine.get_company_peer_info("UNMAPPED_TICKER")
    assert info["status"] == "unmapped"
    assert info["message"] == "No peer group assigned"
