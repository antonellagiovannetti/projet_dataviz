from dash import html

SECTIONS = [
    ("overview", "Vue d’ensemble"), ("landscape", "Les mesures"),
    ("sensitization", "Sensibilisation"), ("clinical", "Signaux cliniques"),
    ("profiles", "Les profils"), ("explorer", "Mes cohortes"),
    ("conclusions", "Conclusions"),
]
NAVIGATION = [("glossary", "Repères")] + SECTIONS


def navbar():
    return html.Header([
        html.A([html.Img(src="/assets/logo.svg", alt="", className="brand-icon"),
                html.Div([html.Strong(["allergy", html.Span("atlas")]),
                          html.Small("EXPLORER LES SIGNATURES IgE")])], href="#overview", className="brand"),
        html.Nav([html.A([html.Small("ABC" if key == "glossary" else f"{i:02d}"), html.Span(label)], href=f"#{key}",
                         id=f"nav-{key}", className="nav-link")
                  for i, (key, label) in enumerate(NAVIGATION)] +
                 [html.Span(id="nav-indicator", **{"aria-hidden": "true"})],
                 **{"aria-label": "Repères et étapes de l’exploration"}),
        html.Span([html.I(className="status-dot"), "ACC · Open data"], className="source-badge"),
    ], className="topbar")
