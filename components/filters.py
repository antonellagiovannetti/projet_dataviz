from dash import dcc, html

FILTER_KEYS = ["age", "sex", "chip", "sensitization", "region", "skin", "asthma", "rhinitis", "cluster", "allergen"]


def dropdown(key, label, options, multi=True):
    return html.Div([html.Label(label, htmlFor=f"filter-{key}"),
                     dcc.Dropdown(id=f"filter-{key}", options=options, value=[] if multi else None,
                                  multi=multi, placeholder="Tous" if multi else "Aucun filtre",
                                  clearable=True, persistence=True, persistence_type="session")], className="filter-field")


def filter_panel(dataset, max_age):
    frame = dataset.frame
    opts = lambda c: sorted(frame[c].dropna().unique().tolist())
    clinical_options = [{"label": "Oui", "value": "Oui"}, {"label": "Non", "value": "Non"},
                        {"label": "Non renseigné", "value": "Inconnu"}]
    return html.Aside([
        html.Details([
            html.Summary([html.Span("Votre population"), html.Span(id="mobile-count", className="mobile-count"), html.Span("⌄", className="filter-chevron")]),
            html.Div([
                html.Div([html.Span("COHORTE ACTIVE", className="eyebrow"),
                          html.Strong(id="cohort-size"), html.P(id="cohort-share")], className="cohort-count"),
                html.Div([html.Div([html.Label("Âge", htmlFor="filter-age"), html.Span(id="age-label")], className="filter-label-row"),
                          dcc.RangeSlider(0, max_age, step=1, value=[0, max_age], id="filter-age",
                                          marks={0: "0", 18: "18", 50: "50", max_age: str(max_age)},
                                          tooltip={"placement": "bottom", "always_visible": False},
                                          persistence=True, persistence_type="session"),
                          dcc.Checklist([{"label": "Inclure les âges inconnus", "value": "yes"}], ["yes"],
                                        id="unknown-age", className="mini-check", persistence=True, persistence_type="session")], className="filter-field age-field"),
                dropdown("sex", "Sexe", opts("sex")),
                dropdown("chip", "Technologie", opts("chip")),
                dropdown("sensitization", "Sensibilisation (variable source)", clinical_options),
                html.Details([html.Summary("Critères complémentaires"),
                    dropdown("region", "Région pseudonymisée", opts("region")),
                    dropdown("skin", "Symptômes cutanés", clinical_options),
                    dropdown("asthma", "Traitement de l’asthme", clinical_options),
                    dropdown("rhinitis", "Traitement de la rhinite", clinical_options),
                    dropdown("cluster", "Profil exploratoire", []),
                    dropdown("allergen", "IgE détectée (> 0)", [{"label": a.replace("_", " "), "value": a} for a in dataset.common_allergens], False),
                ], className="extra-filters"),
                html.Button("↺  Réinitialiser les filtres", id="reset-filters", className="reset-button"),
                html.Div([html.Span("PÉRIMÈTRE COMPARABLE", className="eyebrow"),
                          html.Strong(f"{len(dataset.common_allergens)} allergènes communs"),
                          html.P("La même base de comparaison, quelle que soit la puce.")], className="scope-note"),
            ], className="filter-content")
        ], open=True, className="filter-drawer"),
        html.Div([html.Small("PROJET M2 · IA / DATA"), html.Span("Exploration, pas diagnostic.")], className="sidebar-footer")
    ], className="sidebar")


def toolbars(best_k):
    radio = lambda key, options, value: dcc.RadioItems(options, value, id=key, className="segmented", persistence=True, persistence_type="session")
    return html.Div([
        html.Div([html.Label("Lire la couverture"), radio("coverage-sort", [
            {"label": "Communs d’abord", "value": "common"},
            {"label": "ALEX", "value": "alex"}, {"label": "ISAC", "value": "isac"}], "common"),
            dcc.Checklist([{"label": "Afficher les données non renseignées", "value": "yes"}], ["yes"], id="show-missing")], id="tools-landscape", className="page-tools", style={"display":"none"}),
        html.Div([
            html.Div([html.Label("Indicateur"), radio("allergen-metric", [
                {"label": "Fréquence", "value": "prevalence"}, {"label": "IgE moyenne", "value": "mean"},
                {"label": "IgE médiane", "value": "median"}], "prevalence")]),
            html.Div([html.Label("Allergènes affichés"), radio("top-n", [10, 20, 30], 20)]),
            html.Div([html.Label("Classes d’âge"), radio("age-mode", [
                {"label": "Détaillées", "value": "standard"}, {"label": "Larges", "value": "broad"}], "standard")]),
            html.Div([html.Label("Trier les patients"), radio("heatmap-sort", [
                {"label": "Détections", "value": "count"}, {"label": "Profil", "value": "cluster"}], "count")]),
        ], id="tools-sensitization", className="page-tools", style={"display":"none"}),
        html.Div([
            html.Div([html.Label("Information clinique", htmlFor="clinical-outcome"), dcc.Dropdown([
                {"label": "Symptômes cutanés", "value": "skin"}, {"label": "Traitement de l’asthme", "value": "asthma"},
                {"label": "Traitement de la rhinite", "value": "rhinitis"},
                {"label": "Traitement de la dermatite", "value": "dermatitis"}], "skin", id="clinical-outcome", clearable=False)]),
            html.Div([html.Label("Comparer selon", htmlFor="clinical-dimension"), dcc.Dropdown([
                {"label": "Sensibilisation", "value": "sensitization"}, {"label": "Sexe", "value": "sex"},
                {"label": "Classe d’âge", "value": "age_group"}, {"label": "Profil", "value": "cluster"}],
                "sensitization", id="clinical-dimension", clearable=False)]),
        ], id="tools-clinical", className="page-tools", style={"display":"none"}),
        html.Div([
            html.Div([html.Label("Nombre de profils (K)"), dcc.Slider(2, 8, 1, value=best_k, marks={i: str(i) for i in range(2,9)}, id="cluster-k")], className="k-control"),
            html.Div([html.Label("Standardisation des IgE"), radio("scale-mode", [
                {"label": "Au sein de chaque puce", "value": "within"}, {"label": "Globale", "value": "global"}], "within")]),
        ], id="tools-profiles", className="page-tools", style={"display":"none"}),
    ], className="toolbar-wrap")
