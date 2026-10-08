"""Captions must remain truthful when filters, missingness or contrasts change."""
from types import SimpleNamespace
import numpy as np
import pandas as pd
from src.insights import chart_takeaway


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
