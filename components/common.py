"""Small, shared presentation components."""
from dash import dcc, html
import pandas as pd

RESEARCH_QUESTION = (
    "Comment les profils de sensibilisation IgE se structurent-ils dans ACC, "
    "et quels liens présentent-ils avec les manifestations cliniques disponibles ?"
)
STORY_STEPS = [
    ("overview", "Complexité"), ("landscape", "Comparabilité"),
    ("sensitization", "Profils IgE"), ("clinical", "Clinique"),
    ("profiles", "Groupes"), ("conclusions", "Conclusion"),
]


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


def observation(text):
    return takeaway(text, "CE QU’ON OBSERVE")


def caution(text):
    return html.Details([html.Summary("Prudence · limites de lecture"), html.P(text)],
                        className="chart-caution")


def graph_panel(title, subtitle, figure, graph_id, badge=None, class_name="", footnote=None,
                insight=None, lecture=None, caution=None):
    title = title.replace(" ?", "\u00a0?")
    return html.Section([
        html.Div([html.Div([html.Span("QUESTION", className="chart-question-label"), html.H3(title), html.P(subtitle)]),
                  html.Span(badge, className="panel-badge") if badge else None], className="panel-heading"),
        html.P([html.Strong("Lecture · "), lecture], className="chart-reading") if lecture else None,
        html.Div(dcc.Graph(id=graph_id, figure=figure, responsive=True, style={"height": f"{figure.layout.height or 330}px"},
                  config={"displaylogo": False, "scrollZoom": False,
                          "modeBarButtonsToRemove": ["autoScale2d"],
                          "toImageButtonOptions": {"format": "svg", "filename": graph_id}},
                  className="plot"), className="plot-scroll"),
        takeaway(insight) if insight else None,
        html.Details([html.Summary("Prudence · limites de lecture"), html.P(caution)],
                     className="chart-caution") if caution else None,
        html.P(footnote, className="chart-footnote") if footnote else None,
    ], className=f"chart-panel {class_name}")


def story_progress(step):
    current = int(step) if str(step).isdigit() else 0
    return html.Nav([
        html.Span("Notre progression", className="story-progress-label"),
        html.Ol([html.Li(html.A([
            html.Span("✓" if i < current else f"{i:02d}", className="story-step-number", **{"aria-hidden": "true"}),
            html.Span(label)], href=f"#{route}",
            **({"aria-current": "step"} if i == current else {})),
            className="current" if i == current else "completed" if i < current else "")
            for i, (route, label) in enumerate(STORY_STEPS, 1)]),
    ], className="story-progress", **{"aria-label": "Notre progression"})


def page_heading(step, title, description):
    return html.Div([
        story_progress(step),
        html.Div([html.Span(f"CHAPITRE {step} / 06" if str(step).isdigit() else "LABORATOIRE D’EXPLORATION"),
                  html.A("Repères & vocabulaire ↗", href="#glossary", className="vocabulary-link")], className="chapter-eyebrow"),
        html.H1(title), html.P(description, className="page-description"),
    ], className="page-heading")


def story_question(question, body=None, label="LA QUESTION"):
    return html.Section([html.Span(label, className="eyebrow"), html.H2(question),
                         html.P(body) if body else None], className="story-question")


def method_decision(number, title, body, steps=None):
    return html.Section([
        html.Span(f"DÉCISION MÉTHODOLOGIQUE N°{number}", className="eyebrow"),
        html.H2(title), html.P(body),
        html.Ol([html.Li([html.Strong(value), html.Span(label)]) for value, label in steps],
                className="method-pipeline") if steps else None,
    ], className="method-decision")


def interpretation(text, label="CE QUE CELA IMPLIQUE"):
    return html.Div([html.Span(label, className="eyebrow"), html.P(text)], className="interpretation")


def transition_question(question, href, title, body=None):
    title = title.removesuffix(" →")
    return html.Section([
        html.Span("LA QUESTION SUIVANTE", className="eyebrow"), html.H2(question),
        html.P(body) if body else None,
        html.A([title, html.Span("→", **{"aria-hidden": "true"})], href=href, className="transition-link"),
    ], className="chapter-transition")


def exploration_section(title, children):
    return html.Details([html.Summary([html.Span("POUR APPROFONDIR"), title]),
                         html.Div(children, className="exploration-content")], className="exploration-section")


def next_step(href, title):
    return html.A([html.Span("POURSUIVRE L’EXPLORATION"), html.Strong(title), html.Span("↗")],
                  href=href, className="next-step")
