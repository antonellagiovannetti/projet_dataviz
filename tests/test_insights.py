"""Captions must remain truthful when filters, missingness or contrasts change."""
from types import SimpleNamespace
import numpy as np
import pandas as pd
import pytest
from src.data_loader import load_data
from src.insights import chart_takeaway, clinical_example


DS = SimpleNamespace(common_allergens=("A", "B"), allergens=("A", "B"))


def test_prevalence_caption_uses_observed_measurements():
    df = pd.DataFrame({"A":[1.,np.nan,0.,2.], "B":[0.,0.,0.,0.]})
    text = chart_takeaway("top-allergens", df=df, ds=DS)
    assert "66,7 %" in text and "3 mesures valides" in text
    assert "50,0 %" not in text


def test_summary_changes_with_selected_patients_and_handles_empty():
    df = pd.DataFrame({"common_count":[1.,3.,10.,20.,np.nan]})
    assert "6,5" in chart_takeaway("overview-hist", df=df)
    assert "2,0" in chart_takeaway("overview-hist", df=df.iloc[:2])
    assert "Aucun patient" in chart_takeaway("overview-hist", df=df.iloc[:0])
    assert "Aucun panel commun complet" in chart_takeaway("overview-hist", df=df.iloc[-1:])


def test_clinical_unknowns_cannot_flip_difference():
    df = pd.DataFrame({"A":[1.,np.nan,0.,0.,0.], "B":[0.,0.,0.,0.,0.],
                       "skin":["Oui","Oui","Non","Inconnu","Inconnu"]})
    text = chart_takeaway("clinical-difference", df=df, ds=DS, controls={"outcome":"skin"})
    assert "100,0 points de plus dans le groupe Oui" in text
    only_positive = df.loc[df.skin.eq("Oui")]
    assert "Deux groupes renseignés" in chart_takeaway("clinical-difference",df=only_positive,ds=DS)


def test_cohort_difference_direction_agrees_with_b_minus_a():
    a=pd.DataFrame({"A":[0.,0.],"B":[0.,0.]})
    b=pd.DataFrame({"A":[1.,1.],"B":[0.,0.]})
    assert "100,0 points de plus dans B" in chart_takeaway("cohort-difference",ds=DS,cohort_a=a,cohort_b=b)
    assert "100,0 points de plus dans A" in chart_takeaway("cohort-difference",ds=DS,cohort_a=b,cohort_b=a)
    assert "identiques" in chart_takeaway("cohort-difference",ds=DS,cohort_a=b,cohort_b=b)


def test_flow_caption_counts_only_jointly_observed_patients():
    df=pd.DataFrame({"age_group":["0–5","Inconnu","6–12"],"sensitization":["Oui"]*3,
                     "skin":["Oui","Oui","Non"],"asthma":["Non","Non","Inconnu"]})
    assert "1 patient complètement renseigné" in chart_takeaway("clinical-flow",df=df)
    assert "Aucun patient ne renseigne" in chart_takeaway("clinical-flow",df=df.iloc[1:])


def test_intensity_does_not_present_mixed_platforms_as_comparable():
    df=pd.DataFrame({"A":[1.,3.],"B":[5.,0.],"chip":["ISAC V1","ALEX"]})
    assert "unités non harmonisées" in chart_takeaway("top-allergens",df=df,ds=DS,controls={"metric":"mean"})
    assert "B figure en tête" in chart_takeaway("top-allergens",df=df.iloc[:1],ds=DS,controls={"metric":"mean"})


def test_clinical_example_source_matches_observed_skin_groups():
    ds = load_data()
    example = clinical_example(ds.frame, ds.common_allergens)
    assert example["available"]
    assert example["allergen"] == "Ara_h_2"
    assert (example["yes_count"], example["no_count"], example["unknown_count"]) == (1140, 686, 2445)
    assert (example["yes_n"], example["no_n"]) == (1140, 686)
    assert example["yes_rate"] == pytest.approx(27.719298245614034)
    assert example["no_rate"] == pytest.approx(8.454810495626822)
    assert example["difference"] == pytest.approx(19.26448774998721)
    assert "avec symptômes cutanés" in example["conclusion"]


def test_clinical_example_preserves_unknowns_and_measurement_denominators():
    df = pd.DataFrame({"Ara_h_2": [1., np.nan, 0., 2., np.nan, 4., 0.],
                       "skin": ["Oui", "Oui", "Non", "Non", "Non", "Inconnu", None]})
    example = clinical_example(df, ["Ara_h_2"])
    assert (example["yes_count"], example["no_count"], example["unknown_count"]) == (2, 3, 2)
    assert (example["yes_n"], example["no_n"]) == (1, 2)
    assert (example["yes_rate"], example["no_rate"], example["difference"]) == (100., 50., 50.)
    filtered = clinical_example(df.loc[[0, 2]], ["Ara_h_2"])
    assert filtered["difference"] == 100.
    assert filtered["unknown_count"] == 0


@pytest.mark.parametrize("frame,allergens", [
    (pd.DataFrame(), ["Ara_h_2"]),
    (pd.DataFrame({"skin": ["Oui"], "Ara_h_2": [1.]}), ["Ara_h_2"]),
    (pd.DataFrame({"skin": ["Oui", "Non"], "Ara_h_2": [np.nan, 1.]}), ["Ara_h_2"]),
    (pd.DataFrame({"skin": ["Oui", "Non"]}), ["Ara_h_2"]),
    (pd.DataFrame({"Ara_h_2": [1.]}), ["Ara_h_2"]),
    (pd.DataFrame({"skin": ["Oui", "Non"], "Ara_h_2": [1., 0.]}), ["A"]),
])
def test_clinical_example_does_not_invent_comparison_when_unavailable(frame, allergens):
    example = clinical_example(frame, allergens)
    assert not example["available"]
    assert example["reason"]
    assert example["yes_rate"] is None and example["no_rate"] is None
    assert example["difference"] is None and not example["conclusion"]


def test_clinical_example_treatment_language_and_difference_direction():
    df = pd.DataFrame({"Ara_h_2": [0., 1.], "asthma": ["Oui", "Non"]})
    example = clinical_example(df, ["Ara_h_2"], "asthma")
    assert example["difference"] == -100.
    assert "sans traitement de l’asthme" in example["conclusion"]
    assert "sans asthme" not in example["conclusion"]
    df["Ara_h_2"] = 1.
    assert "aussi souvent" in clinical_example(df, ["Ara_h_2"], "asthma")["conclusion"]
