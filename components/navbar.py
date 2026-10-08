from dash import html

SECTIONS = [
    ("overview", "Complexité"), ("landscape", "Comparabilité"),
    ("sensitization", "Profils IgE"), ("clinical", "Clinique"),
    ("profiles", "Groupes"), ("conclusions", "Conclusion"),
]
NAVIGATION = [("glossary", "Repères")] + SECTIONS + [("explorer", "Laboratoire")]


def navbar():
    chapter_numbers = {key: f"{i:02d}" for i, (key, _) in enumerate(SECTIONS, start=1)}
    return html.Header([
        html.A([html.Img(src="/assets/logo.svg", alt="", className="brand-icon"),
                html.Div([html.Strong(["allergy", html.Span("atlas")]),
                          html.Small("EXPLORER LES SIGNATURES IgE")])], href="#overview", className="brand"),
        html.Nav([html.A([html.Small(chapter_numbers.get(key, "ABC" if key == "glossary" else "A/B")), html.Span(label)], href=f"#{key}",
                         id=f"nav-{key}", className="nav-link")
                  for key, label in NAVIGATION] +
                 [html.Span(id="nav-indicator", **{"aria-hidden": "true"})],
                 **{"aria-label": "Repères et étapes de l’exploration"}),
        html.Span([html.I(className="status-dot"), "ACC · Open data"], className="source-badge"),
    ], className="topbar")
