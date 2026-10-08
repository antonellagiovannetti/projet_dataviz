"""Transparent derivations for the open Allergen Chip Challenge dataset.

The original clinical encodings are kept in the frame. A detectable signal is
defined only as a valid IgE value > 0; it is not a clinical allergy diagnosis.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

CHIP_LABELS = {"ISAC_V1": "ISAC V1", "ISAC_V2": "ISAC V2", "ALEX": "ALEX"}
CHIP_ORDER = ("ISAC V1", "ISAC V2", "ALEX")
AGE_LABELS = ("0–5", "6–12", "13–17", "18–30", "31–50", "51+")
CLINICAL_COLUMNS = {
    "skin": "Skin_Symptoms",
    "asthma": "Treatment_of_athsma",
    "rhinitis": "Treatment_of_rhinitis",
    "dermatitis": "Treatment_of_atopic_dematitis",
}
CLINICAL_LABELS = {
    "skin": "Symptômes cutanés", "asthma": "Traitement de l’asthme",
    "rhinitis": "Traitement de la rhinite", "dermatitis": "Traitement de la dermatite",
}


def clinical_status(value: object, *, treatment: bool = True) -> str:
    """Interpret multicodes without turning a comma-separated code into a decimal.

    9 (or missing) is excluded from yes/no denominators. For skin it means
    'not relevant' according to the dictionary, rather than a confirmed absence.
    """
    if pd.isna(value):
        return "Inconnu"
    text = str(value).strip()
    if text.endswith(".0"):
        text = text[:-2]
    tokens = {token.strip() for token in text.split(",")}
    if not tokens or "" in tokens or "9" in tokens:
        return "Inconnu"
    if tokens == {"0"}:
        return "Non"
    if treatment:
        return "Oui" if all(t.isdigit() for t in tokens) else "Inconnu"
    return "Oui" if tokens == {"1"} else "Inconnu"


def age_groups(ages: pd.Series, mode: str = "standard") -> pd.Series:
    if mode == "decades":
        bins = [-np.inf, 9, 19, 29, 39, 49, 59, 69, np.inf]
        labels = ["0–9", "10–19", "20–29", "30–39", "40–49", "50–59", "60–69", "70+"]
    elif mode == "adult":
        bins, labels = [-np.inf, 17, np.inf], ["0–17", "18+"]
    else:
        bins, labels = [-np.inf, 5, 12, 17, 30, 50, np.inf], list(AGE_LABELS)
    return pd.cut(ages, bins=bins, labels=labels).astype("string").fillna("Inconnu")


def derive_columns(frame: pd.DataFrame, allergens: tuple[str, ...], common: tuple[str, ...]) -> pd.DataFrame:
    """Add display/filter columns while retaining original source column names."""
    result = frame.copy()
    derived = pd.DataFrame(index=result.index)
    derived["id"] = result["Patient_ID"].astype(str)
    derived["age"] = result["Age"]
    derived["sex"] = result["Gender"].map({0: "Femmes", 1: "Hommes"}).fillna("Inconnu")
    derived["chip"] = result["Chip_Type"].map(CHIP_LABELS).fillna(result["Chip_Type"])
    derived["region"] = result["French_Region"].fillna("Inconnu")
    derived["residence"] = result["Rural_or_urban_area"].map({0: "Rural", 1: "Urbain"}).fillna("Inconnu")
    derived["sensitized"] = result["Sensitization"].map({0: False, 1: True}).astype("boolean")
    derived["sensitization"] = result["Sensitization"].map({0: "Non", 1: "Oui"}).fillna("Inconnu")
    for derived_name, source in CLINICAL_COLUMNS.items():
        derived[derived_name] = result[source].map(lambda value: clinical_status(value, treatment=derived_name != "skin"))
    values = result.loc[:, list(allergens)]
    common_values = result.loc[:, list(common)]
    derived["detected_count"] = values.gt(0).sum(axis=1).astype(int)
    derived["measured_count"] = values.notna().sum(axis=1).astype(int)
    derived["common_measured_count"] = common_values.notna().sum(axis=1).astype(int)
    derived["common_count"] = common_values.gt(0).sum(axis=1).astype(float).where(common_values.notna().all(axis=1))
    derived["common_complete"] = common_values.notna().all(axis=1)
    derived["age_group"] = age_groups(derived["age"])
    return pd.concat([result, derived], axis=1)


def clinical_quality(frame: pd.DataFrame) -> pd.DataFrame:
    checks = {
        "age": ("Âge", frame["age"].isna()),
        "sex": ("Sexe", frame["sex"].eq("Inconnu")),
        "residence": ("Habitat rural / urbain", frame["residence"].eq("Inconnu")),
        "skin": ("Symptômes cutanés", frame["skin"].eq("Inconnu")),
        "rhinitis": ("Traitement de la rhinite", frame["rhinitis"].eq("Inconnu")),
        "asthma": ("Traitement de l’asthme", frame["asthma"].eq("Inconnu")),
        "onset": ("Âge de début (classe)", frame["Age_of_onsets"].isna() | frame["Age_of_onsets"].astype(str).isin(["9", "9.0"])),
        "dermatitis": ("Traitement de la dermatite", frame["dermatitis"].eq("Inconnu")),
    }
    n = len(frame)
    return pd.DataFrame([
        {"variable": key, "label": label, "missing": int(mask.sum()), "n": n,
         "missing_pct": 100 * float(mask.mean()) if n else np.nan}
        for key, (label, mask) in checks.items()
    ])
