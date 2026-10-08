"""Cached, validated ingestion of the user-provided ACC source CSV."""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd

from .preprocessing import CHIP_LABELS, CHIP_ORDER, clinical_quality, derive_columns

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = ROOT / "data" / "raw" / "allergenchipchallenge-data-corrected-final-hdh-sfa.csv"
METADATA_COLUMNS = (
    "Patient_ID", "Chip_Type", "Age", "Gender", "Blood_Month_sample",
    "French_Residence_Department", "French_Region", "Rural_or_urban_area",
    "Sensitization", "Treatment_of_rhinitis", "Treatment_of_athsma", "Age_of_onsets",
    "Skin_Symptoms", "General_cofactors", "Treatment_of_atopic_dematitis",
)


@dataclass(frozen=True)
class Dataset:
    frame: pd.DataFrame
    allergens: tuple[str, ...]
    common_allergens: tuple[str, ...]
    coverage: pd.DataFrame
    quality: pd.DataFrame
    source_path: Path
    raw_frame: pd.DataFrame
    invalid_values: pd.DataFrame
    audit: dict


def load_data(path: str | Path | None = None) -> Dataset:
    """Read once per source modification. Returned frames should be treated as read-only."""
    source = Path(path).resolve() if path is not None else DEFAULT_SOURCE
    stat = source.stat()
    return _load_data(str(source), stat.st_mtime_ns, stat.st_size)


@lru_cache(maxsize=4)
def _load_data(path: str, modified: int, size: int) -> Dataset:
    raw = pd.read_csv(path, sep=";", encoding="utf-8-sig", dtype="string", low_memory=False)
    raw.columns = raw.columns.str.strip().str.lstrip("\ufeff")
    missing = set(METADATA_COLUMNS) - set(raw.columns)
    if missing:
        raise ValueError(f"Colonnes ACC absentes : {', '.join(sorted(missing))}")
    if raw["Patient_ID"].isna().any() or raw["Patient_ID"].duplicated().any():
        raise ValueError("Patient_ID doit identifier une seule observation et être renseigné.")
    unknown_chips = set(raw["Chip_Type"].dropna()) - set(CHIP_LABELS)
    if unknown_chips or raw["Chip_Type"].isna().any():
        raise ValueError(f"Technologie non reconnue : {unknown_chips}")
    allergens = tuple(column for column in raw.columns if column not in METADATA_COLUMNS)
    if not allergens:
        raise ValueError("Aucune variable IgE trouvée dans le fichier.")
    values = raw.loc[:, list(allergens)].apply(
        lambda column: pd.to_numeric(column.str.replace(",", ".", regex=False), errors="coerce")
    ).astype(float)
    unparseable = raw.loc[:, list(allergens)].notna() & values.isna()
    if unparseable.any().any():
        raise ValueError("Valeur IgE non numérique : contrôler le format du CSV.")
    invalid_mask = values.lt(0) | (values.notna() & ~np.isfinite(values))
    invalid_positions = np.argwhere(invalid_mask.to_numpy())
    invalid = pd.DataFrame([
        {"id": str(raw.iloc[row]["Patient_ID"]), "allergen": allergens[col],
         "value": float(values.iloc[row, col]), "chip": CHIP_LABELS[str(raw.iloc[row]["Chip_Type"])]}
        for row, col in invalid_positions
    ], columns=["id", "allergen", "value", "chip"])
    # Preserve invalid measurements in raw_frame / invalid_values. A negative
    # concentration has no documented interpretation and must not become zero.
    values = values.mask(invalid_mask)
    frame = raw.loc[:, list(METADATA_COLUMNS)].copy()
    for column in ("Age", "Gender", "Blood_Month_sample", "Rural_or_urban_area", "Sensitization", "Skin_Symptoms"):
        frame[column] = pd.to_numeric(frame[column], errors="coerce").astype(float)
    frame = pd.concat([frame, values], axis=1)
    coverage = values.notna().groupby(raw["Chip_Type"]).any()
    coverage.index = coverage.index.map(CHIP_LABELS)
    coverage = coverage.reindex([chip for chip in CHIP_ORDER if chip in coverage.index])
    coverage.index.name = "chip"
    common = tuple(coverage.columns[coverage.all(axis=0)])
    frame = derive_columns(frame, allergens, common)
    frame["invalid_ige_count"] = invalid_mask.sum(axis=1).astype(int)
    structural = 0
    for chip in coverage.index:
        structural += int(frame["chip"].eq(chip).sum() * (~coverage.loc[chip]).sum())
    audit = {
        "patients": len(frame), "allergens": len(allergens), "common_allergens": len(common),
        "invalid_ige_cells": len(invalid), "patients_with_invalid_ige": int(invalid_mask.any(axis=1).sum()),
        "common_complete_patients": int(frame["common_complete"].sum()),
        "common_incomplete_patients": int((~frame["common_complete"]).sum()),
        "structural_missing_cells": structural,
        "has_severity": "Severe_Allergy" in raw.columns,
        "chip_counts": frame["chip"].value_counts().to_dict(),
        "coverage_counts": coverage.sum(axis=1).astype(int).to_dict(),
    }
    return Dataset(frame, allergens, common, coverage, clinical_quality(frame), Path(path), raw, invalid, audit)
