"""Reproducible exploratory IgE profiles, with no clinical training features."""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import chi2_contingency
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.metrics import normalized_mutual_info_score, silhouette_score
from sklearn.preprocessing import StandardScaler
from threadpoolctl import threadpool_limits

from .data_loader import DEFAULT_SOURCE, load_data

RANDOM_STATE = 42


@dataclass(frozen=True)
class ProfileResult:
    frame: pd.DataFrame
    scores: pd.DataFrame
    best_k: int
    k: int
    explained_variance: tuple[float, ...]
    standardized: pd.DataFrame
    labels: pd.Series
    fingerprints: pd.DataFrame
    cluster_sizes: pd.DataFrame
    platform_cramers_v: float
    platform_nmi: float
    excluded_count: int
    within_chip: bool
    method: str


def platform_association(chips: pd.Series, labels: pd.Series) -> tuple[float, float]:
    """Descriptive Cramér's V and NMI, not a significance/causal conclusion."""
    valid = chips.notna() & labels.notna()
    chips, labels = chips.loc[valid], labels.loc[valid]
    table = pd.crosstab(chips, labels)
    if not len(chips) or min(table.shape, default=0) < 2:
        return np.nan, np.nan
    statistic = chi2_contingency(table, correction=False)[0]
    denominator = len(chips) * min(table.shape[0] - 1, table.shape[1] - 1)
    return float(np.sqrt(statistic / denominator)), float(normalized_mutual_info_score(chips, labels))


def standardize_ige(frame: pd.DataFrame, allergens: tuple[str, ...], within_chip: bool = True) -> pd.DataFrame:
    """Complete cases only; no structural missingness or invalid sentinel imputation.

    Scaling within each chip reduces mean/variance platform differences, but may
    also remove cohort differences. This is a sensitivity choice, not assay
    calibration. Scaling cannot make platform units clinically interchangeable.
    """
    raw = frame.loc[:, list(allergens)]
    valid = raw.notna().all(axis=1) & raw.ge(0).all(axis=1)
    values = np.log1p(raw.loc[valid].astype(float))
    standardized = pd.DataFrame(index=values.index, columns=values.columns, dtype=float)
    if values.empty:
        return standardized
    if within_chip:
        for chip in frame.loc[valid, "chip"].unique():
            rows = frame.loc[valid, "chip"].eq(chip)
            standardized.loc[rows.index[rows], :] = StandardScaler().fit_transform(values.loc[rows.index[rows]])
    else:
        standardized.loc[:, :] = StandardScaler().fit_transform(values)
    return standardized


def get_profiles(k: int | None = None, within_chip: bool = True, path: str | Path | None = None) -> ProfileResult:
    """Cache all K=2..8 solutions once per scaling mode/source version.

    .frame includes ALL patients; excluded patients have cluster='Non attribué'
    and missing PC coordinates. .standardized/.labels share original row index.
    """
    source = Path(path).resolve() if path is not None else DEFAULT_SOURCE
    stat = source.stat()
    results, best_k = _fit_profiles(str(source), stat.st_mtime_ns, stat.st_size, bool(within_chip))
    chosen = best_k if k is None else int(k)
    if chosen not in results:
        raise ValueError(f"K doit appartenir aux solutions disponibles : {sorted(results)}")
    return results[chosen]


@lru_cache(maxsize=4)
def _fit_profiles(path: str, modified: int, size: int, within_chip: bool) -> tuple[dict[int, ProfileResult], int]:
    dataset = load_data(path)
    standardized = standardize_ige(dataset.frame, dataset.common_allergens, within_chip)
    if len(standardized) < 3 or standardized.shape[1] < 2:
        raise ValueError("La PCA et le clustering nécessitent au moins trois profils IgE complets et deux variables communes.")
    matrix = standardized.to_numpy(dtype=float)
    sample_size = min(1500, len(matrix))
    rng = np.random.default_rng(RANDOM_STATE)
    sample = np.sort(rng.choice(len(matrix), size=sample_size, replace=False))
    labels_by_k, score_rows = {}, []
    with threadpool_limits(limits=2):
        pca = PCA(n_components=2, svd_solver="full")
        projection = pca.fit_transform(matrix)
        distinct = np.unique(matrix, axis=0).shape[0]
        for k in range(2, min(8, len(matrix) - 1, distinct) + 1):
            model = KMeans(n_clusters=k, n_init=10, random_state=RANDOM_STATE, algorithm="lloyd")
            raw_labels = model.fit_predict(matrix)
            # Stable display ordering by observed common detection burden.
            counts = dataset.frame.loc[standardized.index, "common_count"]
            burden = counts.groupby(raw_labels).mean().sort_values(kind="stable")
            mapping = {old: str(new) for new, old in enumerate(burden.index, start=1)}
            labels = pd.Series([mapping[label] for label in raw_labels], index=standardized.index, name="cluster")
            sampled_labels = labels.iloc[sample]
            n_sample_clusters = sampled_labels.nunique()
            silhouette = (float(silhouette_score(matrix[sample], sampled_labels))
                          if 1 < n_sample_clusters < len(sample) else np.nan)
            sizes = labels.value_counts()
            v, nmi = platform_association(dataset.frame.loc[labels.index, "chip"], labels)
            labels_by_k[k] = labels
            score_rows.append({"k": k, "silhouette": silhouette, "sample_n": sample_size,
                               "smallest_cluster": int(sizes.min()), "largest_cluster": int(sizes.max()),
                               "platform_cramers_v": v, "platform_nmi": nmi})
    scores = pd.DataFrame(score_rows)
    if scores.empty:
        raise ValueError("Pas assez de profils IgE distincts pour KMeans.")
    ranked = scores.sort_values(["silhouette", "k"], ascending=[False, True], na_position="last")
    best_k = int(ranked.iloc[0]["k"])
    explained = tuple(float(value) for value in pca.explained_variance_ratio_)
    method = ("91 IgE communes" if len(dataset.common_allergens) == 91 else f"{len(dataset.common_allergens)} IgE communes")
    method += "; cas complets; log1p; standardisation " + ("par technologie" if within_chip else "globale")
    method += "; KMeans dans toutes les dimensions; PCA 2D pour la vue; K choisi par silhouette sur échantillon fixe (n ≤ 1 500)."
    results = {}
    for k, labels in labels_by_k.items():
        frame = dataset.frame.copy()
        frame["pc1"] = np.nan
        frame["pc2"] = np.nan
        frame["cluster"] = "Non attribué"
        frame.loc[standardized.index, ["pc1", "pc2"]] = projection
        frame.loc[labels.index, "cluster"] = labels
        score = scores.loc[scores["k"].eq(k)].iloc[0]
        fingerprints = standardized.groupby(labels).mean()
        sizes = labels.value_counts().sort_index().rename_axis("cluster").reset_index(name="n")
        results[k] = ProfileResult(
            frame=frame, scores=scores, best_k=best_k, k=k, explained_variance=explained,
            standardized=standardized, labels=labels, fingerprints=fingerprints, cluster_sizes=sizes,
            platform_cramers_v=float(score["platform_cramers_v"]), platform_nmi=float(score["platform_nmi"]),
            excluded_count=len(frame) - len(standardized), within_chip=within_chip, method=method,
        )
    return results, best_k
