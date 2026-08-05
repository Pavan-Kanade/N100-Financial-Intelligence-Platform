"""
Unit tests for Analysis Text Parser (src/nlp/parser.py).
"""

import os
import pytest
import pandas as pd
from src.nlp.parser import AnalysisTextParser


@pytest.fixture(scope="module")
def parsed_data():
    parser = AnalysisTextParser()
    return parser.parse()


def test_parser_returns_dataframes(parsed_data):
    df_parsed, df_failures = parsed_data
    assert isinstance(df_parsed, pd.DataFrame)
    assert isinstance(df_failures, pd.DataFrame)


def test_analysis_parsed_csv_file():
    assert os.path.exists("output/analysis_parsed.csv")


def test_regex_pattern_extraction():
    parser = AnalysisTextParser()
    match = parser.pattern.search("10 Years: 21%")
    assert match is not None
    assert match.group(1) == "10"
    assert match.group(2) == "21"
