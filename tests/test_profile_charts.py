"""Protect disjoint comparisons and clinical missing-value denominators."""
import numpy as np
import pandas as pd
import pytest

from src.charts import cluster_excess, profile_clinical_comparison


@pytest.fixture
def patients():
    return pd.DataFrame({
        "cluster": ["1", "1", "1", "2", "2", "Non attribué"],
        "a": [1., 1., np.nan, 0., 0., 1.],
        "skin": ["Oui", "Non", "Inconnu", "Non", "Non", "Oui"],
        "asthma": ["Inconnu", None, "Inconnu", "Oui", None, "Non"],
        "rhinitis": ["Non", "Non", None, "Oui", "Oui", "Inconnu"],
        "dermatitis": ["Oui", None, "Oui", None, None, "Inconnu"],
    })


def annotations(fig):
    return " ".join(item.text for item in fig.layout.annotations or [])


def test_ige_profile_reference_excludes_selected_members(patients):
    fig = cluster_excess(patients, ["a"], "1")
    bar = fig.data[0]
    assert bar.x[0] == pytest.approx(100 - 100 / 3)
    assert bar.customdata[0][0] == "a"
    assert list(bar.customdata[0][1:]) == pytest.approx([100, 100 / 3, 2, 2, 1, 3])
    assert "Reste de la cohorte filtrée" in bar.hovertemplate
    assert "profil − reste" in fig.layout.xaxis.title.text


def test_narrow_selected_frame_still_excludes_entire_profile_from_reference(patients):
    fig = cluster_excess(patients, ["a"], "1", selected_df=patients.iloc[:1])
    assert list(fig.data[0].customdata[0][1:]) == pytest.approx([100, 100 / 3, 1, 1, 1, 3])


def test_clinical_rates_use_per_variable_known_denominators(patients):
    original = patients.copy(deep=True)
    fig = profile_clinical_comparison(patients, "1")
    selected, remainder = fig.data
    assert list(selected.x) == [50, None, 0, 100]
    assert list(remainder.x) == [100 / 3, 50, 100, None]
    assert list(selected.customdata[0])[3:] == [1, 1, 2, 1, 3]
    assert list(remainder.customdata[0])[3:] == [1, 2, 3, 0, 3]
    assert selected.marker.symbol != remainder.marker.symbol
    assert "50.0 % · 2 / 1" in annotations(fig)
    assert "33.3 % · 3 / 0" in annotations(fig)
    assert "n/d · 0 / 3" in annotations(fig)
    assert "Effectifs : connus / inconnus" in annotations(fig)
    assert "Non :" in selected.hovertemplate
    assert "Total du groupe" in selected.hovertemplate
    assert "Inconnus exclus" in selected.hovertemplate
    pd.testing.assert_frame_equal(patients, original)


def test_all_unknown_clinical_statuses_never_produce_zero_rates(patients):
    patients.loc[:, ["skin", "asthma", "rhinitis", "dermatitis"]] = "Inconnu"
    fig = profile_clinical_comparison(patients, "1")
    assert all(value is None for trace in fig.data for value in trace.x)
    assert annotations(fig).count("n/d") == 8
    assert all(row[5] == 0 and row[6] == 3 for trace in fig.data for row in trace.customdata)


@pytest.mark.parametrize("selection,message", [
    (None, "Choisir un profil"), ("9", "absent de ces filtres"),
])
def test_clinical_selection_states_are_explicit(patients, selection, message):
    fig = profile_clinical_comparison(patients, selection)
    assert not fig.data
    assert message in annotations(fig).replace("<br>", " ")


def test_empty_population_and_empty_remainder_are_explicit(patients):
    empty = profile_clinical_comparison(patients.iloc[:0], "1")
    assert not empty.data
    assert "Aucun patient" in annotations(empty)
    one_group = patients.loc[patients.cluster.eq("1")]
    clinical = profile_clinical_comparison(one_group, "1")
    assert not clinical.data
    assert "aucun autre patient" in annotations(clinical).replace("<br>", " ")
    assert not cluster_excess(one_group, ["a"], "1").data
