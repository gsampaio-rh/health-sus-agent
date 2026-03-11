"""Tests for pre-built analysis tools."""

import pandas as pd
import pytest

from src.agent.accumulator import FindingsAccumulator
from src.agent.tools import analysis as analysis_tools
from src.agent.tools import data as data_tools
from src.agent.tools import findings as findings_tools


@pytest.fixture(autouse=True)
def reset():
    """Reset global state between tests."""
    data_tools.reset_datasets()
    findings_tools.set_accumulator(FindingsAccumulator())
    yield
    data_tools.reset_datasets()


@pytest.fixture
def sample_df(tmp_path):
    """Create a sample parquet file for testing."""
    df = pd.DataFrame({
        "year": [2020, 2020, 2021, 2021, 2022, 2022],
        "MORTE": [0, 1, 0, 0, 1, 1],
        "IDADE": [65, 72, 45, 80, 55, 68],
        "SEXO": ["1", "3", "1", "3", "1", "3"],
        "MUNIC_RES": ["355030", "355030", "350950", "350950", "355030", "350950"],
        "DIAS_PERM": [5, 12, 3, 20, 8, 15],
    })
    path = tmp_path / "test_data.parquet"
    df.to_parquet(path)
    return str(path)


class TestDataTools:
    def test_load_dataset(self, sample_df):
        result = data_tools.load_dataset("test", sample_df)
        assert "6 rows" in result
        assert "6 columns" in result

    def test_load_dataset_with_filter(self, sample_df):
        result = data_tools.load_dataset(
            "test", sample_df, filters={"SEXO": "1"}
        )
        assert "3 rows" in result

    def test_load_dataset_missing_file(self):
        result = data_tools.load_dataset("test", "/nonexistent.parquet")
        assert "Error" in result

    def test_get_dataset(self, sample_df):
        data_tools.load_dataset("test", sample_df)
        df = data_tools.get_dataset("test")
        assert len(df) == 6

    def test_get_dataset_not_found(self):
        with pytest.raises(KeyError, match="not found"):
            data_tools.get_dataset("nonexistent")

    def test_list_datasets(self, sample_df):
        assert data_tools.list_datasets() == "No datasets loaded."
        data_tools.load_dataset("test", sample_df)
        result = data_tools.list_datasets()
        assert "test" in result
        assert "6 rows" in result

    def test_describe_columns(self, sample_df):
        data_tools.load_dataset("test", sample_df)
        result = data_tools.describe_columns("test", ["IDADE", "SEXO"])
        assert "numeric" in result
        assert "categorical" in result

    def test_filter_dataset(self, sample_df):
        data_tools.load_dataset("test", sample_df)
        result = data_tools.filter_dataset(
            "test", {"SEXO": "1"}, new_name="male"
        )
        assert "6 → 3" in result
        df = data_tools.get_dataset("male")
        assert len(df) == 3


class TestAnalysisTools:
    def test_aggregate(self, sample_df):
        data_tools.load_dataset("test", sample_df)
        result = analysis_tools.aggregate(
            "test",
            group_by=["year"],
            metrics={"mortality_rate": "MORTE:mean", "n": "MORTE:count"},
        )
        assert "2020" in result
        assert "2021" in result

    def test_time_series(self, sample_df):
        data_tools.load_dataset("test", sample_df)
        result = analysis_tools.time_series(
            "test", date_col="year", value_col="MORTE", freq="year"
        )
        assert "Overall change" in result

    def test_cross_tabulate(self, sample_df):
        data_tools.load_dataset("test", sample_df)
        result = analysis_tools.cross_tabulate(
            "test", row_var="SEXO", col_var="MORTE"
        )
        assert "Chi-square" in result or "1" in result

    def test_statistical_test(self, sample_df):
        data_tools.load_dataset("test", sample_df)
        result = analysis_tools.statistical_test(
            "test",
            test_type="mannwhitney",
            group_col="SEXO",
            value_col="IDADE",
        )
        assert "U-statistic" in result

    def test_logistic_regression(self, sample_df):
        data_tools.load_dataset("test", sample_df)
        result = analysis_tools.logistic_regression(
            "test",
            target="MORTE",
            features=["IDADE", "DIAS_PERM"],
        )
        assert "Logistic Regression" in result
        assert "IDADE" in result

    def test_aggregate_missing_column(self, sample_df):
        data_tools.load_dataset("test", sample_df)
        result = analysis_tools.aggregate(
            "test",
            group_by=["nonexistent"],
            metrics={"n": "MORTE:count"},
        )
        assert "Error" in result


class TestFindingsTools:
    def test_record_finding(self):
        result = findings_tools.record_finding(
            finding_id="test_1",
            statement="Mortality is rising",
            evidence="33% in 2020, 50% in 2022",
            so_what="Invest in prevention",
        )
        assert "Finding recorded" in result

    def test_get_findings_summary_empty(self):
        result = findings_tools.get_findings_summary()
        assert "No findings" in result

    def test_get_findings_summary_with_findings(self):
        findings_tools.record_finding(
            finding_id="test_1",
            statement="Test finding",
            evidence="Some evidence",
            so_what="Take action",
        )
        result = findings_tools.get_findings_summary()
        assert "Test finding" in result

    def test_add_open_question(self):
        result = findings_tools.add_open_question(
            "Why is mortality rising in Guarulhos?"
        )
        assert "Open question added" in result
