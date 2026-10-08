"""Scientific invariants: missing is not negative, unknown is not absent."""
import numpy as np
import pandas as pd
import pytest

from src.clustering import get_profiles, standardize_ige
from src.data_loader import load_data
from src.metrics import allergen_statistics, filter_cohort, observed_rate, summary_metrics
from src.preprocessing import clinical_status


@pytest.fixture(scope="module")
def dataset():
    return load_data()


def test_source_shape_identity_and_coverage(dataset):
    assert len(dataset.frame) == 4271
    assert dataset.frame["id"].nunique() == len(dataset.frame)
    assert len(dataset.allergens) == 241
    assert len(dataset.common_allergens) == 91
    assert dataset.coverage.sum(axis=1).to_dict() == {"ISAC V1": 112, "ISAC V2": 112, "ALEX": 223}


def test_structural_missingness_is_never_filled(dataset):
    for chip in dataset.coverage.index:
        absent = dataset.coverage.columns[~dataset.coverage.loc[chip]]
        assert dataset.frame.loc[dataset.frame["chip"].eq(chip), absent].isna().all().all()


def test_negative_sentinel_preserved_and_excluded(dataset):
    assert len(dataset.invalid_values) == 52
    assert dataset.invalid_values["id"].nunique() == 36
    assert not dataset.frame.loc[:, list(dataset.allergens)].lt(0).any().any()
    assert dataset.frame["common_complete"].sum() == 4241
    assert dataset.frame["common_count"].isna().sum() == 30
    for record in dataset.invalid_values.itertuples():
        row = dataset.frame.index[dataset.frame["id"].eq(record.id)][0]
        assert dataset.raw_frame.loc[row, record.allergen] == "-1"
        assert pd.isna(dataset.frame.loc[row, record.allergen])


@pytest.mark.parametrize("raw,expected", [("0", "Non"), ("9", "Inconnu"),
    ("10", "Oui"), ("1, 2", "Oui"), ("2,7", "Oui"), (None, "Inconnu"), ("1,9", "Inconnu")])
def test_treatment_codes_are_not_decimal_values(raw, expected):
    assert clinical_status(raw) == expected


def test_unknown_and_unmeasured_excluded_from_rate_denominators():
    rate, n, count = observed_rate(pd.Series(["Oui", "Non", "Inconnu", "Inconnu"]))
    assert (rate, n, count) == (50.0, 2, 1)
    stats = allergen_statistics(pd.DataFrame({"a": [1, 0, np.nan, np.nan], "b": [np.nan] * 4}), ["a", "b"])
    assert stats.set_index("allergen").loc["a", "prevalence"] == 50
    assert stats.set_index("allergen").loc["a", "measured"] == 2
    assert pd.isna(stats.set_index("allergen").loc["b", "prevalence"])


def test_empty_cohort_is_not_restored_to_full_dataset(dataset):
    empty = filter_cohort(dataset.frame, {"ids": []})
    assert empty.empty
    summary = summary_metrics(empty, dataset.common_allergens)
    assert summary["n"] == 0
    assert np.isnan(summary["sensitized_pct"])
    assert summary["top_allergen"] is None
    assert allergen_statistics(empty, dataset.common_allergens)["prevalence"].isna().all()


def test_unknown_age_is_an_explicit_filter_choice(dataset):
    with_unknown = filter_cohort(dataset.frame, {"age": [0, 17], "include_unknown_age": True})
    observed = filter_cohort(dataset.frame, {"age": [0, 17], "include_unknown_age": False})
    assert len(with_unknown) - len(observed) == 61
    assert observed["age"].between(0, 17).all()


def test_preprocessing_uses_only_ige_and_chip(dataset):
    transformed = standardize_ige(dataset.frame, dataset.common_allergens, True)
    assert np.isfinite(transformed.to_numpy()).all()
    assert len(transformed) == 4241
    changed = dataset.frame.copy()
    for column in ("Age", "Gender", "Sensitization", "age", "skin", "asthma", "sensitized"):
        changed[column] = 0
    alternative = standardize_ige(changed, dataset.common_allergens, True)
    np.testing.assert_array_equal(transformed.to_numpy(), alternative.to_numpy())
    for chip in dataset.frame["chip"].unique():
        rows = dataset.frame.loc[transformed.index, "chip"].eq(chip)
        np.testing.assert_allclose(transformed.loc[rows].mean(), 0, atol=1e-12)


def test_profile_partition_and_finite_coordinates(dataset):
    profiles = get_profiles()
    assert set(profiles.scores["k"]) == set(range(2, 9))
    assert profiles.best_k == int(profiles.scores.loc[profiles.scores["silhouette"].idxmax(), "k"])
    assert len(profiles.frame) == 4271
    assert profiles.excluded_count == 30
    assert profiles.frame["cluster"].eq("Non attribué").sum() == 30
    assert profiles.cluster_sizes["n"].sum() == 4241
    assert profiles.frame.loc[profiles.labels.index, ["pc1", "pc2"]].notna().all().all()
    assert profiles.frame.loc[~dataset.frame["common_complete"], ["pc1", "pc2"]].isna().all().all()
    assert 0 <= profiles.platform_cramers_v <= 1
    assert 0 <= profiles.platform_nmi <= 1
    assert 0 < sum(profiles.explained_variance) <= 1
