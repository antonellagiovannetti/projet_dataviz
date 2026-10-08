"""The seven chapters of the Allergy Atlas narrative."""
from dash import dcc, html
import numpy as np
import pandas as pd
from components.common import graph_panel as panel, metric, next_step, note, number, page_heading, takeaway
from src import charts
from src.insights import chart_takeaway
from pages.glossary import glossary

CLINICAL = {"skin": "Symptômes cutanés", "asthma": "Traitement de l’asthme",
            "rhinitis": "Traitement de la rhinite", "dermatitis": "Traitement de la dermatite"}


def prevalence(df, column):
    known = df[column].isin(["Oui", "Non"])
    count = int(known.sum())
    value = 100 * df.loc[known, column].eq("Oui").mean() if count else np.nan
    return value, count


def cohort_metrics(df, ds, show_top=False):
    sens, known = prevalence(df, "sensitization")
    values = df.loc[:, list(ds.common_allergens)]
    rates = (100*values.gt(0).sum()/values.notna().sum().replace(0,np.nan)).dropna()
    top = rates.idxmax() if not rates.empty else None
    return html.Div([
        metric("PATIENTS SÉLECTIONNÉS", number(len(df)), f"sur {number(len(ds.frame))} dans la cohorte", True),
        metric("SENSIBILISATION · SOURCE", f"{number(sens, 1)} %" if known else "—",
               f"{number(df.sensitization.eq('Oui').sum())} oui · {number(known)} renseignés"),
        metric("IgE DÉTECTÉES / PATIENT", number(df.common_count.median(), 1), f"médiane · n = {number(df.common_count.notna().sum())} complets"),
        metric("ALLERGÈNE LE PLUS DÉTECTÉ", top.replace('_',' ') if top else '—', f"{number(rates[top],1)} % des mesures observées" if top else 'Aucune mesure') if show_top else
        metric("MESURES IgE DISPONIBLES", str(len(ds.allergens)), f"{len(ds.coverage)} technologies · {len(ds.common_allergens)} communes"),
    ], className="metrics-row")


def overview(df, ds, **_):
    return [
        page_heading("01", [f"{number(len(ds.frame))} patients.", html.Br(), "Des signaux aux profils."],
                     "Explorer la diversité des signatures IgE et leurs liens avec les informations cliniques disponibles."),
        cohort_metrics(df, ds),
        html.Div([
            panel("Un patient, plusieurs signaux", "Distribution des IgE détectées sur le panel commun aux trois puces.",
                  charts.common_count_histogram(df), "overview-hist", "SÉLECTION PAR GLISSER", class_name="main-panel",
                  insight=chart_takeaway("overview-hist", df=df, ds=ds),
                  footnote="Détection = valeur strictement positive. Une IgE détectée ne signifie pas automatiquement une allergie clinique."),
            html.Div([
                panel("Trois technologies", "Patients de la cohorte sélectionnée", charts.chip_bars(df), "overview-chips", "CLIQUER POUR FILTRER",
                      insight=chart_takeaway("overview-chips", df=df, ds=ds)),
                html.Div([html.Span("LA PREMIÈRE ÉTAPE", className="eyebrow"), html.H3("Comparer ce qui est comparable."),
                          html.P([html.Strong(str(len(ds.common_allergens))), " allergènes sont présents sur les trois plateformes. Ils forment le socle de cette exploration."]),
                          html.A("Comprendre les mesures →", href="#landscape")], className="editorial-note"),
            ], className="side-stack"),
        ], className="overview-grid"),
        next_step("#landscape", "02 — Comprendre les mesures"),
    ]


def landscape(df, ds, controls, **_):
    return [
        page_heading("02", "Tous les patients n’ont pas été mesurés de la même façon.",
                     "La couverture des puces conditionne les comparaisons. Les valeurs manquantes conditionnent leur interprétation."),
        html.Div([metric(chip, str(int(row.sum())), "mesures couvertes dans le fichier") for chip, row in ds.coverage.iterrows()] +
                 [metric("SOCLE COMMUN", str(len(ds.common_allergens)), "allergènes sur les trois plateformes", True)], className="metrics-row"),
        panel("La carte des mesures", "Couverture structurelle du fichier source complet, indépendante des filtres de patients.",
              charts.coverage_heatmap(ds.coverage, controls["coverage_sort"]), "coverage-chart",
              f"{len(ds.allergens)} ALLERGÈNES", insight=chart_takeaway("coverage-chart", df=df, ds=ds)),
        html.Div([
            panel("Ce que la clinique ne renseigne pas", f"Complétude sur {number(len(df))} patients sélectionnés.",
                  charts.clinical_missingness(df, controls["show_missing"]), "missing-chart",
                  insight=chart_takeaway("missing-chart", df=df, ds=ds, controls=controls)),
            html.Div([
                note("Absence de mesure ≠ valeur nulle", "Une case non mesurée par une puce n’est jamais remplacée par zéro."),
                note("Des codages à interpréter", "Le code 9 indique une information non exploitable : inconnue pour les traitements, sans objet ou non pertinente pour les symptômes cutanés."),
                note("52 valeurs négatives à écarter", "Le CSV contient 52 valeurs IgE à −1 chez 36 patients, sans définition dans les dictionnaires. Elles sont conservées dans la source et traitées comme manquantes pour l’analyse.", "warning"),
            ], className="method-stack"),
        ], className="two-columns"),
        next_step("#sensitization", "03 — Explorer les signatures IgE"),
    ]


def sensitization(df, ds, controls, cross, **_):
    common = ds.common_allergens
    selected = cross.get("allergen") or controls.get("allergen")
    plotted = df.sort_values(["cluster", "common_count"] if controls["heatmap_sort"] == "cluster" else ["common_count"], ascending=False)
    return [
        page_heading("03", "Plusieurs signaux chez un même patient.",
                     "Fréquences, intensités et diversité des signaux : plusieurs façons de lire un même profil biologique."),
        cohort_metrics(df, ds, show_top=True),
        note("Comparer les intensités avec prudence", "Les valeurs brutes sont exprimées dans les unités propres à chaque plateforme. Pour lire les moyennes ou médianes IgE, sélectionnez une seule technologie.") if controls["metric"] != "prevalence" and df.chip.nunique() > 1 else None,
        html.Div([
            panel("Quels allergènes sont les plus détectés ?", "Cliquez sur un allergène pour retenir les patients chez qui sa valeur est > 0.",
                  charts.top_allergens(df, common, metric=controls["metric"], top_n=controls["top_n"], selected_allergen=selected), "top-allergens", "PANEL COMMUN",
                  insight=chart_takeaway("top-allergens", df=df, ds=ds, controls=controls)),
            panel("Comment les signaux varient-ils avec l’âge ?", "Chaque point décrit une classe d’âge. Cliquez pour sélectionner sa population.",
                  charts.age_groups(df, controls["age_mode"]), "age-chart",
                  insight=chart_takeaway("age-chart", df=df, ds=ds, controls=controls)),
        ], className="two-columns equal"),
        panel("Les signatures, patient par patient", "Couleur = log(1 + IgE) ; échantillon déterministe stratifié par technologie, au plus 120 patients.",
              charts.patient_heatmap(plotted, common, max_patients=120, selected_allergen=selected, sort_by=controls["heatmap_sort"]), "patient-heatmap",
              "ZOOM & SURVOL", insight=chart_takeaway("patient-heatmap", df=df, ds=ds, controls=controls),
              footnote="La heatmap montre des intensités brutes transformées, pas une échelle cliniquement harmonisée entre puces. Les identifiants sont pseudonymisés."),
        panel("Combien de signaux par patient ?", "Une base identique de 91 allergènes pour toutes les technologies.",
              charts.common_count_histogram(df), "sensitivity-hist", insight=chart_takeaway("sensitivity-hist", df=df, ds=ds)),
        next_step("#clinical", "04 — Rapprocher biologie et clinique"),
    ]


def clinical(df, ds, controls, **_):
    outcome = controls["outcome"]
    positive = int(df[outcome].eq("Oui").sum())
    negative = int(df[outcome].eq("Non").sum())
    missing = len(df) - positive - negative
    return [
        page_heading("04", "Quand la biologie rencontre la clinique.",
                     "Les signatures IgE diffèrent-elles selon les manifestations ou les traitements déclarés ?"),
        html.Div([metric("OUI / PRÉSENT", number(positive), CLINICAL[outcome], True),
                  metric("NON / ABSENT", number(negative), "groupe de comparaison"),
                  metric("NON RENSEIGNÉ", number(missing), f"{number(100*missing/len(df),1) if len(df) else '—'} % de la sélection"),
                  metric("POPULATION ANALYSÉE", number(positive+negative), "cas renseignés pour cette information")], className="metrics-row"),
        panel("Quelles détections distinguent les deux groupes ?", f"{CLINICAL[outcome]} : différence de fréquence Oui − Non, en points de pourcentage.",
              charts.clinical_differential(df, outcome, ds.common_allergens), "clinical-difference",
              insight=chart_takeaway("clinical-difference", df=df, ds=ds, controls=controls),
              badge="ASSOCIATION ≠ CAUSALITÉ", footnote="Comparaison descriptive, sans ajustement pour l’âge, le sexe ou la puce. Les inconnus sont exclus et le dénominateur IgE observé est indiqué au survol."),
        html.Div([
            panel("La composition clinique", "Les données non renseignées restent visibles pour éviter une lecture trompeuse.",
                  charts.clinical_composition(df, outcome, controls["dimension"], show_missing=True), "clinical-composition",
                  insight=chart_takeaway("clinical-composition", df=df, ds=ds, controls=controls)),
            html.Div([note("Un traitement n’est pas une sévérité", "0 = aucun traitement ; 9 = inconnu ; autre code documenté = traitement déclaré. Ces informations ne décrivent pas automatiquement une maladie sévère."),
                      note("La population observée compte", "L’absence d’information peut dépendre du patient, du centre ou de la technologie. Les groupes renseignés ne sont pas nécessairement représentatifs de tous les patients.")], className="method-stack"),
        ], className="two-columns"),
        panel("Des caractéristiques qui se croisent", "Âge → sensibilisation (source) → symptômes cutanés → traitement de l’asthme.",
              charts.parallel_categories(df), "clinical-flow", "CAS COMPLETS UNIQUEMENT",
              insight=chart_takeaway("clinical-flow", df=df, ds=ds, controls=controls),
              footnote="Ces liens représentent des combinaisons de caractéristiques observées, pas des trajectoires temporelles ou causales."),
        next_step("#profiles", "05 — Faire émerger des profils"),
    ]


def profiles(df, ds, model, cross, controls, reference_frame, **_):
    score = model.scores.loc[model.scores.k.eq(model.k), "silhouette"].iloc[0]
    selected = cross.get("cluster") or (controls["clusters"][0] if len(controls.get("clusters") or []) == 1 else None)
    valid_profiles = df.loc[df.cluster.ne("Non attribué"), "cluster"]
    if selected is None and not valid_profiles.empty:
        selected = valid_profiles.mode().iloc[0]
    shown = df[df.cluster.eq(selected)] if selected is not None else df
    labels = model.labels
    fingerprint_cols = model.fingerprints.var(axis=0).nlargest(25).index
    standardized = model.standardized.loc[:, fingerprint_cols]
    eligible = standardized.index.intersection(df.index)
    return [
        page_heading("05", "Des familles de profils IgE émergent-elles ?",
                     "Une exploration non supervisée : seules les mesures IgE construisent les groupes. La clinique sert ensuite à les décrire."),
        html.Div([metric("PROFILS EXPLORATOIRES", str(model.k), f"K recommandé : {model.best_k}", True),
                  metric("SILHOUETTE", number(score, 3), "plus élevée = groupes mieux séparés"),
                  metric("VARIANCE PCA · 2 AXES", f"{number(100*sum(model.explained_variance[:2]),1)} %", "une projection partielle de la variabilité"),
                  metric("LIEN PROFILS / PUCE", number(model.platform_cramers_v, 3), "V de Cramér · 0 = pas d’association")], className="metrics-row"),
        html.P(f"Diagnostics du modèle sur la cohorte source : {number(len(model.labels))} patients éligibles. Les filtres changent les vues, pas le modèle.", className="context-caption"),
        panel("La carte des profils", "Cliquez sur un patient pour retenir son profil, ou utilisez le lasso pour dessiner votre sous-population.",
              charts.pca_scatter(df, model.explained_variance), "pca-chart", "SÉLECTION LIÉE AUX AUTRES VUES",
              insight=chart_takeaway("pca-chart", df=df, ds=ds, model=model)),
        html.Div([
            panel("L’empreinte de chaque profil", "Moyennes standardisées dans la sélection ; 25 allergènes discriminants du modèle source.",
                  charts.cluster_fingerprints(standardized.loc[eligible], labels.reindex(eligible)), "cluster-fingerprints",
                  insight=chart_takeaway("cluster-fingerprints", df=df, ds=ds, model=model)),
            panel(f"Les détections du profil {selected or '—'}", "Patients retenus du profil vs population avant sélection PCA / profil. Les autres filtres restent actifs.",
                  charts.cluster_excess(reference_frame.loc[reference_frame.cluster.ne("Non attribué")], ds.common_allergens, selected_cluster=selected, selected_df=df), "cluster-excess",
                  insight=chart_takeaway("cluster-excess", df=df, ds=ds, model=model, reference_frame=reference_frame, selected_cluster=selected)),
        ], className="two-columns equal"),
        panel("La technologie explique-t-elle les profils ?", "Composition des profils affichés par technologie. Compléter cette lecture par le V de Cramér calculé sur la source.",
              charts.cluster_platform_composition(df), "cluster-platform",
              insight=chart_takeaway("cluster-platform", df=df, ds=ds, model=model)),
        html.Div([html.H3(f"Lire le profil {selected or '—'} dans la sélection"), cohort_metrics(shown, ds),
                  html.Div([metric(CLINICAL[c], f"{number(prevalence(shown,c)[0],1)} %", f"n renseigné = {number(prevalence(shown,c)[1])}") for c in CLINICAL], className="metrics-row compact"),
                  takeaway(chart_takeaway("profile-summary", df=shown, ds=ds, model=model))], className="profile-summary"),
        html.Details([html.Summary("Méthode, choix de K et limites"),
                      html.P(model.method),
                      html.P(f"{model.excluded_count} patients incomplets sur le panel commun sont exclus du modèle, sans imputation. Ils restent disponibles dans les autres analyses."),
                      html.P("KMeans est ajusté sur les 91 dimensions standardisées, avec graine fixe. La PCA ne sert qu’à projeter les patients ; la silhouette est estimée sur un échantillon déterministe. Les modèles restent fixes lorsque les filtres changent."),
                      html.Div(html.Table([html.Thead(html.Tr([html.Th("K"), html.Th("Silhouette"), html.Th("Plus petit groupe"), html.Th("Plus grand groupe")])),
                                  html.Tbody([html.Tr([html.Td(int(r.k)), html.Td(number(r.silhouette, 3)), html.Td(number(r.smallest_cluster)), html.Td(number(r.largest_cluster))]) for r in model.scores.itertuples()])], className="data-table"), className="table-scroll"),
                      takeaway(chart_takeaway("model-scores", df=df, ds=ds, model=model)),
                      html.P("Un lien résiduel avec la puce peut subsister après standardisation. Le K maximisant la silhouette ne prouve pas l’existence de phénotypes médicaux distincts.")], className="method-details"),
        note("Des regroupements exploratoires", "Ces profils structurent la diversité biologique. Ils ne sont ni des diagnostics, ni des prédictions de sévérité."),
        next_step("#explorer", "06 — Construire et comparer vos cohortes"),
    ]


def comparison_value(df, key):
    if df is None:
        return "—"
    if key == "n":
        return number(len(df))
    if key == "age":
        return f"{number(df.age.median(),1)} ans · n={number(df.age.notna().sum())}"
    if key == "count":
        return number(df.common_count.median(), 1)
    rate, n = prevalence(df, key)
    return f"{number(rate,1)} % · n={number(n)}" if n else "— · n=0"


def explorer(df, ds, model, cohorts, **_):
    snapshots = {}
    for letter in ["a", "b"]:
        saved = cohorts.get(letter)
        snapshots[letter] = model.frame[model.frame.id.isin(saved["ids"])] if saved is not None else None
    a, b = snapshots["a"], snapshots["b"]
    both = a is not None and b is not None
    rows = [("Patients", "n"), ("Âge médian", "age"), ("Sensibilisation (variable source)", "sensitization"),
            ("IgE détectées, médiane · panel commun", "count"), ("Symptômes cutanés", "skin"),
            ("Traitement de l’asthme", "asthma"), ("Traitement de la rhinite", "rhinitis")]
    return [
        page_heading("06", "Une question. Deux cohortes.",
                     "Appliquez vos filtres, mémorisez une population, puis construisez la seconde pour comparer leurs signatures."),
        html.Div([
            html.Div([html.Span("COHORTE A", className="eyebrow"), html.H2(number(len(a)) if a is not None else "À construire"),
                      html.P(cohorts["a"].get("description", "") if a is not None else "Par exemple : les enfants et adolescents."),
                      html.Button("Enregistrer la sélection en A", id="save-a", className="primary-button")], className="cohort-card cohort-a"),
            html.Div([html.Span("COHORTE B", className="eyebrow"), html.H2(number(len(b)) if b is not None else "À construire"),
                      html.P(cohorts["b"].get("description", "") if b is not None else "Puis : les adultes, avec les mêmes critères."),
                      html.Button("Enregistrer la sélection en B", id="save-b", className="primary-button secondary")], className="cohort-card cohort-b"),
        ], className="two-columns equal"),
        html.Div([html.Span(f"Sélection actuelle : {number(len(df))} patients"),
                  html.Button("Exporter la sélection CSV ↓", id="export-cohort", className="text-button"),
                  html.Button("Effacer A et B", id="clear-cohorts", className="text-button")], className="cohort-actions"),
        html.Section([html.Div([html.H3("Les cohortes, côte à côte"), html.P("Les pourcentages cliniques utilisent uniquement les observations renseignées.")], className="panel-heading"),
                      html.Div(html.Table([html.Thead(html.Tr([html.Th("Indicateur"), html.Th("Cohorte A"), html.Th("Cohorte B")])),
                                           html.Tbody([html.Tr([html.Td(label), html.Td(comparison_value(a,key)), html.Td(comparison_value(b,key))]) for label,key in rows])], className="data-table"), className="table-scroll"),
                      takeaway(chart_takeaway("cohort-table", df=df, ds=ds, cohort_a=a, cohort_b=b))], className="chart-panel"),
        note("Chevauchement des populations", f"{number(len(set(a.id) & set(b.id)))} patients appartiennent aux deux cohortes. Les différences sont descriptives, sans test d’indépendance.") if both else
            note("Vos cohortes restent mémorisées", "Enregistrez A puis B. Les sélections sont conservées dans ce navigateur ; modifier les filtres ne modifie pas les cohortes enregistrées."),
        panel("La différence de signature IgE", "Différence B − A en points de pourcentage : gauche = plus fréquent dans A ; droite = plus fréquent dans B.",
              charts.cohort_difference(a,b,ds.common_allergens), "cohort-difference",
              insight=chart_takeaway("cohort-difference", df=df, ds=ds, cohort_a=a, cohort_b=b)) if both else
              html.Div([html.Span("A ↔ B"), html.H3("La comparaison commence avec deux populations."), html.P("Les signatures différentielles apparaîtront après l’enregistrement de A et B.")], className="empty-comparison"),
        next_step("#conclusions", "07 — Interpréter avec recul"),
    ]


def conclusions(df, ds, model, **_):
    source = ds.frame
    q1, q3 = source.common_count.quantile([.25,.75])
    known_skin = source.skin.isin(["Oui", "Non"]).sum()
    limits = [
        ("01", "La sévérité n’est pas disponible", "Severe_Allergy figure dans la documentation générale, mais est absente du CSV fourni. Aucune cible de sévérité n’a été reconstruite."),
        ("02", "La clinique est incomplète", "Les associations concernent seulement les données observées. Une valeur non renseignée ne signifie jamais l’absence d’un symptôme ou d’un traitement."),
        ("03", "Les puces restent différentes", "Le panel commun réduit le biais de couverture. Il ne rend pas identiques les unités, les seuils de détection ou les performances analytiques des plateformes."),
        ("04", "Association n’est pas causalité", "Les écarts descriptifs ne sont pas ajustés pour les facteurs de confusion et ne démontrent aucun mécanisme causal."),
        ("05", "Détection, sensibilisation et allergie", "Une mesure > 0 indique un signal dans ce fichier. La sensibilisation fournie par la source est une variable distincte. Le diagnostic d’allergie nécessite un contexte clinique."),
        ("06", "Des profils à explorer, pas à diagnostiquer", "Les groupes KMeans dépendent du prétraitement et du nombre de clusters. La projection PCA est une représentation partielle ; elle ne valide pas des phénotypes médicaux."),
    ]
    return [
        page_heading("07", "Structurer la complexité. Garder les limites visibles.",
                     "La valeur du dashboard : passer de centaines de mesures à des populations que l’on peut explorer, comparer et questionner."),
        html.Div([html.Span("LA RÉPONSE À NOTRE PROBLÉMATIQUE", className="eyebrow"),
                  html.H2("Des profils IgE exploratoires,\ndes liens cliniques à préciser."),
                  html.P(f"Sur les {len(ds.common_allergens)} allergènes communs, les signatures révèlent des profils hétérogènes. Leurs différences cliniques se décrivent parmi les cas renseignés, sans établir de causalité ni prédire la sévérité.")], className="closing-statement"),
        html.Div([
            html.Article([html.Strong(f"{number(q1)} à {number(q3)} signaux"), html.P("L’intervalle interquartile des détections communes illustre l’hétérogénéité biologique des patients.")]),
            html.Article([html.Strong(f"{number(known_skin)} observations cutanées"), html.P(f"Sur {number(len(source))} patients, seuls {number(100*known_skin/len(source),1)} % renseignent cette information. Les associations concernent cette population observée.")]),
            html.Article([html.Strong(f"K recommandé : {model.best_k}"), html.P("Des groupes fondés sur les seules IgE structurent l’exploration, mais leur pertinence clinique reste à valider.")]),
        ], className="findings-row"),
        html.P("Constats calculés sur la cohorte source complète ; les filtres ne modifient pas cette synthèse.", className="context-caption"),
        html.Div([html.Article([html.Span(i), html.Div([html.H3(title), html.P(body)])], className="limitation") for i,title,body in limits], className="limits-grid"),
        html.Details([html.Summary("Sources et décisions méthodologiques"),
                      html.Ul([html.Li("Source : allergenchipchallenge-data-corrected-final-hdh-sfa.csv, fourni localement."),
                               html.Li("Codages vérifiés dans acc-dictionnaire-final.xls et dictionnaire-acc-english.pdf."),
                               html.Li("Contexte pédagogique : Projets.pdf et brief du projet M2 IA/DATA."),
                               html.Li("Régions et départements pseudonymisés : aucune localisation réelle n’est inférée."),
                               html.Li("52 valeurs IgE négatives sont masquées dans l’analyse ; aucune valeur non mesurée n’est convertie en zéro."),
                               html.Li("Toutes les statistiques visibles sont calculées à partir du fichier local et de la sélection active.")]),
                      html.P(f"Version du fichier : {number(len(ds.frame))} patients · {len(ds.allergens)} mesures IgE · {len(ds.coverage)} technologies.")], className="method-details"),
        html.A("↺ Revenir au début de l’exploration", href="#overview", className="primary-button inline-button"),
    ]


PAGES = {"overview": overview, "landscape": landscape, "sensitization": sensitization,
         "clinical": clinical, "profiles": profiles, "explorer": explorer, "conclusions": conclusions,
         "glossary": glossary}
