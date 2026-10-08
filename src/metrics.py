"""Cohort filters and metrics with explicit observed-population denominators."""
from __future__ import annotations

from collections.abc import Sequence
import numpy as np
import pandas as pd

from .preprocessing import clinical_quality


def _selected(value: object) -> list:
    if value is None:
        return []
    if isinstance(value, (str, int, float, bool)):
        return [value]
    return list(value)


def filter_cohort(frame: pd.DataFrame, filters: dict | None = None) -> pd.DataFrame:
    """Combine filters by AND; values within a categorical filter combine by OR.

    An omitted/empty categorical selection means all. An explicit empty ids
    list means an empty lasso cohort, not all patients. Missing ages are retained
    by default and controlled separately with include_unknown_age.
    """
    filters = filters or {}
    mask = pd.Series(True, index=frame.index)
    age = filters.get("age") or filters.get("age_range")
    if age is not None and len(age) == 2:
        age_mask = frame["age"].between(float(age[0]), float(age[1]), inclusive="both")
        if filters.get("include_unknown_age", True):
            age_mask |= frame["age"].isna()
        mask &= age_mask
    elif not filters.get("include_unknown_age", True):
        mask &= frame["age"].notna()
    for key in ("sex", "chip", "sensitization", "region", "skin", "asthma", "rhinitis", "dermatitis", "cluster", "age_group", "residence"):
        selected = _selected(filters.get(key))
        if selected and key in frame:
            mask &= frame[key].astype(str).isin([str(v) for v in selected])
    if "sensitized" in filters and filters["sensitized"] is not None:
        selected = _selected(filters["sensitized"])
        if selected:
            mask &= frame["sensitized"].isin(selected).fillna(False)
    if filters.get("ids") is not None:
        mask &= frame["id"].isin(_selected(filters["ids"]))
    allergen = filters.get("allergen")
    if allergen and allergen in frame:
        mask &= frame[allergen].gt(0).fillna(False)
    return frame.loc[mask].copy()


def observed_rate(series: pd.Series, positive: str = "Oui") -> tuple[float, int, int]:
    known = series.isin(["Oui", "Non"])
    n = int(known.sum())
    count = int(series.loc[known].eq(positive).sum())
    return (100 * count / n if n else np.nan), n, count


def allergen_statistics(frame: pd.DataFrame, allergens: Sequence[str], threshold: float = 0) -> pd.DataFrame:
    columns = [column for column in allergens if column in frame]
    values = frame.loc[:, columns]
    measured = values.notna().sum()
    detected = values.gt(threshold).sum()
    result = pd.DataFrame({"allergen": columns, "measured": measured.to_numpy(),
                           "detected": detected.to_numpy(),
                           "prevalence": (100 * detected / measured.replace(0, np.nan)).to_numpy(),
                           "mean": values.mean().to_numpy(), "median": values.median().to_numpy()})
    result["label"] = result["allergen"].str.replace("_", " ", regex=False)
    return result.sort_values(["prevalence", "allergen"], ascending=[False, True], na_position="last")


def summary_metrics(frame: pd.DataFrame, allergens: Sequence[str] | None = None) -> dict:
    n = len(frame)
    sensitized_pct, known_n, sensitized_n = observed_rate(frame["sensitization"])
    result = {"n": n, "patients": n, "patient_count": n,
              "median_age": float(frame["age"].median()) if n else np.nan,
              "age_known_n": int(frame["age"].notna().sum()),
              "sensitized_n": sensitized_n, "sensitized_pct": sensitized_pct,
              "sensitization_known_n": known_n,
              "median_common_count": float(frame["common_count"].median()) if frame["common_count"].notna().any() else np.nan,
              "common_count_n": int(frame["common_count"].notna().sum()),
              "median_detected_count": float(frame["detected_count"].median()) if n else np.nan}
    for variable in ("skin", "asthma", "rhinitis", "dermatitis"):
        pct, known, positives = observed_rate(frame[variable])
        result.update({f"{variable}_pct": pct, f"{variable}_known_n": known,
                       f"{variable}_n": positives, f"{variable}_unknown_n": n - known})
    if allergens is not None:
        ranking = allergen_statistics(frame, allergens).dropna(subset=["prevalence"])
        result["top_allergen"] = ranking.iloc[0]["allergen"] if len(ranking) else None
        result["top_allergen_pct"] = float(ranking.iloc[0]["prevalence"]) if len(ranking) else np.nan
    return result


def cohort_difference(a: pd.DataFrame, b: pd.DataFrame, allergens: Sequence[str], threshold: float = 0) -> pd.DataFrame:
    left = allergen_statistics(a, allergens, threshold).set_index("allergen")
    right = allergen_statistics(b, allergens, threshold).set_index("allergen")
    result = pd.DataFrame({"prevalence_a": left["prevalence"], "prevalence_b": right["prevalence"],
                           "measured_a": left["measured"], "measured_b": right["measured"]})
    result["difference"] = result["prevalence_a"] - result["prevalence_b"]
    result["absolute_difference"] = result["difference"].abs()
    return result.reset_index().sort_values("absolute_difference", ascending=False, na_position="last")


def clinical_difference(frame: pd.DataFrame, variable: str, allergens: Sequence[str], threshold: float = 0) -> pd.DataFrame:
    return cohort_difference(frame.loc[frame[variable].eq("Oui")], frame.loc[frame[variable].eq("Non")], allergens, threshold)


def missingness(frame: pd.DataFrame) -> pd.DataFrame:
    return clinical_quality(frame)
