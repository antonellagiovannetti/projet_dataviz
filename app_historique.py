"""Allergy Atlas — run with python app.py, then http://127.0.0.1:8050."""
from pathlib import Path
import os
from dash import Dash, dcc, html
from components.navbar import navbar
from components.filters import filter_panel, reading_mode, toolbars
from src.data_loader import load_data
from src.clustering import get_profiles
from src.callbacks import register_callbacks

ROOT = Path(__file__).resolve().parent
dataset = load_data()
model = get_profiles()
app = Dash(__name__, title="Allergy Atlas · Recherche clinique en allergologie",
           assets_folder=str(ROOT / "assets"), suppress_callback_exceptions=True,
           update_title="Mise à jour de la cohorte…", use_pages=False)
server = app.server
app.index_string = '''<!DOCTYPE html>
<html lang="fr"><head>{%metas%}<meta name="theme-color" content="#182c47">
<meta name="description" content="Explorer une cohorte allergologique pour la recherche clinique : signatures IgE, comparaisons descriptives, profils exploratoires et limites scientifiques.">
<title>{%title%}</title>{%favicon%}{%css%}</head>
<body>{%app_entry%}<footer>{%config%}{%scripts%}{%renderer%}</footer></body></html>'''
app.layout = html.Div([
    dcc.Location(id="url", refresh=False),
    dcc.Store(id="filter-store", storage_type="session"),
    dcc.Store(id="cross-store", data={}, storage_type="session"),
    dcc.Store(id="cohort-store", data={}, storage_type="local"),
    dcc.Download(id="download-cohort"),
    html.A("Aller aux graphiques", href="#main-content", className="skip-link"),
    navbar(), html.Div(html.Div(id="page-progress"), className="progress-track"),
    filter_panel(dataset, int(dataset.frame.age.max())),
    html.Main([
        reading_mode(),
        html.Div([html.Span("EXPLORATION DE COHORTE · RECHERCHE CLINIQUE", className="workspace-label"),
                  html.Div(id="active-filters", className="active-filters", role="status", **{"aria-live": "polite"})], className="workspace-status"),
        toolbars(model.best_k),
        dcc.Loading(html.Div(id="page-body", className="page-body"), type="circle", color="#168b87", delay_show=350),
        html.Footer([html.Span("ALLERGY ATLAS"), html.Span("Données ACC · Analyse descriptive & exploratoire"),
                     html.A("Limites & sources ↗", href="#conclusions")], className="main-footer"),
    ], id="main-content", className="workspace"),
], id="app-shell", className="app-shell mode-story")
register_callbacks(app, dataset, model)

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=int(os.environ.get("PORT", "8050")), debug=False)
