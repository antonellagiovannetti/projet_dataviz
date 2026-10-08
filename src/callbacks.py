"""Coordinated selections, narrative rendering and durable cohort snapshots."""
from datetime import datetime, timezone
import math
from dash import ALL, Input, Output, State, ctx, dcc, html, no_update
from dash.exceptions import PreventUpdate
from components.common import number
from components.filters import FILTER_KEYS
from components.navbar import NAVIGATION, SECTIONS
from pages.glossary import render_terms
from pages.story import PAGES
from src.clustering import get_profiles
from src.metrics import filter_cohort

FILTER_LABELS = {"age": "Âge", "sex": "Sexe", "chip": "Puce", "sensitization": "Sensibilisation",
                 "region": "Région", "skin": "Peau", "asthma": "Traitement asthme", "rhinitis": "Traitement rhinite",
                 "cluster": "Profil", "allergen": "IgE", "ids": "Sélection PCA", "count_range": "IgE détectées"}

STORY_CONTROLS = {"coverage_sort": "common", "show_missing": True, "metric": "prevalence",
                  "top_n": 20, "age_mode": "standard", "heatmap_sort": "count",
                  "outcome": "skin", "dimension": "sensitization", "allergen": None, "clusters": [], "mode": "story"}


def preset_cohorts(key, model, ds, scaling):
    """Create two immutable populations from the source, never from active filters."""
    frame = model.frame
    choices = {
        "age": ((frame.age.between(0, 17), "Enfants · 0–17 ans, âge renseigné"),
                (frame.age.ge(18), "Adultes · 18 ans et plus, âge renseigné")),
        "sex": ((frame.sex.eq("Hommes"), "Hommes · sexe renseigné"),
                (frame.sex.eq("Femmes"), "Femmes · sexe renseigné")),
        "skin": ((frame.skin.eq("Oui"), "Avec symptômes cutanés · réponse Oui"),
                 (frame.skin.eq("Non"), "Sans symptômes cutanés · réponse Non")),
        "cluster": ((frame.cluster.eq("1"), "Profil 1 du modèle courant"),
                    (frame.cluster.eq("2"), "Profil 2 du modèle courant")),
    }
    if key not in choices:
        raise PreventUpdate
    saved_at = datetime.now(timezone.utc).isoformat()
    normalization = "au sein de chaque puce" if scaling != "global" else "globale"
    return {slot: {"ids": frame.loc[mask, "id"].tolist(),
                   "description": f"{description} · K = {model.k}, standardisation {normalization}" if key == "cluster" else description,
                   "saved_at": saved_at, "model_k": model.k, "scaling": scaling,
                   "source": ds.source_path.name, "preset": key}
            for slot, (mask, description) in zip(("a", "b"), choices[key])}


def selected_frame(model, filters, cross):
    frame = filter_cohort(model.frame, filters)
    extra = dict(cross or {})
    count_range = extra.pop("count_range", None)
    # A click on a known age class explicitly excludes unknown ages.
    if "age" in extra:
        extra["include_unknown_age"] = False
    frame = filter_cohort(frame, extra)
    if count_range is not None:
        frame = frame.loc[frame.common_count.between(count_range[0], count_range[1])]
    return frame


def describe_filter(key, value):
    if key == "ids":
        return f"Sélection PCA : {len(value)} patients"
    if key in ("age", "count_range"):
        return f"{FILTER_LABELS[key]} : {number(value[0])}–{number(value[1])}"
    if isinstance(value, list):
        value = ", ".join(map(str, value))
    return f"{FILTER_LABELS.get(key, key)} : {str(value).replace('_', ' ')}"


def register_callbacks(app, ds, default_model):
    max_age = int(math.ceil(ds.frame.age.max()))

    @app.callback(Output("reading-mode", "value"), Output("url", "hash"),
                  Input("reading-mode", "value"), Input("url", "hash"))
    def coordinate_mode(mode, route):
        # The laboratory is optional exploration; returning to Story resumes chapter 1.
        if route == "#explorer":
            if ctx.triggered_id == "reading-mode" and mode == "story":
                return no_update, "#overview"
            if mode != "explore":
                return "explore", no_update
        raise PreventUpdate

    @app.callback(Output("filter-store", "data"),
                  [Input(f"filter-{key}", "value") for key in FILTER_KEYS] + [Input("unknown-age", "value")])
    def collect_filters(*values):
        filters = dict(zip(FILTER_KEYS, values[:-1]))
        filters["include_unknown_age"] = "yes" in (values[-1] or [])
        return filters

    @app.callback([Output(f"filter-{key}", "value") for key in FILTER_KEYS] + [Output("unknown-age", "value")],
                  Input("reset-filters", "n_clicks"), Input("cluster-k", "value"), Input("scale-mode", "value"),
                  prevent_initial_call=True)
    def reset_controls(_clicks, _k, _scale):
        if ctx.triggered_id != "reset-filters":
            values = [no_update] * (len(FILTER_KEYS) + 1)
            values[FILTER_KEYS.index("cluster")] = []
            return values
        return [[0, max_age], [], [], [], [], [], [], [], [], None, ["yes"]]

    @app.callback(Output("cross-store", "data"),
                  Input("overview-chips", "clickData", allow_optional=True),
                  Input("top-allergens", "clickData", allow_optional=True),
                  Input("age-chart", "clickData", allow_optional=True),
                  Input("overview-hist", "selectedData", allow_optional=True),
                  Input("sensitivity-hist", "selectedData", allow_optional=True),
                  Input("pca-chart", "clickData", allow_optional=True),
                  Input("pca-chart", "selectedData", allow_optional=True),
                  Input("reset-filters", "n_clicks"),
                  Input("cluster-k", "value"), Input("scale-mode", "value"),
                  Input({"type": "remove-cross", "key": ALL}, "n_clicks"),
                  State("cross-store", "data"), State("reading-mode", "value"), prevent_initial_call=True)
    def crossfilter(chip, allergen, age, overview_range, sensitivity_range, pca_click, pca_selection,
                    _reset, _k, _scale, _remove, current, mode):
        if mode != "explore":
            raise PreventUpdate
        trigger = ctx.triggered_id
        state = dict(current or {})
        if trigger == "reset-filters":
            return {}
        if trigger in ("cluster-k", "scale-mode"):
            state.pop("cluster", None)
            state.pop("ids", None)
            return state if state != current else no_update
        if isinstance(trigger, dict):
            if not ctx.triggered[0].get("value"):
                raise PreventUpdate
            state.pop(trigger["key"], None)
            return state
        if trigger == "overview-chips" and chip and chip.get("points"):
            state["chip"] = chip["points"][0]["customdata"][0]
        elif trigger == "top-allergens" and allergen and allergen.get("points"):
            state["allergen"] = allergen["points"][0]["customdata"][0]
        elif trigger == "age-chart" and age and age.get("points"):
            state["age"] = age["points"][0]["customdata"][:2]
        elif trigger in ("overview-hist", "sensitivity-hist"):
            selection = overview_range if trigger == "overview-hist" else sensitivity_range
            if not selection:
                raise PreventUpdate
            if "range" in selection:
                state["count_range"] = selection["range"]["x"]
            elif selection.get("points"):
                bins = [point["customdata"] for point in selection["points"]]
                state["count_range"] = [min(v[0] for v in bins), max(v[1] for v in bins)]
            else:
                raise PreventUpdate
        elif trigger == "pca-chart":
            prop = ctx.triggered[0]["prop_id"].split(".")[-1]
            if prop == "selectedData" and pca_selection is not None:
                state["ids"] = list(dict.fromkeys(p["customdata"][0] for p in pca_selection.get("points", []) if p.get("customdata")))
            elif prop == "clickData" and pca_click and pca_click.get("points"):
                state["cluster"] = str(pca_click["points"][0]["customdata"][5])
            else:
                raise PreventUpdate
        else:
            raise PreventUpdate
        return state if state != current else no_update

    outputs = [Output("page-body", "children"), Output("active-filters", "children"),
               Output("cohort-size", "children"), Output("cohort-share", "children"), Output("age-label", "children")]
    outputs += [Output(f"nav-{key}", "className") for key, _ in NAVIGATION]
    outputs += [Output(f"tools-{key}", "style") for key in ("landscape", "sensitization", "clinical", "profiles")]
    outputs += [Output("filter-cluster", "options"), Output("page-progress", "style"), Output("mobile-count", "children"),
                Output("app-shell", "className"), Output("mode-note", "children")]

    @app.callback(outputs,
                  Input("url", "hash"), Input("filter-store", "data"), Input("cross-store", "data"),
                  Input("coverage-sort", "value"), Input("show-missing", "value"),
                  Input("allergen-metric", "value"), Input("top-n", "value"), Input("age-mode", "value"), Input("heatmap-sort", "value"),
                  Input("clinical-outcome", "value"), Input("clinical-dimension", "value"),
                  Input("cluster-k", "value"), Input("scale-mode", "value"), Input("cohort-store", "data"),
                  Input("reading-mode", "value"))
    def render_page(route, filters, cross, coverage_sort, missing, metric_mode, top_n, age_mode, heatmap_sort,
                    outcome, dimension, k, scaling, cohorts, mode):
        page = (route or "#overview").lstrip("#")
        if page not in PAGES:
            page = "overview"
        mode = "explore" if mode == "explore" or page == "explorer" else "story"
        # Story reads the same complete source and reference model on every visit.
        # Persisted Explore controls stay mounted and retain their own values.
        filters, cross = (filters or {}, cross or {}) if mode == "explore" else ({}, {})
        model = get_profiles(k=k, within_chip=scaling != "global") if mode == "explore" else default_model
        frame = selected_frame(model, filters, cross)
        reference_filters = {key:value for key,value in filters.items() if key != "cluster"}
        reference_cross = {key:value for key,value in cross.items() if key not in ("cluster", "ids")}
        reference_frame = selected_frame(model, reference_filters, reference_cross)
        controls = {"coverage_sort": coverage_sort, "show_missing": "yes" in (missing or []),
                    "metric": metric_mode, "top_n": top_n, "age_mode": age_mode, "heatmap_sort": heatmap_sort,
                    "outcome": outcome, "dimension": dimension, "allergen": filters.get("allergen"), "clusters": filters.get("cluster") or [], "mode": mode}
        if mode == "story":
            controls = dict(STORY_CONTROLS)
        contents = PAGES[page](df=frame, ds=ds, controls=controls, model=model, cross=cross, cohorts=cohorts or {}, reference_frame=reference_frame)
        if frame.empty and page != "glossary":
            contents.insert(1, html.Div("Aucun patient ne correspond à ces critères. Retirez un filtre ou réinitialisez la sélection.", role="status", className="empty-alert"))
        chips = []
        for key, value in filters.items():
            if key == "include_unknown_age" or value is None or value == [] or (key == "age" and value == [0,max_age]):
                continue
            chips.append(html.Span(describe_filter(key,value), className="filter-chip muted"))
        if not filters.get("include_unknown_age", True):
            chips.append(html.Span("Âges renseignés", className="filter-chip muted"))
        for key, value in cross.items():
            chips.append(html.Button([describe_filter(key,value), html.Span(" ×")],
                                     id={"type": "remove-cross", "key": key}, n_clicks=0,
                                     title="Retirer ce filtre graphique", className="filter-chip"))
        active = chips or html.Span("Population entière · aucun filtre actif", className="no-filter")
        age = filters.get("age") or [0,max_age]
        navigation = ["nav-link active" if key == page else "nav-link" for key, _ in NAVIGATION]
        toolbar_styles = [{} if key == page or (key == "profiles" and page == "explorer") else {"display": "none"} for key in ("landscape", "sensitization", "clinical", "profiles")]
        cluster_options = [{"label": f"Profil {i}", "value": str(i)} for i in range(1, int(k or default_model.k)+1)] + [{"label": "Non attribué", "value": "Non attribué"}]
        chapter_keys = [key for key, _ in SECTIONS]
        progress = (chapter_keys.index(page)+1)/len(chapter_keys)*100 if page in chapter_keys else 0
        chapter = html.Div(contents, key=page, className="chapter-content", **{"data-chapter": page})
        mode_note = (f"Parcours guidé · cohorte complète ({number(len(ds.frame))} patients). Les filtres Explore sont conservés pour votre retour."
                     if mode == "story" else
                     f"Exploration libre · {number(len(frame))} patients sélectionnés. Les filtres et sélections graphiques actualisent les résultats ; les cohortes A/B restent des instantanés sauvegardés.")
        return [chapter, active, number(len(frame)), f"{number(100*len(frame)/len(ds.frame),1)} % de la cohorte source",
                f"{age[0]}–{age[1]} ans", *navigation, *toolbar_styles, cluster_options, {"width": f"{progress}%"}, f"{number(len(frame))} · {number(100*len(frame)/len(ds.frame),1)} %",
                f"app-shell mode-{mode}", mode_note]

    @app.callback(Output("glossary-results", "children"), Output("glossary-count", "children"),
                  Input("glossary-search", "value", allow_optional=True))
    def search_glossary(query):
        if query is None:
            raise PreventUpdate
        return render_terms(query, ds)

    @app.callback(Output("cohort-store", "data"),
                  Input("save-a", "n_clicks", allow_optional=True), Input("save-b", "n_clicks", allow_optional=True),
                  Input("clear-cohorts", "n_clicks", allow_optional=True),
                  Input({"type": "cohort-preset", "key": ALL}, "n_clicks", allow_optional=True), State("cohort-store", "data"),
                  State("filter-store", "data"), State("cross-store", "data"), State("cluster-k", "value"), State("scale-mode", "value"),
                  prevent_initial_call=True)
    def save_cohort(a, b, clear, presets, cohorts, filters, cross, k, scale):
        trigger = ctx.triggered_id
        if isinstance(trigger, dict) and trigger.get("type") == "cohort-preset":
            if not presets or not any(presets):
                raise PreventUpdate
            return preset_cohorts(trigger["key"], get_profiles(k, scale != "global"), ds, scale)
        clicked = {"save-a": a, "save-b": b, "clear-cohorts": clear}.get(trigger)
        if not clicked:
            raise PreventUpdate
        if ctx.triggered_id == "clear-cohorts":
            return {}
        model = get_profiles(k, scale != "global")
        frame = selected_frame(model, filters, cross)
        result = dict(cohorts or {})
        criteria = [describe_filter(key,value) for key,value in (filters or {}).items()
                    if key != "include_unknown_age" and value is not None and value != []]
        criteria += [describe_filter(key,value) for key,value in (cross or {}).items()]
        result["a" if ctx.triggered_id == "save-a" else "b"] = {
            "ids": frame.id.tolist(), "description": " · ".join(criteria) or "Population entière",
            "saved_at": datetime.now(timezone.utc).isoformat(), "model_k": model.k, "scaling": scale,
            "source": ds.source_path.name,
        }
        return result

    @app.callback(Output("download-cohort", "data"), Input("export-cohort", "n_clicks", allow_optional=True),
                  State("filter-store", "data"), State("cross-store", "data"), State("cluster-k", "value"), State("scale-mode", "value"),
                  prevent_initial_call=True)
    def export_cohort(clicks, filters, cross, k, scale):
        if not clicks:
            raise PreventUpdate
        frame = selected_frame(get_profiles(k, scale != "global"), filters, cross)
        return dcc.send_data_frame(frame.to_csv, "allergy-atlas-cohorte.csv", index=False, sep=";", decimal=",")
