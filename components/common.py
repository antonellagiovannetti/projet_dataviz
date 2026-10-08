"""Small, shared presentation components."""
from dash import dcc, html
import pandas as pd

RESEARCH_QUESTION = (
    "Comment les profils de sensibilisation IgE se structurent-ils dans ACC, "
    "et quels liens présentent-ils avec les manifestations cliniques disponibles ?"
)
CHAPTER_PURPOSE = {
    "02": "Avant de chercher des profils, établir ce qui est réellement comparable.",
    "03": "Repérer les signaux partagés et la diversité des sensibilisations.",
    "04": "Observer les différences de signatures selon la clinique renseignée.",
    "05": "Former des profils à partir des IgE, puis décrire leur composition clinique.",
    "06": "Mettre vos hypothèses à l’épreuve en comparant deux populations.",
    "07": "Répondre à la question de départ en distinguant constats et limites.",
}


def number(value, decimals=0):
    if value is None or pd.isna(value):
        return "—"
    return f"{value:,.{decimals}f}".replace(",", "\u202f").replace(".", ",")


def metric(label, value, detail="", accent=False):
    return html.Div([html.Span(label, className="metric-label"),
                     html.Strong(value, className="metric-value"),
                     html.Small(detail, className="metric-detail")],
                    className="metric accent" if accent else "metric")


def note(title, body, tone="info"):
    return html.Div([html.Span("i" if tone == "info" else "!", className="note-icon"),
                     html.Div([html.Strong(title), html.P(body)])], className=f"note {tone}")


def takeaway(text, label="À RETENIR"):
    return html.Div([html.Span(label, className="takeaway-label"), html.P(text)], className="chart-takeaway")


def graph_panel(title, subtitle, figure, graph_id, badge=None, class_name="", footnote=None, insight=None):
    title = title.replace(" ?", "\u00a0?")
    return html.Section([
        html.Div([html.Div([html.H3(title), html.P(subtitle)]),
                  html.Span(badge, className="panel-badge") if badge else None], className="panel-heading"),
        html.Div(dcc.Graph(id=graph_id, figure=figure, responsive=True, style={"height": f"{figure.layout.height or 330}px"},
                  config={"displaylogo": False, "scrollZoom": False,
                          "modeBarButtonsToRemove": ["autoScale2d"],
                          "toImageButtonOptions": {"format": "svg", "filename": graph_id}},
                  className="plot"), className="plot-scroll"),
        takeaway(insight) if insight else None,
        html.P(footnote, className="chart-footnote") if footnote else None,
    ], className=f"chart-panel {class_name}")


def page_heading(step, title, description):
    if step == "01":
        thread = html.Section([
            html.Span("LA PROBLÉMATIQUE", className="eyebrow"),
            html.H2(RESEARCH_QUESTION),
            html.P("Comprendre les mesures → faire émerger des profils → explorer leurs liens avec la clinique.", className="research-path"),
        ], className="research-question", **{"aria-label": "Problématique du projet"})
    else:
        thread = html.Div([
            html.A([html.Span("FIL CONDUCTEUR"), html.Strong("Profils IgE → manifestations cliniques")], href="#overview"),
            html.P(CHAPTER_PURPOSE[step]),
        ], className="story-thread")
    return html.Div([html.Div([html.Span(f"ÉTAPE {step} / 07"),
                              html.Span("ALLERGEN CHIP CHALLENGE", className="eyebrow-source")], className="eyebrow"),
                     html.H1(title), html.P(description, className="page-description"),
                     html.A("Repères & vocabulaire ↗", href="#glossary", className="vocabulary-link"),
                     thread], className="page-heading")


def next_step(href, title):
    return html.A([html.Span("POURSUIVRE L’EXPLORATION"), html.Strong(title), html.Span("↗")],
                  href=href, className="next-step")
