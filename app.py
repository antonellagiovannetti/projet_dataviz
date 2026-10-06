"""Narrative Dash application for the Allergen Chip Challenge dataset."""

from __future__ import annotations

from urllib.parse import parse_qs, urlencode

import numpy as np
import plotly.graph_objects as go
from dash import Dash, Input, Output, ctx, dcc, html, no_update
from flask import request

from acc_data import (
    AGE_GROUPS,
    CHIP_COLORS,
    CHIP_LABELS,
    CHIP_ORDER,
    COMPONENT_CUTOFF,
    AccBundle,
    age_breadth_summary,
    chip_coverage_summary,
    cohort_summary,
    component_age_summary,
    load_acc_data,
    sensitization_agreement,
    skin_age_standardized_summary,
    top_component_matrix,
)


PLOT_CONFIG = {
    "displayModeBar": False,
    "responsive": True,
    "scrollZoom": False,
}
CHIP_OPTIONS = [
    {"label": "Toutes les puces", "value": "all"},
    *[
        {"label": CHIP_LABELS[chip], "value": chip}
        for chip in CHIP_ORDER
    ],
]


try:
    DATA: AccBundle | None = load_acc_data()
    DATA_ERROR: str | None = None
except Exception as exc:  # The page shows a useful local-data setup message.
    DATA = None
    DATA_ERROR = str(exc)

if DATA is not None:
    COHORT = cohort_summary(DATA)
    AGE_SUMMARY = age_breadth_summary(DATA)
    SKIN_SUMMARY = skin_age_standardized_summary(DATA)
    AGREEMENT, AGREEMENT_RATE = sensitization_agreement(DATA)
else:
    COHORT = None
    AGE_SUMMARY = None
    SKIN_SUMMARY = None
    AGREEMENT = None
    AGREEMENT_RATE = None


def _base_figure(
    figure: go.Figure,
    *,
    height: int = 360,
    margin: dict[str, int] | None = None,
) -> go.Figure:
    figure.update_layout(
        template="plotly_white",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="#ffffff",
        font={
            "family": "Arial, Helvetica, sans-serif",
            "size": 13,
            "color": "#233133",
        },
        height=height,
        autosize=True,
        margin=margin or {"l": 36, "r": 24, "t": 28, "b": 48},
        hoverlabel={
            "bgcolor": "#ffffff",
            "bordercolor": "#d7dfdb",
            "font": {"color": "#233133", "size": 13},
        },
    )
    figure.update_xaxes(
        showline=False,
        zeroline=False,
        gridcolor="#edf0ee",
        automargin=True,
        tickfont={"size": 12},
    )
    figure.update_yaxes(
        showline=False,
        zeroline=False,
        gridcolor="#edf0ee",
        automargin=True,
        tickfont={"size": 12},
    )
    return figure


def _empty_figure(message: str, height: int = 300) -> go.Figure:
    figure = go.Figure()
    figure.add_annotation(
        text=message,
        x=0.5,
        y=0.5,
        xref="paper",
        yref="paper",
        showarrow=False,
        font={"size": 15, "color": "#617174"},
    )
    figure.update_xaxes(visible=False)
    figure.update_yaxes(visible=False)
    return _base_figure(figure, height=height)


def build_agreement_figure(bundle: AccBundle) -> go.Figure:
    counts, _ = sensitization_agreement(bundle)
    row_totals = counts.sum(axis=1).to_numpy()
    row_rates = counts.div(counts.sum(axis=1), axis=0) * 100
    x_labels = [
        "Aucun composant<br>au seuil",
        "Au moins un composant<br>au seuil",
    ]
    y_labels = [
        f"Non sensibilisé · n={int(row_totals[0]):,}".replace(",", " "),
        f"Sensibilisé · n={int(row_totals[1]):,}".replace(",", " "),
    ]

    annotations = []
    customdata = []
    for row_index in range(2):
        annotation_row = []
        custom_row = []
        for column_index, column in enumerate([False, True]):
            count = int(counts.iloc[row_index, column_index])
            rate = float(row_rates.iloc[row_index, column_index])
            annotation_row.append(f"{count:,}".replace(",", " ") + f"<br>{rate:.1f}%")
            custom_row.append([count, int(row_totals[row_index])])
        annotations.append(annotation_row)
        customdata.append(custom_row)

    figure = go.Figure(
        go.Heatmap(
            z=row_rates.to_numpy(),
            x=x_labels,
            y=y_labels,
            text=annotations,
            texttemplate="%{text}",
            customdata=customdata,
            colorscale=[
                [0.0, "#f1f5f5"],
                [0.45, "#b8d1d1"],
                [1.0, "#176b70"],
            ],
            zmin=0,
            zmax=100,
            colorbar={
                "title": {"text": "Part<br>de la ligne"},
                "ticksuffix": "%",
                "thickness": 12,
                "len": 0.84,
            },
            hovertemplate=(
                "%{y}<br>%{x}<br>"
                "%{z:.1f}% de la ligne<br>"
                "n = %{customdata[0]:,} / %{customdata[1]:,}"
                "<extra></extra>"
            ),
            xgap=3,
            ygap=3,
        )
    )
    figure.update_xaxes(side="top", tickfont={"size": 12})
    figure.update_yaxes(autorange="reversed", tickfont={"size": 12})
    return _base_figure(
        figure,
        height=285,
        margin={"l": 150, "r": 44, "t": 82, "b": 30},
    )


def build_age_figure(summary) -> go.Figure:
    if summary is None or summary.empty:
        return _empty_figure("Les groupes d’âge ne peuvent pas être calculés.")

    figure = go.Figure()
    for chip in CHIP_ORDER:
        rows = summary[summary["Chip_Type"] == chip]
        if rows.empty:
            continue
        customdata = np.column_stack(
            [
                rows["n"].to_numpy(),
                rows["median_pct"].to_numpy(),
                rows["low_pct"].to_numpy(),
                rows["high_pct"].to_numpy(),
            ]
        )
        figure.add_trace(
            go.Scatter(
                x=rows["Age_Group"],
                y=rows["mean_pct"],
                mode="lines+markers",
                name=CHIP_LABELS[chip],
                line={"color": CHIP_COLORS[chip], "width": 2.5},
                marker={
                    "color": CHIP_COLORS[chip],
                    "size": 9,
                    "line": {"color": "#ffffff", "width": 1.5},
                },
                error_y={
                    "type": "data",
                    "symmetric": False,
                    "array": (rows["high_pct"] - rows["mean_pct"]).clip(lower=0),
                    "arrayminus": (rows["mean_pct"] - rows["low_pct"]).clip(lower=0),
                    "color": CHIP_COLORS[chip],
                    "thickness": 1.4,
                    "width": 4,
                },
                customdata=customdata,
                hovertemplate=(
                    "<b>%{x} ans</b><br>"
                    f"{CHIP_LABELS[chip]}<br>"
                    "Moyenne : %{y:.1f}% des composants mesurés<br>"
                    "Médiane : %{customdata[1]:.1f}%<br>"
                    "IC bootstrap 95% : %{customdata[2]:.1f}–"
                    "%{customdata[3]:.1f}%<br>"
                    "Patients : n = %{customdata[0]:,}"
                    "<extra></extra>"
                ),
            )
        )

    figure.update_layout(
        legend={
            "orientation": "h",
            "yanchor": "bottom",
            "y": 1.02,
            "xanchor": "left",
            "x": 0,
            "title": None,
        },
        yaxis_title="Composants au seuil / composants mesurés (%)",
        xaxis_title="Âge au prélèvement",
        yaxis={"rangemode": "tozero", "ticksuffix": "%"},
        hovermode="x",
    )
    return _base_figure(
        figure,
        height=390,
        margin={"l": 72, "r": 24, "t": 66, "b": 62},
    )


def build_skin_figure(summary) -> go.Figure:
    if summary is None or summary.empty:
        return _empty_figure(
            "Les données renseignées ne couvrent pas tous les groupes d’âge."
        )

    summary = summary.set_index("Chip_Type").reindex(CHIP_ORDER).dropna(
        subset=["effect_pp"]
    ).reset_index()
    if summary.empty:
        return _empty_figure("Aucun contraste calculable pour ces puces.")

    colors = [CHIP_COLORS[chip] for chip in summary["Chip_Type"]]
    symbols = [
        "circle-open"
        if row["low_pp"] <= 0 <= row["high_pp"]
        else "circle"
        for _, row in summary.iterrows()
    ]
    customdata = np.column_stack(
        [
            summary["low_pp"].to_numpy(),
            summary["high_pp"].to_numpy(),
            summary["known_n"].to_numpy(),
            summary["no_n"].to_numpy(),
            summary["yes_n"].to_numpy(),
            summary["standardized_no_pct"].to_numpy(),
            summary["standardized_yes_pct"].to_numpy(),
        ]
    )
    figure = go.Figure(
        go.Scatter(
            x=summary["effect_pp"],
            y=[CHIP_LABELS[chip] for chip in summary["Chip_Type"]],
            mode="markers",
            marker={
                "size": 13,
                "color": colors,
                "symbol": symbols,
                "line": {"color": "#ffffff", "width": 1.4},
            },
            error_x={
                "type": "data",
                "symmetric": False,
                "array": (summary["high_pp"] - summary["effect_pp"]).clip(lower=0),
                "arrayminus": (summary["effect_pp"] - summary["low_pp"]).clip(lower=0),
                "color": "#506164",
                "thickness": 1.7,
                "width": 7,
            },
            customdata=customdata,
            hovertemplate=(
                "<b>%{y}</b><br>"
                "Écart symptômes oui − non : %{x:+.1f} points<br>"
                "IC bootstrap 95% : %{customdata[0]:+.1f} à "
                "%{customdata[1]:+.1f}<br>"
                "Effectif avec âge et peau renseignés : n = %{customdata[2]:,}<br>"
                "Sans symptômes : n = %{customdata[3]:,}<br>"
                "Avec symptômes : n = %{customdata[4]:,}<br>"
                "Part standardisée, sans : %{customdata[5]:.1f}%<br>"
                "Part standardisée, avec : %{customdata[6]:.1f}%"
                "<extra></extra>"
            ),
        )
    )
    figure.add_vline(
        x=0,
        line_color="#647477",
        line_dash="dash",
        line_width=1.3,
    )
    figure.update_layout(
        xaxis_title="Écart de diversité mesurée (symptômes oui − non, points)",
        yaxis_title="",
        showlegend=False,
        xaxis={"zeroline": False},
    )
    return _base_figure(
        figure,
        height=280,
        margin={"l": 86, "r": 28, "t": 22, "b": 66},
    )


def build_component_heatmap(
    bundle: AccBundle,
    age_groups: list[str],
) -> go.Figure:
    components, rates, counts = top_component_matrix(
        bundle,
        age_groups=age_groups,
        cutoff=COMPONENT_CUTOFF,
        limit=16,
        min_measured=20,
    )
    if not components:
        return _empty_figure(
            "Aucun composant n’a assez de mesures dans cette sélection.",
            height=300,
        )

    text = []
    customdata = []
    for row_rates, row_counts in zip(rates, counts):
        text_row = []
        custom_row = []
        for rate, count in zip(row_rates, row_counts):
            if rate is None or count is None:
                text_row.append("")
                custom_row.append([None, None])
            else:
                positive_n, measured_n = count
                text_row.append(f"{rate:.0f}%")
                custom_row.append([positive_n, measured_n])
        text.append(text_row)
        customdata.append(custom_row)

    figure = go.Figure(
        go.Heatmap(
            z=rates,
            x=[CHIP_LABELS[chip] for chip in CHIP_ORDER],
            y=components,
            text=text,
            texttemplate="%{text}",
            customdata=customdata,
            colorscale=[
                [0.0, "#f2f6f5"],
                [0.35, "#b7d7d2"],
                [0.7, "#5aa59a"],
                [1.0, "#145c60"],
            ],
            zmin=0,
            zmax=100,
            colorbar={
                "title": {"text": "Mesures<br>≥ 0,30"},
                "ticksuffix": "%",
                "thickness": 12,
                "len": 0.84,
            },
            hoverongaps=False,
            hovertemplate=(
                "<b>%{y}</b><br>%{x}<br>"
                "%{z:.1f}% des mesures disponibles<br>"
                "Mesures au seuil : %{customdata[0]:,} / "
                "%{customdata[1]:,}"
                "<extra></extra>"
            ),
            xgap=3,
            ygap=2,
        )
    )
    figure.update_layout(
        xaxis={"side": "top"},
        yaxis={"autorange": "reversed"},
    )
    figure.update_xaxes(showgrid=False)
    figure.update_yaxes(showgrid=False, tickfont={"size": 11})
    figure = _base_figure(
        figure,
        height=max(370, 25 * len(components) + 100),
        margin={"l": 96, "r": 58, "t": 62, "b": 28},
    )
    figure.update_layout(plot_bgcolor="#e9eeeb")
    return figure


def build_component_age_figure(
    bundle: AccBundle,
    component: str,
    chip: str,
    age_groups: list[str],
) -> tuple[go.Figure, str]:
    summary = component_age_summary(
        bundle,
        component=component,
        chip=chip,
        age_groups=age_groups,
        cutoff=COMPONENT_CUTOFF,
    )
    if summary.empty:
        return (
            _empty_figure(
                "Aucune mesure disponible pour ce composant dans cette sélection."
            ),
            "Aucune mesure disponible.",
        )

    customdata = np.column_stack(
        [
            summary["positive_n"].to_numpy(),
            summary["n"].to_numpy(),
            summary["low_pct"].to_numpy(),
            summary["high_pct"].to_numpy(),
        ]
    )
    labels = [
        f"n={int(row.n)}"
        for row in summary.itertuples(index=False)
    ]
    figure = go.Figure(
        go.Scatter(
            x=summary["Age_Group"],
            y=summary["rate_pct"],
            mode="lines+markers+text",
            text=labels,
            textposition="top center",
            line={"color": CHIP_COLORS[chip], "width": 2.4},
            marker={
                "color": CHIP_COLORS[chip],
                "size": 9,
                "line": {"color": "#ffffff", "width": 1.4},
            },
            error_y={
                "type": "data",
                "symmetric": False,
                "array": (summary["high_pct"] - summary["rate_pct"]).clip(lower=0),
                "arrayminus": (summary["rate_pct"] - summary["low_pct"]).clip(lower=0),
                "color": CHIP_COLORS[chip],
                "thickness": 1.3,
                "width": 4,
            },
            customdata=customdata,
            hovertemplate=(
                "<b>%{x} ans</b><br>"
                f"{component} · {CHIP_LABELS[chip]}<br>"
                "%{y:.1f}% des mesures au seuil<br>"
                "%{customdata[0]:,} positives / %{customdata[1]:,} mesurées<br>"
                "IC de Wilson 95% : %{customdata[2]:.1f}–"
                "%{customdata[3]:.1f}%"
                "<extra></extra>"
            ),
        )
    )
    figure.update_layout(
        xaxis_title="Âge au prélèvement",
        yaxis_title="Part des mesures ≥ 0,30 (%)",
        yaxis={"rangemode": "tozero", "ticksuffix": "%"},
        showlegend=False,
    )
    figure = _base_figure(figure, height=320)
    counts_text = " · ".join(
        f"{row.Age_Group} ans : {int(row.positive_n)}/{int(row.n)}"
        for row in summary.itertuples(index=False)
    )
    return figure, f"Composants au seuil / mesures disponibles — {counts_text}."


def _age_filter_values(raw_values) -> list[str]:
    if not isinstance(raw_values, list):
        return AGE_GROUPS.copy()
    values = [value for value in raw_values if value in AGE_GROUPS]
    return values or AGE_GROUPS.copy()


def _valid_chip(raw_chip) -> str:
    return raw_chip if raw_chip in CHIP_ORDER else "ISAC_V1"


def _component_options(bundle: AccBundle, chip: str) -> list[str]:
    mask = bundle.patients["Chip_Type"].eq(chip)
    selected_indices = bundle.patients.index[mask]
    available = [
        component
        for component in bundle.component_columns
        if bundle.values.loc[selected_indices, component].notna().any()
    ]
    return available or bundle.component_columns


def _default_component(bundle: AccBundle, chip: str) -> str:
    options = _component_options(bundle, chip)
    indices = bundle.patients.index[bundle.patients["Chip_Type"].eq(chip)]
    best_component = options[0]
    best_rate = -1.0
    for component in options:
        measured = bundle.values.loc[indices, component].dropna()
        if measured.empty:
            continue
        rate = float(measured.ge(COMPONENT_CUTOFF).mean())
        if rate > best_rate:
            best_rate = rate
            best_component = component
    return best_component


def _state_from_search(search: str | None) -> tuple[list[str], str, str]:
    params = parse_qs((search or "").lstrip("?"))
    ages = _age_filter_values(params.get("age", AGE_GROUPS))
    chip = _valid_chip(params.get("chip", ["ISAC_V1"])[0])
    component = params.get("component", [""])[0]
    if DATA is not None and component not in _component_options(DATA, chip):
        component = _default_component(DATA, chip)
    return ages, chip, component


def _encode_state(ages: list[str], chip: str, component: str) -> str:
    params: list[tuple[str, str]] = []
    if ages != AGE_GROUPS:
        params.extend(("age", age) for age in AGE_GROUPS if age in ages)
    if chip != "ISAC_V1":
        params.append(("chip", chip))
    default = _default_component(DATA, chip) if DATA is not None else ""
    if component and component != default:
        params.append(("component", component))
    encoded = urlencode(params)
    return f"?{encoded}" if encoded else ""


def _initial_state():
    try:
        search = request.query_string.decode("utf-8")
    except RuntimeError:
        search = ""
    ages, chip, component = _state_from_search(search)
    if not component and DATA is not None:
        component = _default_component(DATA, chip)
    return ages, chip, component


def _section_heading(number: str, eyebrow: str, title: str, body: str):
    return html.Div(
        [
            html.Div(number, className="section-number", **{"aria-hidden": "true"}),
            html.Div(
                [
                    html.P(eyebrow, className="eyebrow"),
                    html.H2(title),
                    html.P(body, className="section-intro"),
                ],
                className="section-heading-copy",
            ),
        ],
        className="section-heading",
    )


def _figure(graph_id: str, figure: go.Figure, label: str):
    return html.Div(
        [
            dcc.Graph(
                id=graph_id,
                figure=figure,
                config=PLOT_CONFIG,
                responsive=True,
            ),
        ],
        className="figure-frame",
        role="group",
        **{"aria-label": label},
    )


def _skin_readouts(summary):
    if summary is None or summary.empty:
        return html.P("Contraste non calculable.", className="muted")
    items = []
    for row in summary.itertuples(index=False):
        direction = "plus faible" if row.effect_pp < 0 else "plus élevée"
        interval_readout = (
            "L’intervalle recoupe 0."
            if row.low_pp <= 0 <= row.high_pp
            else "L’intervalle n’inclut pas 0."
        )
        items.append(
            html.Div(
                [
                    html.Strong(f"{row.effect_pp:+.1f} points"),
                    html.Span(
                        f"{CHIP_LABELS[row.Chip_Type]} · IC bootstrap 95% "
                        f"[{row.low_pp:+.1f} ; {row.high_pp:+.1f}] · "
                        f"n={row.known_n}"
                    ),
                    html.Span(
                        f"Estimation : part moyenne {direction} chez les "
                        f"patients avec symptômes cutanés, après "
                        f"standardisation sur l’âge. {interval_readout}"
                    ),
                ],
                className="effect-readout",
            )
        )
    return html.Div(items, className="effect-readouts")


def _error_layout():
    return html.Main(
        [
            html.P("ACC · Data visualisation", className="eyebrow"),
            html.H1("Le fichier de données n’est pas prêt"),
            html.P(
                "L’application attend le CSV ACC en local. Elle ne copie pas "
                "les données dans le dépôt."
            ),
            html.Pre(DATA_ERROR or "Erreur de lecture inconnue.", className="error-path"),
            html.P(
                [
                    "Dans PowerShell, définissez ACC_CSV_PATH avec le chemin "
                    "du fichier, puis relancez l’application. Le chemin par "
                    "défaut recherché est ",
                    html.Code("Téléchargements/allergenchipchallenge-data-corrected-final-hdh-sfa.csv"),
                    ".",
                ]
            ),
        ],
        className="error-page",
    )


def _serve_layout():
    if DATA is None:
        return _error_layout()

    initial_ages, initial_chip, initial_component = _initial_state()
    agreement_figure = build_agreement_figure(DATA)
    age_figure = build_age_figure(AGE_SUMMARY)
    skin_figure = build_skin_figure(SKIN_SUMMARY)
    agreement_count = int(AGREEMENT.loc[0, False] + AGREEMENT.loc[1, True])
    agreement_n = int(AGREEMENT.to_numpy().sum())
    age_highlights = (
        "La moyenne est plus élevée entre 6 et 17 ans que chez les 40 ans et "
        "plus pour chacune des trois puces. L’âge manque pour "
        f"{COHORT['age_missing_n']} patients. Les barres donnent des "
        "intervalles bootstrap à 95 % ; il s’agit de groupes d’âge "
        "transversaux, pas du suivi des mêmes personnes."
    )
    coverage = chip_coverage_summary(DATA)
    coverage_items = []
    for row in coverage.itertuples(index=False):
        coverage_items.append(
            html.Div(
                [
                    html.Span(CHIP_LABELS[row.Chip_Type]),
                    html.Strong(
                        f"{row.components} / {row.total_components}"
                    ),
                    html.Small(f"{row.coverage_pct:.1f}% du panel · n={row.patients:,}".replace(",", " ")),
                ],
                className="coverage-fact",
            )
        )

    return html.Div(
        [
            dcc.Location(id="explorer-url", refresh=False),
            html.Header(
                [
                    html.Div(
                        [
                            html.Span("ACC", className="brand-mark"),
                            html.Span("Allergen Chip Challenge"),
                        ],
                        className="brand",
                    ),
                    html.Span(
                        "M2 IA · DATA VISUALISATION",
                        className="course-label",
                    ),
                ],
                className="topbar page-width",
            ),
            html.Main(
                [
                    html.Section(
                        [
                            html.Div(
                                [
                                    html.P(
                                        "Une histoire de mesure, d’âge et de profils",
                                        className="eyebrow",
                                    ),
                                    html.H1(
                                        [
                                            "Un signal global.",
                                            html.Br(),
                                            "Des profils qui divergent.",
                                        ],
                                        className="hero-title",
                                    ),
                                    html.P(
                                        "La diversité des sensibilisations IgE varie-t-elle avec "
                                        "l’âge et les symptômes cutanés — et cette relation "
                                        "se retrouve-t-elle selon la puce utilisée ?",
                                        className="hero-question",
                                    ),
                                ],
                                className="hero-copy",
                            ),
                            html.Div(
                                [
                                    html.P("LE FIL DE L’ANALYSE", className="eyebrow"),
                                    html.P(
                                        "Le statut global « sensibilisé » est presque toujours "
                                        "retrouvé dans les composants mesurés. Mais le panel "
                                        "dépend de la puce, la part de composants détectés varie "
                                        "selon l’âge, et le contraste cutané change selon la "
                                        "technologie.",
                                        className="hero-thesis",
                                    ),
                                    html.P(
                                        "Les résultats décrivent cette cohorte rétrospective ; "
                                        "ils ne montrent ni une évolution individuelle ni un "
                                        "effet causal.",
                                        className="hero-caveat",
                                    ),
                                ],
                                className="hero-thesis-block",
                            ),
                        ],
                        className="hero page-width",
                    ),
                    html.Div(
                        [
                            html.P(
                                [
                                    html.Strong("Limite de portée"),
                                    " — le CSV fourni ne contient pas le diagnostic "
                                    "« Allergy_Present » ni la cible « Severe_Allergy ». "
                                    "Ce dashboard étudie la sensibilisation et les symptômes "
                                    "cutanés observés ; il ne prédit pas la sévérité.",
                                ],
                                className="scope-note",
                            )
                        ],
                        className="page-width",
                    ),
                    html.Section(
                        [
                            html.Div(
                                [
                                    html.Div(
                                        [
                                            html.Dt("Patients"),
                                            html.Dd(f"{COHORT['n']:,}".replace(",", " ")),
                                        ],
                                        className="stat-item",
                                    ),
                                    html.Div(
                                        [
                                            html.Dt("Sensibilisés"),
                                            html.Dd(f"{COHORT['sensitized_pct']:.1f}%"),
                                        ],
                                        className="stat-item",
                                    ),
                                    html.Div(
                                        [
                                            html.Dt("Âge médian"),
                                            html.Dd(f"{COHORT['median_age']:.0f} ans"),
                                        ],
                                        className="stat-item",
                                    ),
                                    html.Div(
                                        [
                                            html.Dt("Composants IgE"),
                                            html.Dd(str(COHORT["component_count"])),
                                        ],
                                        className="stat-item",
                                    ),
                                ],
                                className="stat-strip",
                            ),
                            html.P(
                                "Les mesures au seuil ≥ 0,30 utilisent l’unité propre à "
                                "chaque plateforme (ISAC ou ALEX). Elles représentent un "
                                "signal de sensibilisation moléculaire, jamais un grade de "
                                "sévérité.",
                                className="threshold-note",
                            ),
                        ],
                        className="page-width stats-section",
                    ),
                    html.Section(
                        [
                            _section_heading(
                                "01",
                                "Du statut global au signal moléculaire",
                                f"Le statut global et les mesures IgE concordent dans "
                                f"{AGREEMENT_RATE * 100:.1f}% des statuts renseignés",
                                "La matrice compare le champ binaire « Sensitization » au fait "
                                "d’avoir au moins un composant mesuré au seuil exploratoire "
                                "de 0,30. Les nombres et les parts par ligne restent visibles.",
                            ),
                            html.Div(
                                [
                                    html.Div(
                                        [
                                            html.Strong(f"{agreement_count:,}".replace(",", " ")),
                                            html.Span(
                                                f" lignes concordantes sur {agreement_n:,}".replace(",", " ")
                                            ),
                                        ],
                                        className="chart-callout",
                                    ),
                                    _figure(
                                        "agreement-chart",
                                        agreement_figure,
                                        "Matrice de concordance du statut Sensitization "
                                        "et de la présence d’au moins un composant mesuré "
                                        "à 0,30 ou plus. Chaque case montre le nombre et "
                                        "le pourcentage dans la ligne.",
                                    ),
                                ],
                                className="chapter-visual",
                            ),
                            html.P(
                                "Cette concordance est un contrôle interne de cohérence, "
                                "pas une validation clinique indépendante : les deux signaux "
                                "proviennent du même jeu de données.",
                                className="method-note",
                            ),
                        ],
                        className="story-section page-width",
                    ),
                    html.Section(
                        [
                            _section_heading(
                                "02",
                                "La fenêtre de mesure",
                                "La puce change le nombre de composants observables",
                                "Les cases vides correspondent souvent à des composants "
                                "absents du panel de la puce. Elles ne valent pas zéro et ne "
                                "sont pas comptées comme des résultats négatifs.",
                            ),
                            html.Div(coverage_items, className="coverage-strip"),
                            html.P(
                                f"La matrice IgE est vide sur {COHORT['component_missing_pct']:.1f}% "
                                "de ses cellules, principalement à cause de cette couverture "
                                "différente. " + (
                                    f"{DATA.negative_sentinel_count} valeurs négatives codées "
                                    "−1 ont été traitées comme non mesurées."
                                    if DATA.negative_sentinel_count
                                    else "Les zéros mesurés restent distincts des valeurs absentes."
                                ),
                                className="method-note",
                            ),
                        ],
                        className="story-section page-width",
                    ),
                    html.Section(
                        [
                            _section_heading(
                                "03",
                                "Une comparaison à panel normalisé",
                                "La part détectée est plus faible après 40 ans dans les trois puces",
                                age_highlights,
                            ),
                            _figure(
                                "age-chart",
                                age_figure,
                                "Courbes par puce du pourcentage moyen de composants mesurés "
                                "au seuil de 0,30 par classe d’âge. Les barres montrent des "
                                "intervalles bootstrap à 95 pour cent.",
                            ),
                            html.P(
                                "La mesure est le nombre de composants avec une valeur "
                                "supérieure ou égale à 0,30 divisé par le nombre de composants "
                                "effectivement mesurés pour cette personne. Le seuil est "
                                "appliqué dans l’unité propre à chaque puce.",
                                className="method-note",
                            ),
                        ],
                        className="story-section page-width",
                    ),
                    html.Section(
                        [
                            _section_heading(
                                "04",
                                "Le signal clinique",
                                "Le contraste cutané dépend de la plateforme",
                                "On compare la part de composants au seuil entre les dossiers "
                                "avec et sans symptômes cutanés, séparément par puce et "
                                "standardisé sur la distribution d’âge observée dans chaque puce.",
                            ),
                            _figure(
                                "skin-chart",
                                skin_figure,
                                "Écart en points de pourcentage de la part de composants "
                                "mesurés au seuil entre les patients avec et sans symptômes "
                                "cutanés, standardisé selon l’âge et séparé par puce. "
                                "Les intervalles à 95 pour cent proviennent d’un bootstrap.",
                            ),
                            _skin_readouts(SKIN_SUMMARY),
                            html.P(
                                f"Les symptômes cutanés sont renseignés pour "
                                f"{COHORT['skin_known_n']:,} patients seulement ; "
                                f"{COHORT['skin_unknown_pct']:.1f}% des lignes ont un statut "
                                "inconnu. La standardisation porte uniquement sur l’âge ; "
                                "elle ne corrige pas les autres différences de recrutement "
                                "ou de mesure.",
                                className="method-note",
                            ),
                        ],
                        className="story-section page-width",
                    ),
                    html.Section(
                        [
                            _section_heading(
                                "05",
                                "À vous d’explorer",
                                "Les profils moléculaires ne se réduisent pas à un score",
                                "La carte montre les composants les plus souvent au seuil "
                                "dans les groupes d’âge sélectionnés. Chaque colonne garde "
                                "son propre dénominateur ; les cellules avec moins de 20 "
                                "mesures sont masquées.",
                            ),
                            html.P(
                                "Les cases grisées indiquent l’absence de mesures ou "
                                "moins de 20 mesures disponibles pour ce couple "
                                "composant-puce. Les pourcentages inscrits restent lisibles "
                                "sans survol.",
                                className="method-note",
                            ),
                            _figure(
                                "molecular-heatmap",
                                _empty_figure("Chargement de la sélection…", height=520),
                                "Carte thermique des composants observés : pour chaque "
                                "composant et chaque puce, la couleur et l’étiquette "
                                "indiquent la part des mesures disponibles au seuil ; "
                                "les cases grisées ont moins de 20 mesures.",
                            ),
                            html.Div(
                                [
                                    html.Div(
                                        [
                                            html.Label(
                                                "Classe(s) d’âge",
                                                htmlFor="age-filter",
                                            ),
                                            dcc.Dropdown(
                                                id="age-filter",
                                                options=[
                                                    {"label": age, "value": age}
                                                    for age in AGE_GROUPS
                                                ],
                                                value=initial_ages,
                                                multi=True,
                                                clearable=False,
                                                searchable=False,
                                                className="filter-control",
                                            ),
                                        ],
                                        className="filter-field age-filter-field",
                                    ),
                                    html.Div(
                                        [
                                            html.Label(
                                                "Puce pour le détail",
                                                htmlFor="chip-filter",
                                            ),
                                            dcc.Dropdown(
                                                id="chip-filter",
                                                options=[
                                                    {
                                                        "label": CHIP_LABELS[chip],
                                                        "value": chip,
                                                    }
                                                    for chip in CHIP_ORDER
                                                ],
                                                value=initial_chip,
                                                clearable=False,
                                                searchable=False,
                                                className="filter-control",
                                            ),
                                        ],
                                        className="filter-field",
                                    ),
                                    html.Div(
                                        [
                                            html.Label(
                                                "Composant à détailler",
                                                htmlFor="component-filter",
                                            ),
                                            dcc.Dropdown(
                                                id="component-filter",
                                                options=[
                                                    {
                                                        "label": component,
                                                        "value": component,
                                                    }
                                                    for component in _component_options(
                                                        DATA, initial_chip
                                                    )
                                                ],
                                                value=initial_component,
                                                clearable=False,
                                                searchable=True,
                                                className="filter-control",
                                            ),
                                        ],
                                        className="filter-field component-filter-field",
                                    ),
                                    html.A(
                                        "Réinitialiser",
                                        href="/",
                                        className="reset-link",
                                    ),
                                ],
                                className="explorer-controls",
                            ),
                            html.P(
                                id="explorer-summary",
                                className="explorer-summary",
                            ),
                            _figure(
                                "component-age-chart",
                                _empty_figure("Choisissez un composant.", height=320),
                                "Part des mesures au seuil pour le composant choisi, "
                                "par âge, sur la puce sélectionnée. Les effectifs mesurés "
                                "sont affichés sous le graphique.",
                            ),
                            html.P(
                                "Explorer les composants décrit les mesures disponibles "
                                "dans cette cohorte. Les noms restent les codes du fichier ; "
                                "aucune famille allergénique n’a été inventée à partir des "
                                "préfixes.",
                                className="method-note",
                            ),
                        ],
                        className="story-section page-width explorer-section",
                    ),
                    html.Footer(
                        [
                            html.P("Sources et méthode", className="eyebrow"),
                            html.P(
                                [
                                    "Données : ",
                                    html.A(
                                        "Allergen Chip Challenge, data.gouv.fr",
                                        href="https://www.data.gouv.fr/datasets/allergen-chip-challenge/",
                                        target="_blank",
                                        rel="noreferrer",
                                    ),
                                    ". Seuil qualitatif exploratoire de 0,30 dans "
                                    "l’unité propre à chaque plateforme ; la littérature "
                                    "emploie ce seuil pour comparer des résultats ISAC et ALEX : ",
                                    html.A(
                                        "étude comparative",
                                        href="https://www.mdpi.com/2075-4418/14/10/976",
                                        target="_blank",
                                        rel="noreferrer",
                                    ),
                                    ". Le seuil n’est pas un grade de sévérité.",
                                ]
                            ),
                            html.P(
                                "Les données restent locales. Les graphiques agrègent les "
                                "observations et n’exposent pas les identifiants patients.",
                                className="footer-small",
                            ),
                        ],
                        className="page-width footer",
                    ),
                ],
                className="page-content",
            ),
        ],
        className="app-shell",
    )


app = Dash(
    __name__,
    title="ACC · Profils de sensibilisation",
    meta_tags=[
        {
            "name": "viewport",
            "content": "width=device-width, initial-scale=1",
        },
        {
            "name": "description",
            "content": "Dashboard narratif des profils de sensibilisation IgE dans la cohorte ACC.",
        },
    ],
    suppress_callback_exceptions=True,
)
app.layout = _serve_layout


if DATA is not None:
    @app.callback(
        Output("age-filter", "value"),
        Output("chip-filter", "value"),
        Output("component-filter", "value"),
        Output("component-filter", "options"),
        Output("explorer-url", "search"),
        Output("molecular-heatmap", "figure"),
        Output("component-age-chart", "figure"),
        Output("explorer-summary", "children"),
        Input("explorer-url", "search"),
        Input("age-filter", "value"),
        Input("chip-filter", "value"),
        Input("component-filter", "value"),
    )
    def update_explorer(search, age_values, chip, component):
        triggered = ctx.triggered_id
        requested_component = component
        if triggered == "explorer-url":
            age_values, chip, component = _state_from_search(search)
            update_controls = True
        else:
            age_values = _age_filter_values(age_values)
            chip = _valid_chip(chip)
            update_controls = False

        age_values = _age_filter_values(age_values)
        chip = _valid_chip(chip)
        options = _component_options(DATA, chip)
        if component not in options:
            component = _default_component(DATA, chip)

        if triggered == "explorer-url":
            encoded_state = _encode_state(age_values, chip, component)
            search_value = (
                no_update
                if (search or "") == encoded_state
                else encoded_state
            )
        else:
            search_value = _encode_state(age_values, chip, component)

        heatmap = build_component_heatmap(DATA, age_values)
        detail, counts_text = build_component_age_figure(
            DATA,
            component=component,
            chip=chip,
            age_groups=age_values,
        )
        selected_rows = DATA.patients[
            DATA.patients["Age_Group"].isin(age_values)
        ]
        selected_component = DATA.values.loc[
            selected_rows.index, component
        ].dropna()
        summary = html.Span(
            [
                f"{len(selected_rows):,} patients dans les classes d’âge sélectionnées · "
                f"{CHIP_LABELS[chip]} · {component} · "
                f"{int(selected_component.ge(COMPONENT_CUTOFF).sum()):,} mesures au seuil "
                f"sur {len(selected_component):,} mesurées. ".replace(",", " "),
                counts_text,
            ]
        )

        return (
            age_values if update_controls else no_update,
            chip if update_controls else no_update,
            (
                component
                if update_controls or component != requested_component
                else no_update
            ),
            [{"label": value, "value": value} for value in options],
            search_value,
            heatmap,
            detail,
            summary,
        )


if __name__ == "__main__":
    app.run(debug=False, host="127.0.0.1", port=8050)
