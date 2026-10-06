"""Data loading and statistically transparent summaries for the ACC story."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os

import numpy as np
import pandas as pd


DATA_FILENAME = "allergenchipchallenge-data-corrected-final-hdh-sfa.csv"
COMPONENT_CUTOFF = 0.3
AGE_GROUPS = ["0–5", "6–11", "12–17", "18–39", "40+"]
AGE_BINS = [-1, 5, 11, 17, 39, np.inf]
CHIP_ORDER = ["ISAC_V1", "ISAC_V2", "ALEX"]
CHIP_LABELS = {
    "ISAC_V1": "ISAC v1",
    "ISAC_V2": "ISAC v2",
    "ALEX": "ALEX",
}
CHIP_COLORS = {
    "ISAC_V1": "#355f7b",
    "ISAC_V2": "#bb6847",
    "ALEX": "#14776e",
}
SKIN_LABELS = {
    0: "Sans symptôme cutané",
    1: "Avec symptôme cutané",
    9: "Inconnu",
}


@dataclass
class AccBundle:
    patients: pd.DataFrame
    values: pd.DataFrame
    component_columns: list[str]
    csv_path: Path
    negative_sentinel_count: int


def _resolve_csv_path() -> Path:
    override = os.environ.get("ACC_CSV_PATH")
    if override:
        path = Path(override).expanduser()
        if path.is_file():
            return path
        raise FileNotFoundError(
            f"ACC_CSV_PATH pointe vers un fichier absent : {path}"
        )

    project_dir = Path(__file__).resolve().parent
    candidates = [
        Path.home() / "Downloads" / DATA_FILENAME,
        project_dir / "data" / DATA_FILENAME,
        project_dir / DATA_FILENAME,
    ]
    for path in candidates:
        if path.is_file():
            return path

    searched = "\n".join(f"• {path}" for path in candidates)
    raise FileNotFoundError(
        "Le CSV ACC est introuvable. Définissez ACC_CSV_PATH ou placez le "
        f"fichier dans un des emplacements suivants :\n{searched}"
    )


def _to_numeric(series: pd.Series) -> pd.Series:
    normalized = series.astype("string").str.strip().str.replace(
        ",", ".", regex=False
    )
    return pd.to_numeric(normalized, errors="coerce")


def load_acc_data() -> AccBundle:
    csv_path = _resolve_csv_path()
    raw = pd.read_csv(
        csv_path,
        sep=";",
        encoding="utf-8-sig",
        low_memory=False,
        dtype={"Patient_ID": "string"},
    )

    required = {
        "Patient_ID",
        "Chip_Type",
        "Age",
        "Sensitization",
        "Skin_Symptoms",
    }
    missing = sorted(required.difference(raw.columns))
    if missing:
        raise ValueError(
            "Le CSV ne correspond pas au dictionnaire attendu. "
            f"Colonnes obligatoires absentes : {', '.join(missing)}"
        )
    if raw.shape[1] <= 15:
        raise ValueError(
            "Le fichier ne contient pas la matrice de composants IgE attendue."
        )

    metadata_columns = list(raw.columns[:15])
    component_columns = list(raw.columns[15:])
    patients = raw[metadata_columns].copy()
    values = raw[component_columns].apply(_to_numeric)

    # Negative concentrations are not treated as measured negative values.
    # This public extract contains -1 sentinel values in ISAC rows.
    negative_sentinel_count = int(values.lt(0).sum().sum())
    values = values.mask(values.lt(0))

    for column in ("Age", "Gender", "Sensitization", "Skin_Symptoms"):
        if column in patients:
            patients[column] = pd.to_numeric(
                patients[column], errors="coerce"
            )

    patients["Age_Group"] = pd.cut(
        patients["Age"],
        bins=AGE_BINS,
        labels=AGE_GROUPS,
        right=True,
        include_lowest=True,
    ).astype("string")
    patients["Skin_Label"] = (
        patients["Skin_Symptoms"].map(SKIN_LABELS).fillna("Inconnu")
    )

    return AccBundle(
        patients=patients,
        values=values,
        component_columns=component_columns,
        csv_path=csv_path,
        negative_sentinel_count=negative_sentinel_count,
    )


def measured_breadth(bundle: AccBundle, cutoff: float = COMPONENT_CUTOFF) -> pd.DataFrame:
    tested = bundle.values.notna()
    positive = bundle.values.ge(cutoff)
    tested_count = tested.sum(axis=1)
    positive_count = positive.sum(axis=1)
    breadth = positive_count.div(tested_count.where(tested_count > 0))

    return pd.DataFrame(
        {
            "tested_components": tested_count,
            "positive_components": positive_count,
            "breadth": breadth,
        },
        index=bundle.patients.index,
    )


def _bootstrap_mean_interval(
    values: np.ndarray,
    rng: np.random.Generator,
    n_resamples: int = 600,
) -> tuple[float, float]:
    values = np.asarray(values, dtype=float)
    values = values[np.isfinite(values)]
    if values.size == 0:
        return float("nan"), float("nan")
    if values.size == 1:
        value = float(values[0])
        return value, value

    sample_indices = rng.integers(
        0, values.size, size=(n_resamples, values.size)
    )
    sample_means = values[sample_indices].mean(axis=1)
    lower, upper = np.quantile(sample_means, [0.025, 0.975])
    return float(lower), float(upper)


def age_breadth_summary(
    bundle: AccBundle,
    cutoff: float = COMPONENT_CUTOFF,
    n_resamples: int = 600,
) -> pd.DataFrame:
    profile = measured_breadth(bundle, cutoff)
    frame = bundle.patients[["Chip_Type", "Age_Group"]].copy()
    frame["breadth"] = profile["breadth"]
    rng = np.random.default_rng(20261006)
    rows: list[dict[str, object]] = []

    for chip in CHIP_ORDER:
        for age_group in AGE_GROUPS:
            values = frame.loc[
                (frame["Chip_Type"] == chip)
                & (frame["Age_Group"] == age_group),
                "breadth",
            ].dropna().to_numpy()
            if values.size == 0:
                continue
            lower, upper = _bootstrap_mean_interval(
                values, rng, n_resamples=n_resamples
            )
            rows.append(
                {
                    "Chip_Type": chip,
                    "Age_Group": age_group,
                    "n": int(values.size),
                    "mean_pct": float(values.mean() * 100),
                    "median_pct": float(np.median(values) * 100),
                    "low_pct": lower * 100,
                    "high_pct": upper * 100,
                }
            )
    return pd.DataFrame(rows)


def skin_age_standardized_summary(
    bundle: AccBundle,
    cutoff: float = COMPONENT_CUTOFF,
    n_resamples: int = 600,
) -> pd.DataFrame:
    profile = measured_breadth(bundle, cutoff)
    frame = bundle.patients[
        ["Chip_Type", "Age_Group", "Skin_Symptoms"]
    ].copy()
    frame["breadth"] = profile["breadth"]
    frame = frame[
        frame["Skin_Symptoms"].isin([0, 1]) & frame["Age_Group"].notna()
    ]

    rng = np.random.default_rng(20261007)
    rows: list[dict[str, object]] = []
    for chip in CHIP_ORDER:
        subset = frame[frame["Chip_Type"] == chip]
        if subset.empty:
            continue

        age_counts = (
            subset["Age_Group"]
            .value_counts()
            .reindex(AGE_GROUPS, fill_value=0)
        )
        weights = (age_counts / age_counts.sum()).to_numpy(dtype=float)
        cells: dict[tuple[int, str], np.ndarray] = {}
        complete = True
        for skin_status in (0, 1):
            for age_group in AGE_GROUPS:
                cell = subset.loc[
                    (subset["Skin_Symptoms"] == skin_status)
                    & (subset["Age_Group"] == age_group),
                    "breadth",
                ].dropna().to_numpy(dtype=float)
                cells[(skin_status, age_group)] = cell
                if cell.size == 0:
                    complete = False
        if not complete:
            continue

        means: dict[int, np.ndarray] = {}
        for skin_status in (0, 1):
            means[skin_status] = np.array(
                [
                    cells[(skin_status, age_group)].mean()
                    for age_group in AGE_GROUPS
                ],
                dtype=float,
            )

        standardized_no = float(np.dot(weights, means[0]) * 100)
        standardized_yes = float(np.dot(weights, means[1]) * 100)
        effect = standardized_yes - standardized_no

        bootstrap_effects = np.empty(n_resamples, dtype=float)
        for iteration in range(n_resamples):
            sampled_means = {}
            for skin_status in (0, 1):
                sampled_means[skin_status] = np.array(
                    [
                        rng.choice(cell, size=cell.size, replace=True).mean()
                        for age_group in AGE_GROUPS
                        for cell in [cells[(skin_status, age_group)]]
                    ],
                    dtype=float,
                )
            bootstrap_effects[iteration] = (
                np.dot(
                    weights,
                    sampled_means[1] - sampled_means[0],
                )
                * 100
            )
        low, high = np.quantile(bootstrap_effects, [0.025, 0.975])

        rows.append(
            {
                "Chip_Type": chip,
                "known_n": int(len(subset)),
                "no_n": int((subset["Skin_Symptoms"] == 0).sum()),
                "yes_n": int((subset["Skin_Symptoms"] == 1).sum()),
                "standardized_no_pct": standardized_no,
                "standardized_yes_pct": standardized_yes,
                "effect_pp": effect,
                "low_pp": float(low),
                "high_pp": float(high),
            }
        )
    return pd.DataFrame(rows)


def sensitization_agreement(
    bundle: AccBundle,
    cutoff: float = COMPONENT_CUTOFF,
) -> tuple[pd.DataFrame, float]:
    profile = measured_breadth(bundle, cutoff)
    component_signal = profile["positive_components"] > 0
    status = bundle.patients["Sensitization"]
    table = pd.crosstab(status, component_signal).reindex(
        index=[0, 1], columns=[False, True], fill_value=0
    )
    agreement = float(
        (table.loc[0, False] + table.loc[1, True]) / table.to_numpy().sum()
    )
    return table, agreement


def chip_coverage_summary(bundle: AccBundle) -> pd.DataFrame:
    observed_per_patient = bundle.values.notna().sum(axis=1)
    rows: list[dict[str, object]] = []
    total_components = len(bundle.component_columns)
    for chip in CHIP_ORDER:
        mask = bundle.patients["Chip_Type"] == chip
        if not mask.any():
            continue
        observed = observed_per_patient.loc[mask]
        rows.append(
            {
                "Chip_Type": chip,
                "patients": int(mask.sum()),
                "components": int(observed.median()),
                "total_components": total_components,
                "coverage_pct": float(observed.median() / total_components * 100),
            }
        )
    return pd.DataFrame(rows)


def top_component_matrix(
    bundle: AccBundle,
    age_groups: list[str] | None = None,
    cutoff: float = COMPONENT_CUTOFF,
    limit: int = 16,
    min_measured: int = 20,
) -> tuple[list[str], list[list[float | None]], list[list[tuple[int, int] | None]]]:
    selected_ages = age_groups or AGE_GROUPS
    frame = bundle.patients
    row_mask = frame["Age_Group"].isin(selected_ages)
    component_rates: dict[str, list[float | None]] = {}
    component_counts: dict[str, list[tuple[int, int] | None]] = {}

    for component in bundle.component_columns:
        rates: list[float | None] = []
        counts: list[tuple[int, int] | None] = []
        for chip in CHIP_ORDER:
            indices = frame.index[row_mask & frame["Chip_Type"].eq(chip)]
            measured = bundle.values.loc[indices, component].dropna()
            denominator = int(measured.size)
            numerator = int(measured.ge(cutoff).sum())
            if denominator < min_measured:
                rates.append(None)
                counts.append(None)
            else:
                rates.append(numerator / denominator * 100)
                counts.append((numerator, denominator))
        available_rates = [rate for rate in rates if rate is not None]
        if available_rates:
            component_rates[component] = rates
            component_counts[component] = counts

    ranked = sorted(
        component_rates,
        key=lambda component: (
            -float(
                np.mean(
                    [
                        rate
                        for rate in component_rates[component]
                        if rate is not None
                    ]
                )
            ),
            component,
        ),
    )[:limit]

    return (
        ranked,
        [component_rates[component] for component in ranked],
        [component_counts[component] for component in ranked],
    )


def component_age_summary(
    bundle: AccBundle,
    component: str,
    chip: str,
    age_groups: list[str] | None = None,
    cutoff: float = COMPONENT_CUTOFF,
) -> pd.DataFrame:
    selected_ages = age_groups or AGE_GROUPS
    patients = bundle.patients
    rows: list[dict[str, object]] = []
    for age_group in AGE_GROUPS:
        if age_group not in selected_ages:
            continue
        indices = patients.index[
            patients["Chip_Type"].eq(chip)
            & patients["Age_Group"].eq(age_group)
        ]
        measured = bundle.values.loc[indices, component].dropna()
        n = int(measured.size)
        positives = int(measured.ge(cutoff).sum())
        if n == 0:
            continue

        proportion = positives / n
        z = 1.96
        denominator = 1 + (z * z / n)
        center = (proportion + z * z / (2 * n)) / denominator
        half_width = (
            z
            * np.sqrt(
                proportion * (1 - proportion) / n
                + z * z / (4 * n * n)
            )
            / denominator
        )
        rows.append(
            {
                "Age_Group": age_group,
                "n": n,
                "positive_n": positives,
                "rate_pct": proportion * 100,
                "low_pct": max(0.0, center - half_width) * 100,
                "high_pct": min(1.0, center + half_width) * 100,
            }
        )
    return pd.DataFrame(rows)


def cohort_summary(bundle: AccBundle) -> dict[str, object]:
    patients = bundle.patients
    n = len(patients)
    age = patients["Age"].dropna()
    sensitized = patients["Sensitization"].eq(1)
    skin_known = patients["Skin_Symptoms"].isin([0, 1])
    coverage = chip_coverage_summary(bundle)

    return {
        "n": n,
        "sensitized_n": int(sensitized.sum()),
        "sensitized_pct": float(sensitized.mean() * 100),
        "median_age": float(age.median()) if not age.empty else float("nan"),
        "q1_age": float(age.quantile(0.25)) if not age.empty else float("nan"),
        "q3_age": float(age.quantile(0.75)) if not age.empty else float("nan"),
        "age_missing_n": int(patients["Age"].isna().sum()),
        "skin_known_n": int(skin_known.sum()),
        "skin_unknown_pct": float((~skin_known).mean() * 100),
        "component_count": len(bundle.component_columns),
        "component_missing_pct": float(
            bundle.values.isna().to_numpy().mean() * 100
        ),
        "coverage": coverage,
        "unique_patient_ids": int(patients["Patient_ID"].nunique()),
        "severe_label_available": "Severe_Allergy" in patients.columns,
        "allergy_label_available": "Allergy_Present" in patients.columns,
    }
