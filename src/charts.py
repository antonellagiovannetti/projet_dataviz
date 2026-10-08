"""Figures for Allergy Atlas, with observed denominators and explicit missingness.

Chart factories never mutate source data. Detection means strictly ``IgE > 0``;
the source sensitization flag is kept separate from that derived measurement.
"""
from __future__ import annotations

from collections.abc import Sequence
import textwrap

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

INK = "#182c47"
TEAL = "#168b87"
VIOLET = "#8580bb"
MUTED = "#81909f"
GRID = "#edf1f5"
COLORS = [TEAL, VIOLET, "#e5a768", "#4a7fba", "#b2749c", "#7ba573", "#bb8c65", "#64758c"]
CHIP_COLORS = {"ISAC V1": INK, "ISAC V2": VIOLET, "ALEX": TEAL}
CLINICAL_LABELS = {
    "skin": "Symptômes cutanés", "asthma": "Traitement de l’asthme",
    "rhinitis": "Traitement de la rhinite", "dermatitis": "Traitement de la dermatite",
    "sex": "Sexe", "age": "Âge", "age_group": "Classe d’âge",
    "sensitization": "Sensibilisation (source)", "cluster": "Profil",
    "rural": "Zone rurale / urbaine", "onset": "Âge de début",
}
CLINICAL_ALIASES = {
    "Skin_Symptoms": "skin", "Treatment_of_athsma": "asthma",
    "Treatment_of_rhinitis": "rhinitis", "Treatment_of_atopic_dematitis": "dermatitis",
}


def _base(fig: go.Figure, height: int = 330, *, left: int = 52, bottom: int = 48) -> go.Figure:
    fig.update_layout(
        template="plotly_white", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, Segoe UI, sans-serif", color=INK, size=12),
        height=height, margin=dict(l=left, r=24, t=26, b=bottom),
        hoverlabel=dict(bgcolor="white", font_size=12, font_family="Inter, Segoe UI, sans-serif"),
        legend=dict(orientation="h", y=1.13, x=0, font_size=11),
        modebar=dict(color=MUTED, activecolor=TEAL),
        uirevision="allergy-atlas", transition=dict(duration=200),
    )
    fig.update_xaxes(showgrid=False, zeroline=False, automargin=True, linecolor=GRID, tickfont_size=11)
    fig.update_yaxes(gridcolor=GRID, zeroline=False, automargin=True, tickfont_size=11)
    return fig


def empty_figure(message: str = "Aucun patient ne correspond à cette sélection.", height: int = 330) -> go.Figure:
    fig = _base(go.Figure(), height)
    fig.update_xaxes(visible=False)
    fig.update_yaxes(visible=False)
    fig.add_annotation(text="<br>".join(textwrap.wrap(message, width=34)), x=.5, y=.5, xref="paper", yref="paper", showarrow=False,
                       font=dict(color=MUTED, size=13), align="center")
    return fig


def _note(fig: go.Figure, text: str, y: float = 1.07) -> None:
    lines = textwrap.wrap(text, width=36)
    fig.update_layout(margin_t=max(fig.layout.margin.t or 26, 22 + len(lines)*12))
    fig.add_annotation(text="<br>".join(lines), x=0, y=1.025 if y <= 1.1 else y, xref="paper", yref="paper", showarrow=False,
                       xanchor="left", yanchor="bottom", align="left", font=dict(size=10, color=MUTED))


def _fmt(n: float | int) -> str:
    return f"{n:,.0f}".replace(",", " ")


def _name(name: str) -> str:
    return str(name).replace("_", " ")


def _column(df: pd.DataFrame, name: str) -> pd.Series:
    return df[name] if name in df else pd.Series(index=df.index, dtype="object")


def _known(s: pd.Series) -> pd.Series:
    return s.notna() & ~s.astype(str).str.strip().str.lower().isin(
        ["inconnu", "inconnue", "unknown", "nan", "none", "<na>", "9", "9.0", ""]
    )


def _clinical(df: pd.DataFrame, col: str) -> pd.Series:
    key = CLINICAL_ALIASES.get(col, col)
    if key in df:
        return df[key].fillna("Inconnu")
    raw = _column(df, col)
    numeric = pd.to_numeric(raw, errors="coerce")
    return pd.Series(np.where(numeric.isna() | numeric.eq(9), "Inconnu",
                             np.where(numeric.eq(0), "Non", "Oui")), index=df.index)


def _values(df: pd.DataFrame, allergens: Sequence[str]) -> pd.DataFrame:
    cols = [col for col in allergens if col in df]
    return df.loc[:, cols].apply(pd.to_numeric, errors="coerce")


def _stats(df: pd.DataFrame, allergens: Sequence[str], threshold: float = 0) -> pd.DataFrame:
    values = _values(df, allergens)
    n = values.notna().sum()
    positive = values.gt(threshold).sum()
    return pd.DataFrame({"n": n, "positive": positive, "prevalence": positive.div(n.replace(0, np.nan)) * 100,
                         "mean": values.mean(), "median": values.median()})


def _wilson(positive, n):
    """Wilson 95% intervals; empty denominators stay NaN, never become 0%."""
    n = np.asarray(n, dtype=float)
    positive = np.asarray(positive, dtype=float)
    n = np.where(n > 0, n, np.nan)
    p = positive / n
    z = 1.959963984540054
    center = (p + z * z / (2 * n)) / (1 + z * z / n)
    half = z / (1 + z * z / n) * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return (center - half) * 100, (center + half) * 100


def common_count_histogram(df: pd.DataFrame) -> go.Figure:
    values = pd.to_numeric(_column(df, "common_count"), errors="coerce").dropna()
    if values.empty:
        return empty_figure("Aucun profil complet sur les allergènes communs.")
    hi = max(10, int(values.max()))
    width = 2 if hi <= 40 else 3
    edges = np.arange(-.5, hi + width + 1, width)
    counts, edges = np.histogram(values, bins=edges)
    lower = np.ceil(edges[:-1]).astype(int)
    upper = np.floor(edges[1:]).astype(int)
    fig = go.Figure(go.Bar(x=(lower + upper) / 2, y=counts, width=width * .87,
                          marker=dict(color=TEAL, line_width=0),
                          customdata=np.c_[lower, upper, counts / len(values) * 100],
                          hovertemplate="<b>%{customdata[0]}–%{customdata[1]} IgE détectées</b>"
                                        "<br>%{y} patients (%{customdata[2]:.1f} %)"
                                        "<br>Allergènes communs · valeur > 0<extra></extra>"))
    q1, median, q3 = values.quantile([.25, .5, .75])
    fig.add_vrect(x0=q1, x1=q3, fillcolor=TEAL, opacity=.055, line_width=0, layer="below")
    fig.add_vline(x=median, line_color=INK, line_width=1.4, line_dash="dot")
    _base(fig, 320)
    _note(fig, f"Médiane {_fmt(median)} · Q1–Q3 : {_fmt(q1)}–{_fmt(q3)} · n = {_fmt(len(values))}")
    fig.update_layout(dragmode="select", selectdirection="h", bargap=.1)
    fig.update_xaxes(title="IgE détectées · panel commun", range=[-.7, edges[-1]])
    fig.update_yaxes(title="Patients", rangemode="tozero")
    return fig


def chip_bars(df: pd.DataFrame) -> go.Figure:
    if df.empty:
        return empty_figure()
    counts = _column(df, "chip").value_counts().reindex(["ISAC V1", "ISAC V2", "ALEX"], fill_value=0)
    fig = go.Figure(go.Bar(x=counts.index, y=counts.values,
                          marker_color=[CHIP_COLORS[x] for x in counts.index], width=.48,
                          text=[_fmt(v) for v in counts.values], textposition="outside", cliponaxis=False,
                          customdata=np.c_[counts.index, counts.values / max(len(df), 1) * 100],
                          hovertemplate="<b>%{customdata[0]}</b><br>%{y} patients"
                                        "<br>%{customdata[1]:.1f} % de la sélection"
                                        "<br>Cliquer pour filtrer<extra></extra>"))
    _base(fig, 290)
    fig.update_yaxes(title="Patients", range=[0, max(1, counts.max()) * 1.2])
    return fig


def coverage_heatmap(coverage_df: pd.DataFrame, sort_by: str = "common") -> go.Figure:
    if coverage_df.empty:
        return empty_figure("Couverture des plateformes indisponible.")
    coverage = coverage_df.copy().fillna(False).astype(bool)
    order = [x for x in ["ISAC V1", "ISAC V2", "ALEX"] if x in coverage.index]
    if order:
        coverage = coverage.reindex(order)
    common = coverage.all(axis=0)
    alex = coverage.loc["ALEX"] if "ALEX" in coverage.index else pd.Series(False, index=coverage.columns)
    isac = coverage.loc[[c for c in coverage.index if "ISAC" in c]].any(axis=0)
    sort_key = {
        col: (0 if common[col] else (1 if alex[col] and not isac[col] else 2), col)
        for col in coverage.columns
    }
    if str(sort_by).lower() in ["alex", "alex_only", "specific_alex"]:
        sort_key = {col: (not (alex[col] and not isac[col]), not common[col], col) for col in coverage.columns}
    elif str(sort_by).lower() in ["isac", "isac_only", "specific_isac"]:
        sort_key = {col: (not (isac[col] and not alex[col]), not common[col], col) for col in coverage.columns}
    cols = sorted(coverage.columns, key=lambda c: sort_key[c])
    coverage = coverage.loc[:, cols]
    custom = np.empty((len(coverage), len(cols), 3), dtype=object)
    for row, chip in enumerate(coverage.index):
        for j, col in enumerate(cols):
            custom[row, j] = [col, "Mesuré" if coverage.loc[chip, col] else "Non mesuré", "Panel commun" if common[col] else "Panel partiel"]
    fig = go.Figure(go.Heatmap(x=cols, y=list(coverage.index), z=coverage.astype(int).values,
                              customdata=custom, zmin=0, zmax=1,
                              colorscale=[[0, "#eef1f5"], [.499, "#eef1f5"], [.5, TEAL], [1, TEAL]],
                              showscale=False, xgap=.4, ygap=5,
                              hovertemplate="<b>%{customdata[0]}</b><br>%{y} : %{customdata[1]}"
                                            "<br>%{customdata[2]}<extra></extra>"))
    _base(fig, 225, left=72, bottom=45)
    fig.update_xaxes(showticklabels=False, title=f"{len(cols)} allergènes · survoler pour le détail", showgrid=False)
    fig.update_yaxes(autorange="reversed", showgrid=False)
    _note(fig, f"{int(common.sum())} communs · turquoise : mesuré · gris : absent du panel")
    return fig


def clinical_missingness(df: pd.DataFrame, show_missing: bool = True) -> go.Figure:
    if df.empty:
        return empty_figure()
    specs = [("age", "Âge"), ("sex", "Sexe"), ("Rural_or_urban_area", "Zone rurale / urbaine"),
             ("skin", "Symptômes cutanés"), ("rhinitis", "Traitement rhinite"),
             ("asthma", "Traitement asthme"), ("Age_of_onsets", "Âge de début"),
             ("dermatitis", "Traitement dermatite")]
    rows = []
    for col, label in specs:
        series = _column(df, col)
        valid = series.notna() if col == "age" else _known(series)
        missing = int((~valid).sum())
        value = missing if show_missing else len(df) - missing
        rows.append((label, 100 * value / len(df), value, len(df) - missing))
    rows.sort(key=lambda x: x[1])
    state = "inconnus ou manquants" if show_missing else "renseignés"
    fig = go.Figure(go.Bar(x=[r[1] for r in rows], y=[r[0] for r in rows], orientation="h",
                          marker_color=VIOLET if show_missing else TEAL, width=.6,
                          text=[f"{r[1]:.0f} %" for r in rows], textposition="outside", cliponaxis=False,
                          customdata=[[r[2], r[3]] for r in rows],
                          hovertemplate=f"<b>%{{y}}</b><br>%{{customdata[0]}} / {_fmt(len(df))} {state}"
                                        "<br>%{customdata[1]} observations disponibles<extra></extra>"))
    _base(fig, 350, left=160)
    fig.update_xaxes(title="Non renseigné (%)" if show_missing else "Renseigné (%)", range=[0, 111], ticksuffix=" %")
    fig.update_yaxes(showgrid=False)
    return fig


def top_allergens(df: pd.DataFrame, allergens: Sequence[str], metric: str = "prevalence",
                  threshold: float = 0, top_n: int = 15, selected_allergen: str | None = None) -> go.Figure:
    metric = {"mean_ige": "mean", "median_ige": "median"}.get(metric, metric)
    if metric not in ["prevalence", "mean", "median"]:
        metric = "prevalence"
    stats = _stats(df, allergens, threshold).dropna(subset=[metric]).nlargest(top_n, metric).iloc[::-1]
    if stats.empty:
        return empty_figure("Aucune mesure IgE disponible pour cette sélection.")
    custom = [[col, row["positive"], row["n"], row["prevalence"], row["mean"], row["median"], len(stats) - i]
              for i, (col, row) in enumerate(stats.iterrows())]
    error = None
    if metric == "prevalence":
        low, high = _wilson(stats.positive, stats.n)
        error = dict(type="data", symmetric=False, array=high - stats.prevalence,
                     arrayminus=stats.prevalence - low, color=MUTED, thickness=1, width=2)
    fig = go.Figure(go.Bar(x=stats[metric], y=[_name(c) for c in stats.index], orientation="h",
                          marker_color=[INK if c == selected_allergen else TEAL for c in stats.index],
                          width=.65, customdata=custom, error_x=error,
                          hovertemplate="<b>%{customdata[0]}</b> · rang %{customdata[6]}"
                                        "<br>IgE détectée : %{customdata[3]:.1f} %"
                                        "<br>%{customdata[1]:.0f} / %{customdata[2]:.0f} valeurs observées"
                                        "<br>Moyenne : %{customdata[4]:.2f} · médiane : %{customdata[5]:.2f}"
                                        "<br>Valeurs source, unités propres aux puces<extra></extra>"))
    _base(fig, max(340, top_n * 22 + 80), left=104)
    titles = {"prevalence": "Fréquence de détection (%)", "mean": "IgE moyenne · valeur source", "median": "IgE médiane · valeur source"}
    fig.update_xaxes(title=titles[metric], rangemode="tozero", ticksuffix=" %" if metric == "prevalence" else "")
    fig.update_yaxes(showgrid=False)
    if metric == "prevalence":
        fig.update_xaxes(range=[0, min(105, max(10, float(high.max()) * 1.1))])
        _note(fig, "Barres fines : IC 95 % de Wilson · dénominateur propre à chaque allergène")
    else:
        _note(fig, "Unités propres aux plateformes ; les concentrations ne sont pas harmonisées.")
    return fig


def _age_spec(mode: str):
    if mode == "broad":
        return [(0, 17, "0–17"), (18, 50, "18–50"), (51, 120, "51+")]
    return [(0, 5, "0–5"), (6, 12, "6–12"), (13, 17, "13–17"), (18, 30, "18–30"), (31, 50, "31–50"), (51, 120, "51+")]


def age_groups(df: pd.DataFrame, mode: str = "standard") -> go.Figure:
    ages = pd.to_numeric(_column(df, "age"), errors="coerce")
    if ages.dropna().empty:
        return empty_figure("Aucun âge renseigné dans cette sélection.")
    data = []
    for low, high, label in _age_spec(mode):
        part = df.loc[ages.between(low, high)]
        sens = _column(part, "sensitized").dropna()
        positive = int(sens.astype(bool).sum())
        n = len(sens)
        med = pd.to_numeric(_column(part, "common_count"), errors="coerce").dropna()
        interval = _wilson(positive, n)
        q = med.quantile([.25, .5, .75])
        data.append(dict(low=low, high=high, label=label, count=len(part), n=n, positive=positive,
                         pct=positive / n * 100 if n else np.nan, ci_low=float(interval[0]), ci_high=float(interval[1]),
                         median=q.iloc[1], q1=q.iloc[0], q3=q.iloc[2], measured=len(med)))
    table = pd.DataFrame(data)
    custom = table[["low", "high", "count", "n", "positive", "measured"]].values
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=.17)
    fig.add_trace(go.Scatter(x=table.label, y=table.pct, mode="lines+markers", line=dict(color=TEAL, width=2.5),
                             marker=dict(size=9, color=TEAL), customdata=custom,
                             error_y=dict(type="data", symmetric=False, array=table.ci_high - table.pct,
                                          arrayminus=table.pct - table.ci_low, color=TEAL, thickness=1, width=3),
                             hovertemplate="<b>%{x} ans</b><br>Sensibilisation (source) : %{y:.1f} %"
                                           "<br>%{customdata[4]} / %{customdata[3]} statuts renseignés"
                                           "<br>Classe : %{customdata[2]} patients<extra></extra>", showlegend=False), row=1, col=1)
    fig.add_trace(go.Scatter(x=table.label, y=table["median"], mode="lines+markers", line=dict(color=VIOLET, width=2.5),
                             marker=dict(size=9, color=VIOLET), customdata=custom,
                             error_y=dict(type="data", symmetric=False, array=table.q3 - table["median"],
                                          arrayminus=table["median"] - table.q1, color=VIOLET, thickness=1, width=3),
                             hovertemplate="<b>%{x} ans</b><br>IgE détectées, médiane : %{y:.1f}"
                                           "<br>%{customdata[5]} profils complets sur le panel commun"
                                           "<br>Barres : quartiles Q1–Q3<extra></extra>", showlegend=False), row=2, col=1)
    _base(fig, 375, left=60, bottom=43)
    fig.update_yaxes(title="Sensibilisés (%)", range=[0, 105], row=1, col=1)
    fig.update_yaxes(title="IgE · médiane", rangemode="tozero", row=2, col=1)
    fig.update_xaxes(title="Classe d’âge (ans)", row=2, col=1)
    _note(fig, f"Âge connu : n = {_fmt(int(ages.notna().sum()))} · haut : IC 95 % · bas : Q1–Q3")
    return fig


def _stratified_sample(df: pd.DataFrame, maximum: int) -> pd.DataFrame:
    if len(df) <= maximum:
        return df.copy()
    strata = [c for c in ["chip", "cluster"] if c in df]
    if not strata:
        return df.sample(n=maximum, random_state=42)
    grouped = list(df.groupby(strata, dropna=False, observed=True, sort=True))
    target = np.array([len(g) for _, g in grouped]) * maximum / len(df)
    allocations = np.floor(target).astype(int)
    for i in np.argsort(-(target - allocations), kind="stable")[: maximum - allocations.sum()]:
        allocations[i] += 1
    return pd.concat([g.sample(n=int(n), random_state=42) for (_, g), n in zip(grouped, allocations) if n])


def patient_heatmap(df: pd.DataFrame, allergens: Sequence[str], max_patients: int = 120,
                    threshold: float = 0, selected_allergen: str | None = None, sort_by: str = "count") -> go.Figure:
    if df.empty:
        return empty_figure()
    sample = _stratified_sample(df, min(120, max(1, max_patients)))
    ordering = ["cluster", "common_count", "id"] if sort_by == "cluster" else ["common_count", "id"]
    sort_cols = [c for c in ordering if c in sample]
    if sort_cols:
        sample = sample.sort_values(sort_cols, kind="stable")
    values = _values(sample, allergens)
    if values.empty:
        return empty_figure("Aucun allergène disponible pour cette sélection.")
    # Rank columns on the full selected cohort, not on a possibly unrepresentative sample.
    cols = _stats(df, values.columns, threshold).sort_values("prevalence", ascending=False).index.tolist()
    values = values.loc[:, cols]
    ids = _column(sample, "id").astype(str).to_numpy()
    custom = np.empty((len(sample), len(cols), 3), dtype=object)
    custom[:, :, 0] = ids[:, None]
    custom[:, :, 1] = np.asarray(cols)[None, :]
    custom[:, :, 2] = values.to_numpy()
    fig = go.Figure(go.Heatmap(z=np.log1p(values.clip(lower=0)).to_numpy(), x=cols,
                              y=np.arange(len(sample)), customdata=custom,
                              colorscale=[[0, "#f0f4f7"], [.12, "#c4e0de"], [.45, "#58aea5"], [1, INK]],
                              colorbar=dict(title="log(1 + IgE)", thickness=10, len=.78, tickfont_size=10),
                              hoverongaps=False, zmin=0,
                              hovertemplate="<b>%{customdata[0]} · %{customdata[1]}</b>"
                                            "<br>IgE : %{customdata[2]:.2f} (valeur source)"
                                            "<br>log(1 + IgE) : %{z:.2f}<extra></extra>"))
    _base(fig, 405, left=40, bottom=80)
    every = max(1, int(np.ceil(len(cols) / 15)))
    ticks = cols[::every]
    if selected_allergen in cols and selected_allergen not in ticks:
        ticks.append(selected_allergen)
    fig.update_xaxes(tickmode="array", tickvals=ticks, ticktext=[_name(c) for c in ticks], tickangle=-45,
                     title="Allergènes · triés par fréquence de détection", tickfont_size=9)
    fig.update_yaxes(title="Patients", showticklabels=False, autorange="reversed", showgrid=False)
    kind = "Échantillon stratifié" if len(sample) < len(df) else "Sélection complète"
    _note(fig, f"{kind} : {_fmt(len(sample))} / {_fmt(len(df))} patients · {len(cols)} allergènes · unités source")
    return fig


def _difference(a: pd.DataFrame, b: pd.DataFrame, allergens: Sequence[str], threshold: float,
                 top_n: int, labels: tuple[str, str], *, direction: str = "a_minus_b",
                 interval: bool = True) -> go.Figure:
    if a.empty or b.empty:
        return empty_figure("Les deux groupes doivent contenir au moins un patient renseigné.", 420)
    sa, sb = _stats(a, allergens, threshold), _stats(b, allergens, threshold)
    stats = sa.add_suffix("_a").join(sb.add_suffix("_b")).dropna(subset=["prevalence_a", "prevalence_b"])
    if stats.empty:
        return empty_figure("Aucune mesure commune observée dans les deux groupes.", 420)
    sign = 1 if direction == "a_minus_b" else -1
    stats["difference"] = sign * (stats.prevalence_a - stats.prevalence_b)
    stats = stats.loc[stats.difference.abs().nlargest(top_n).index].sort_values("difference")
    a_low, a_high = _wilson(stats.positive_a, stats.n_a)
    b_low, b_high = _wilson(stats.positive_b, stats.n_b)
    # Newcombe independent-proportion intervals derived from Wilson score intervals.
    lower = np.sqrt((stats.prevalence_a - a_low) ** 2 + (b_high - stats.prevalence_b) ** 2)
    upper = np.sqrt((a_high - stats.prevalence_a) ** 2 + (stats.prevalence_b - b_low) ** 2)
    if sign < 0:
        lower, upper = upper, lower
    custom = [[c, r.prevalence_a, r.prevalence_b, r.positive_a, r.n_a, r.positive_b, r.n_b]
              for c, r in stats.iterrows()]
    error = dict(type="data", symmetric=False, array=upper, arrayminus=lower,
                 color=MUTED, thickness=1, width=2) if interval else None
    fig = go.Figure(go.Bar(x=stats.difference, y=[_name(c) for c in stats.index], orientation="h", width=.6,
                          marker_color=[TEAL if d >= 0 else VIOLET for d in stats.difference],
                          customdata=custom, error_x=error,
                          hovertemplate="<b>%{customdata[0]}</b>"
                                        f"<br>{labels[0]} : %{{customdata[1]:.1f}} % (%{{customdata[3]:.0f}} / %{{customdata[4]:.0f}})"
                                        f"<br>{labels[1]} : %{{customdata[2]:.1f}} % (%{{customdata[5]:.0f}} / %{{customdata[6]:.0f}})"
                                        "<br>Différence : %{x:+.1f} points<extra></extra>"))
    _base(fig, max(380, top_n * 23 + 105), left=110, bottom=65)
    max_abs = max(float((stats.difference - (lower if interval else 0)).abs().max()),
                  float((stats.difference + (upper if interval else 0)).abs().max()), 5)
    fig.update_xaxes(range=[-max_abs * 1.12, max_abs * 1.12], title="Écart de détection (points de pourcentage)", showgrid=True)
    fig.update_yaxes(showgrid=False)
    fig.add_vline(x=0, line_color="#b8c1cb", line_width=1)
    suffix = " · IC 95 % exploratoires, non ajustés" if interval else " · comparaison descriptive"
    _note(fig, f"{labels[0]} : n = {_fmt(len(a))} · {labels[1]} : n = {_fmt(len(b))}{suffix}")
    return fig


def clinical_differential(df: pd.DataFrame, clinical_col: str, allergens: Sequence[str],
                          threshold: float = 0, top_n: int = 15) -> go.Figure:
    statuses = _clinical(df, clinical_col)
    a, b = df.loc[statuses.eq("Oui")], df.loc[statuses.eq("Non")]
    fig = _difference(a, b, allergens, threshold, top_n, ("Présence", "Absence"))
    if not a.empty and not b.empty:
        fig.update_xaxes(title="Écart Oui − Non (points)")
        fig.update_layout(margin_b=90)
        unknown = int((~statuses.isin(["Oui", "Non"])).sum())
        fig.add_annotation(text=f"Non renseignés exclus : n = {_fmt(unknown)}",
                           x=0, y=0, yshift=-60, yanchor="top", xref="paper", yref="paper", xanchor="left", showarrow=False,
                           font=dict(size=10, color=MUTED))
    return fig


def clinical_composition(df: pd.DataFrame, clinical_col: str, dimension: str = "sex",
                          show_missing: bool = True) -> go.Figure:
    if df.empty:
        return empty_figure()
    dimension = {"age": "age_group", "sensitized": "sensitization"}.get(dimension, dimension)
    groups = _column(df, dimension).fillna("Inconnu").astype(str)
    statuses = _clinical(df, clinical_col)
    table = pd.crosstab(groups, statuses).reindex(columns=["Non", "Oui", "Inconnu"], fill_value=0)
    if not show_missing:
        table = table.loc[:, ["Non", "Oui"]]
    table = table.loc[table.sum(axis=1).gt(0)]
    if table.empty:
        return empty_figure("Aucun statut clinique renseigné dans ces groupes.")
    if dimension == "age_group":
        desired = [a[2] for a in _age_spec("standard")]
        table = table.reindex([x for x in desired if x in table.index] + [x for x in table.index if x not in desired])
    totals = table.sum(axis=1)
    colors = {"Non": "#d5dde7", "Oui": TEAL, "Inconnu": VIOLET}
    fig = go.Figure()
    for status in table.columns:
        fig.add_trace(go.Bar(x=table.index, y=table[status] / totals * 100, name=status,
                             marker_color=colors[status], width=.58,
                             customdata=np.c_[table[status], totals],
                             hovertemplate=f"<b>%{{x}} · {status}</b><br>%{{y:.1f}} %"
                                           "<br>%{customdata[0]} / %{customdata[1]} patients<extra></extra>"))
    _base(fig, 340, bottom=60)
    fig.update_layout(barmode="stack", legend=dict(y=1.15))
    fig.update_xaxes(title=CLINICAL_LABELS.get(dimension, _name(dimension)), tickmode="array", tickvals=table.index,
                     ticktext=[f"{label}<br><span style='color:{MUTED}'>n={_fmt(totals[label])}</span>" for label in table.index])
    fig.update_yaxes(title="Composition clinique (%)", range=[0, 100], ticksuffix=" %")
    return fig


def parallel_categories(df: pd.DataFrame, dimensions: Sequence[str] | None = None) -> go.Figure:
    dimensions = list(dimensions or ["age_group", "sensitization", "skin", "asthma"])
    if any(col not in df for col in dimensions):
        return empty_figure("Variables nécessaires aux trajectoires indisponibles.", 350)
    complete = pd.Series(True, index=df.index)
    for col in dimensions:
        complete &= _known(df[col])
    selected = df.loc[complete, dimensions].astype(str)
    if selected.empty:
        return empty_figure("Aucun cas complet sur toutes les variables de la trajectoire.", 350)
    # Aggregate identical paths to keep the browser payload small.
    patterns = selected.groupby(dimensions, observed=True).size().reset_index(name="count")
    colors = (patterns[dimensions[-1]].eq("Oui")).astype(int)
    axes = []
    for col in dimensions:
        axis = dict(label=CLINICAL_LABELS.get(col, _name(col)), values=patterns[col])
        if col == "age_group":
            axis.update(categoryorder="array", categoryarray=[item[2] for item in _age_spec("standard")])
        elif col in ["sensitization", "skin", "asthma", "rhinitis", "dermatitis"]:
            axis.update(categoryorder="array", categoryarray=["Non", "Oui"])
        axes.append(axis)
    fig = go.Figure(go.Parcats(dimensions=axes,
                              counts=patterns["count"], line=dict(color=colors, colorscale=[[0, "#b9c5d4"], [1, TEAL]]),
                              labelfont=dict(family="Inter, Segoe UI", size=11, color=INK),
                              tickfont=dict(family="Inter, Segoe UI", size=10, color=MUTED),
                              arrangement="freeform", hoveron="color", hoverinfo="count+probability"))
    _base(fig, 360, left=35, bottom=35)
    fig.update_layout(margin_t=65, margin_r=45)
    _note(fig, f"Cas complets : n = {_fmt(len(selected))} / {_fmt(len(df))} · {_fmt(len(df) - len(selected))} exclus", y=1.18)
    return fig


def pca_scatter(projection_df: pd.DataFrame, explained_variance: Sequence[float] | None = None) -> go.Figure:
    df = projection_df
    if df.empty or not all(c in df for c in ["pc1", "pc2", "cluster"]):
        return empty_figure("Projection indisponible pour cette sélection.", 465)
    df = df.dropna(subset=["pc1", "pc2", "cluster"])
    if df.empty:
        return empty_figure("Aucun profil IgE complet projetable dans cette sélection.", 465)
    fig = go.Figure()
    symbols = {"ISAC V1": "circle", "ISAC V2": "diamond", "ALEX": "square"}
    clusters = sorted(df.cluster.dropna().astype(str).unique(), key=lambda x: (not x.isdigit(), int(x) if x.isdigit() else x))
    for i, cluster in enumerate(clusters):
        group = df.loc[df.cluster.astype(str).eq(cluster)]
        custom = pd.DataFrame({c: _column(group, c) for c in ["id", "age", "sex", "chip", "common_count", "cluster"]})
        fig.add_trace(go.Scattergl(x=group.pc1, y=group.pc2, mode="markers", name=f"Profil {cluster} · n = {_fmt(len(group))}",
                                   customdata=custom.astype(object).where(custom.notna(), "Inconnu").values,
                                   marker=dict(size=6, color=COLORS[((int(cluster) - 1) if cluster.isdigit() else i) % len(COLORS)], opacity=.68,
                                               symbol=[symbols.get(c, "circle") for c in _column(group, "chip")], line_width=0),
                                   selected=dict(marker=dict(opacity=1, size=8)), unselected=dict(marker=dict(opacity=.16)),
                                   hovertemplate="<b>%{customdata[0]} · profil %{customdata[5]}</b>"
                                                 "<br>Âge : %{customdata[1]} ans · %{customdata[2]}"
                                                 "<br>Puce : %{customdata[3]}"
                                                 "<br>IgE détectées (panel commun) : %{customdata[4]}"
                                                 "<br>PC1 : %{x:.2f} · PC2 : %{y:.2f}<extra></extra>"))
    _base(fig, 480, left=50, bottom=90)
    fig.update_layout(dragmode="lasso", legend=dict(y=1.1, font_size=10))
    labels = ["Composante principale 1", "Composante principale 2"]
    if explained_variance is not None and len(explained_variance) >= 2:
        labels = [f"PC{i + 1} · {100 * explained_variance[i]:.1f} % de variance" for i in [0, 1]]
    fig.update_xaxes(title=labels[0], showgrid=True)
    fig.update_yaxes(title=labels[1])
    fig.add_annotation(text=f"n = {_fmt(len(df))} patients projetés<br>○ ISAC V1 · ◇ ISAC V2 · □ ALEX",
                       x=0, y=0, yshift=-60, yanchor="top", xref="paper", yref="paper", showarrow=False, xanchor="left", align="left", font=dict(size=10, color=MUTED))
    return fig


def cluster_fingerprints(standardized: pd.DataFrame, labels, top_n: int = 25) -> go.Figure:
    if standardized.empty:
        return empty_figure("Aucune signature de profil disponible.", 340)
    frame = standardized.copy()
    # Positional input is accepted; a Series index must match the matrix index.
    cluster = labels.reindex(frame.index) if isinstance(labels, pd.Series) else pd.Series(labels, index=frame.index)
    cluster = cluster.astype("string")
    means = frame.groupby(cluster, observed=True).mean()
    counts = cluster.value_counts()
    if means.empty:
        return empty_figure("Aucun profil aligné avec les valeurs standardisées.")
    cols = means.var(axis=0, ddof=0).nlargest(min(top_n, len(means.columns))).index.tolist()
    means = means.loc[:, cols]
    lim = max(float(np.nanmax(np.abs(means.to_numpy()))), .1)
    custom = np.empty((len(means), len(cols), 3), dtype=object)
    for i, c in enumerate(means.index):
        for j, col in enumerate(cols):
            custom[i, j] = [str(c), col, int(counts.get(c, 0))]
    fig = go.Figure(go.Heatmap(x=cols, y=[f"Profil {c}" for c in means.index], z=means.values,
                              customdata=custom, colorscale=[[0, VIOLET], [.5, "#f8fafb"], [1, TEAL]],
                              zmin=-lim, zmax=lim, zmid=0, xgap=2, ygap=3,
                              colorbar=dict(title="Moyenne<br>standardisée", thickness=10, len=.7, tickfont_size=10),
                              hovertemplate="<b>Profil %{customdata[0]} · %{customdata[1]}</b>"
                                            "<br>Moyenne standardisée : %{z:.2f}"
                                            "<br>n = %{customdata[2]} patients<extra></extra>"))
    _base(fig, 350, left=70, bottom=95)
    fig.update_xaxes(ticktext=[_name(c) for c in cols], tickvals=cols, tickangle=-55, tickfont_size=9)
    fig.update_yaxes(showgrid=False, autorange="reversed")
    _note(fig, f"{len(cols)} allergènes les plus discriminants · moyenne de log(1 + IgE) standardisée")
    return fig


def cluster_excess(df: pd.DataFrame, allergens: Sequence[str], selected_cluster: str | int | None = None,
                    threshold: float = 0, top_n: int = 15, selected_df: pd.DataFrame | None = None) -> go.Figure:
    if df.empty or "cluster" not in df:
        return empty_figure("Aucun profil disponible pour cette sélection.")
    if selected_cluster is None:
        selected_cluster = str(df.cluster.mode().iloc[0])
    cohort = df if selected_df is None else selected_df
    selected = cohort.loc[cohort.cluster.astype(str).eq(str(selected_cluster))]
    fig = _difference(selected, df, allergens, threshold, top_n,
                      (f"Profil {selected_cluster}", "Population"), interval=False)
    if not selected.empty:
        fig.update_xaxes(title="Écart au total (points de pourcentage)")
    return fig


def cluster_platform_composition(df: pd.DataFrame) -> go.Figure:
    valid = df.loc[df.cluster.ne("Non attribué")]
    if valid.empty:
        return empty_figure("Aucun profil attribué dans la sélection.", 285)
    table = pd.crosstab(valid.cluster, valid.chip).sort_index()
    totals = table.sum(axis=1)
    fig = go.Figure()
    for chip in ["ISAC V1", "ISAC V2", "ALEX"]:
        counts = table[chip] if chip in table else pd.Series(0, index=table.index)
        fig.add_trace(go.Bar(x=[f"Profil {c}" for c in table.index], y=100*counts/totals,
                            name=chip, marker_color=CHIP_COLORS[chip],
                            customdata=np.c_[counts, totals],
                            hovertemplate=f"<b>%{{x}} · {chip}</b><br>%{{customdata[0]}} / %{{customdata[1]}} patients<br>%{{y:.1f}} %<extra></extra>"))
    _base(fig, 285)
    fig.update_layout(barmode="stack", legend=dict(y=1.12), margin_t=42)
    fig.update_yaxes(title="Composition du profil (%)", range=[0,100])
    return fig


def cohort_difference(a: pd.DataFrame, b: pd.DataFrame, allergens: Sequence[str],
                       threshold: float = 0, top_n: int = 15) -> go.Figure:
    # Saved cohorts can overlap: do not display independent-sample confidence intervals.
    fig = _difference(a, b, allergens, threshold, top_n, ("Cohorte A", "Cohorte B"),
                      direction="b_minus_a", interval=False)
    if not a.empty and not b.empty:
        fig.update_xaxes(title="← Cohorte A · écart B − A (points) · Cohorte B →")
        fig.update_layout(margin_b=100)
        overlap = len(set(_column(a, "id").dropna()) & set(_column(b, "id").dropna()))
        fig.add_annotation(text=f"Chevauchement : {_fmt(overlap)} patients<br>Dénominateurs IgE au survol",
                           x=0, y=0, yshift=-60, yanchor="top", xref="paper", yref="paper", showarrow=False, xanchor="left", align="left", font=dict(size=10, color=MUTED))
    return fig
