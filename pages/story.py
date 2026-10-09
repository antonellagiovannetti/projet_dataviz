"""A six-step cohort investigation, with a separate exploration laboratory."""
from dash import html
import numpy as np

from components.common import (
    graph_panel as panel, metric, note, number, page_heading, takeaway,
    story_question, method_decision, interpretation, transition_question,
    exploration_section,
)
from pages.glossary import glossary
from src import charts
from src.insights import chart_takeaway, clinical_example


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
    rates = (100 * values.gt(0).sum() / values.notna().sum().replace(0, np.nan)).dropna()
    top = rates.idxmax() if not rates.empty else None
    return html.Div([
        metric("PATIENTS SÉLECTIONNÉS", number(len(df)), f"sur {number(len(ds.frame))} dans la cohorte", True),
        metric("SENSIBILISATION · SOURCE", f"{number(sens, 1)} %" if known else "—",
               f"{number(df.sensitization.eq('Oui').sum())} oui · {number(known)} renseignés"),
        metric("IgE DÉTECTÉES / PATIENT", number(df.common_count.median(), 1),
               f"médiane · n = {number(df.common_count.notna().sum())} complets"),
        metric("ALLERGÈNE LE PLUS DÉTECTÉ", top.replace('_', ' ') if top else '—',
               f"{number(rates[top], 1)} % des mesures observées" if top else 'Aucune mesure') if show_top else
        metric("MESURES IgE DANS LE FICHIER", str(len(ds.allergens)),
               f"{len(ds.coverage)} technologies · {len(ds.common_allergens)} communes"),
    ], className="metrics-row")


def _diversity_message(df, common):
    """Describe the active cohort, including empty and homogeneous selections."""
    complete = df.loc[df.common_count.notna(), list(common)]
    if complete.empty:
        return "Aucun profil complet dans cette sélection : la diversité des combinaisons ne peut pas être décrite ici."
    patterns = len(complete.gt(0).drop_duplicates())
    if patterns == 1:
        return "Les profils complets de cette sélection partagent la même combinaison de détections. Les intensités peuvent néanmoins différer."
    return (f"{number(patterns)} combinaisons de détections distinctes parmi {number(len(complete))} profils complets : "
            "une fréquence globale ne résume pas les combinaisons observées chez chaque patient.")


def overview(df, ds, **_):
    sens, known = prevalence(df, "sensitization")
    counts = df.common_count.dropna()
    if counts.nunique() > 1:
        implication = "Le seul statut de sensibilisation ne décrit pas combien de signaux IgE sont détectés chez un patient. Il faut donc regarder les profils plus en détail."
    elif len(counts):
        implication = "Cette sélection ne montre pas de dispersion du nombre de détections. Un même nombre peut toutefois recouvrir des allergènes différents."
    else:
        implication = "Sans profil complet dans cette sélection, nous ne pouvons pas décrire la dispersion des détections."
    return [
        page_heading("01", [f"{number(len(df))} patients. {len(ds.allergens)} mesures IgE.", html.Br(),
                            "Comment rendre cette complexité lisible ?"],
                     "Un patient peut présenter plusieurs signaux IgE en même temps. Explorons leurs combinaisons et leurs liens cliniques, sans confondre profil biologique et sévérité."),
        html.P(f"{len(ds.allergens)} mesures différentes sont présentes dans le fichier ; chaque technologie n’en mesure qu’une partie. "
               "Allergy Atlas est destiné aux allergologues impliqués dans la recherche clinique : observer une cohorte, comparer des profils et formuler des hypothèses, sans diagnostic individuel.", className="context-caption"),
        html.Div([
            metric("PATIENTS", number(len(df)), f"sur {number(len(ds.frame))} dans la source", True),
            metric("MESURES IgE DANS LE FICHIER", str(len(ds.allergens)), "pas toutes mesurées chez chaque patient"),
            metric("TECHNOLOGIES", str(df.chip.nunique()), f"{len(ds.coverage)} dans le fichier source"),
            metric("SENSIBILISÉS · SOURCE", f"{number(sens, 1)} %" if known else "—", f"sur {number(known)} statuts renseignés"),
        ], className="metrics-row"),
        story_question("Les patients présentent-ils des profils simples ou très différents les uns des autres ?",
                       "Commençons par un indicateur lisible : le nombre de détections sur les allergènes mesurés par les trois technologies."),
        panel("Combien de signaux retrouve-t-on chez un patient ?",
              "La distribution permet de voir ce qu’une valeur moyenne masquerait : l’étendue des profils individuels.",
              charts.common_count_histogram(df), "overview-hist", "PANEL COMMUN",
              lecture="Horizontal : nombre d’IgE > 0 sur le panel commun. Vertical : patients. Pointillés : médiane ; bande claire : les 50 % centraux.",
              insight=chart_takeaway("overview-hist", df=df, ds=ds),
              caution="Une détection dans le fichier n’équivaut ni à un diagnostic d’allergie ni à un niveau de sévérité. Seuls les panels complets sont comptés."),
        exploration_section("Pourquoi ce nombre ne suffit-il pas ?", [interpretation(implication)]),
        exploration_section("Comment les patients se répartissent-ils entre les technologies ?", [
            panel("Combien de patients ont été mesurés avec chaque technologie ?",
                  "Les effectifs situent les trois sources de mesures avant d’examiner leur comparabilité.",
                  charts.chip_bars(df), "overview-chips", "EXPLORATION",
                  lecture="Une barre par technologie ; sa hauteur donne l’effectif de la sélection. En mode Explore, un clic filtre les patients.",
                  insight=chart_takeaway("overview-chips", df=df, ds=ds),
                  caution="Les technologies ne constituent pas des groupes de sévérité clinique."),
        ]),
        transition_question("Mais avant d’aller plus loin, peut-on réellement comparer tous les patients entre eux ?",
                            "#landscape", "Vérifier comment les patients ont été mesurés →"),
    ]


def landscape(df, ds, controls, **_):
    complete = int(ds.frame.common_count.notna().sum())
    missing_state = "non renseignées" if controls["show_missing"] else "renseignées"
    return [
        page_heading("02", "Peut-on vraiment comparer tous les patients ?",
                     "Compter les IgE détectées semble simple. Mais les trois technologies ne mesurent pas le même nombre d’allergènes."),
        html.Div([metric(chip, str(int(row.sum())), "allergènes couverts dans le fichier")
                  for chip, row in ds.coverage.iterrows()] +
                 [metric("SOCLE COMMUN", str(len(ds.common_allergens)), "allergènes sur les trois technologies", True)], className="metrics-row"),
        interpretation("Compter toutes les détections favoriserait mécaniquement ALEX, dont le panel offre davantage de possibilités de détection.", label="LE PREMIER OBSTACLE"),
        panel("Les trois technologies mesurent-elles les mêmes allergènes ?",
              "La matrice rend visible le biais de couverture qu’un simple total de détections cacherait.",
              charts.coverage_heatmap(ds.coverage, controls["coverage_sort"]), "coverage-chart", "FICHIER SOURCE COMPLET",
              lecture="Colonnes : allergènes ; lignes : technologies. Turquoise : mesure couverte ; gris : allergène absent du panel.",
              insight=chart_takeaway("coverage-chart", df=df, ds=ds),
              caution="La couverture décrit le fichier source, indépendamment des filtres. Une case grise n’est pas une mesure égale à zéro."),
        method_decision("1", "Comparer sur un même panel",
                        f"Nous retenons les {len(ds.common_allergens)} allergènes communs pour les comparaisons transversales. "
                        "Cela réduit le biais de couverture, sans rendre identiques les unités ou les performances des technologies.",
                        steps=[(str(len(ds.allergens)), "mesures dans le fichier"),
                               (str(len(ds.common_allergens)), "mesures communes"),
                               (number(complete), "patients complets dans la source")]),
        html.P("Les panels complets sont nécessaires pour compter les détections et construire les groupes. "
               "Pour la fréquence d’un allergène, le dénominateur reste son nombre de mesures effectivement observées.", className="context-caption"),
        method_decision("2", "Garder les inconnus visibles",
                        "Une information inconnue ne devient ni une absence de symptôme ni une valeur nulle. "
                        "Chaque comparaison clinique utilise son effectif réellement renseigné."),
        panel("Quelles informations cliniques sont réellement disponibles ?",
              f"Sur les {number(len(df))} patients affichés, la complétude détermine la population que l’on peut comparer.",
              charts.clinical_missingness(df, controls["show_missing"]), "missing-chart",
              lecture=f"Chaque barre donne la part d’informations {missing_state} pour une variable. Le survol précise les effectifs.",
              insight=chart_takeaway("missing-chart", df=df, ds=ds, controls=controls),
              caution="Les patients renseignés peuvent différer des autres. Les résultats cliniques ne décrivent donc pas nécessairement toute la cohorte."),
        exploration_section("Comment les codages et les valeurs invalides sont-ils traités ?", [
            note("Absence de mesure ≠ valeur nulle", "Les mesures absentes du panel d’une technologie ne sont jamais remplacées par zéro."),
            note("Le code 9 reste une information inconnue", "Pour les traitements : inconnu. Pour les symptômes cutanés : sans objet ou non pertinent. Il n’est pas assimilé à « Non »."),
            note("52 valeurs négatives écartées de l’analyse", "Le CSV contient 52 valeurs IgE à −1 chez 36 patients, sans définition dans les dictionnaires. Elles restent intactes dans la source et sont traitées comme manquantes dans l’analyse.", "warning"),
        ]),
        transition_question(f"Sur ce même panel de {len(ds.common_allergens)} allergènes, à quoi ressemblent les profils IgE ?",
                            "#sensitization", "Explorer les profils IgE →",
                            "Le périmètre de comparaison est maintenant défini. Regardons comment les signaux se répartissent et se combinent."),
    ]


def sensitization(df, ds, controls, cross, **_):
    common = ds.common_allergens
    selected = cross.get("allergen") or controls.get("allergen")
    plotted = df.sort_values(["cluster", "common_count"] if controls["heatmap_sort"] == "cluster" else ["common_count"], ascending=False)
    count = df.common_count.dropna()
    q1, median, q3 = count.quantile([.25, .5, .75])
    is_frequency = controls["metric"] == "prevalence"
    metric_word = "moyenne" if controls["metric"] in {"mean", "mean_ige"} else "médiane"
    return [
        page_heading("03", "Les patients ont-ils vraiment des profils similaires ?",
                     f"Sur le panel commun de {len(common)} allergènes, passons d’une vue de la cohorte aux combinaisons observées chez chaque patient."),
        story_question("Quels allergènes sont les plus souvent détectés ?" if is_frequency else f"Quels allergènes ont les IgE {metric_word}s les plus élevées ?",
                       "Le classement repère les signaux dominants dans la sélection, avant d’examiner comment ils se combinent.", label="1 · VUE GLOBALE"),
        note("Les intensités nécessitent une seule technologie", "Les valeurs brutes utilisent les unités propres aux plateformes. Filtrez une seule technologie pour comparer les intensités moyennes ou médianes.")
        if not is_frequency and df.chip.nunique() > 1 else None,
        panel("Quels allergènes dominent dans la sélection ?",
              "Le taux correspond aux mesures IgE strictement positives (> 0) parmi les mesures disponibles ; il ne définit pas une allergie clinique.",
              charts.top_allergens(df, common, metric=controls["metric"], top_n=controls["top_n"], selected_allergen=selected), "top-allergens", "PANEL COMMUN",
              lecture=("Une barre par allergène ; longueur : fréquence de détection. Les traits fins indiquent l’incertitude statistique (IC 95 %)." if is_frequency else
                       f"Une barre par allergène ; longueur : IgE {metric_word} dans les valeurs observées, en unités propres à chaque technologie."),
              insight=chart_takeaway("top-allergens", df=df, ds=ds, controls=controls),
              caution="Le classement porte sur les données observées de la sélection, pas sur la fréquence des allergies dans la population générale."),
        interpretation("La fréquence d’un allergène ne dit pas avec quels autres signaux il apparaît chez un même patient."),
        story_question("Les patients présentent-ils les mêmes combinaisons de signaux ?",
                       "Deux patients avec le même nombre de détections peuvent présenter des combinaisons entièrement différentes.", label="2 · VUE PATIENT"),
        exploration_section("Retrouver la distribution et ses repères chiffrés", [
        panel("Combien de signaux retrouve-t-on chez un patient ?",
              "Comparer la dispersion, plutôt que résumer tous les patients par une seule moyenne.",
              charts.common_count_histogram(df), "sensitivity-hist",
              lecture="Horizontal : détections sur le panel commun ; vertical : effectifs. Pointillés : médiane ; bande claire : Q1–Q3.",
              insight=chart_takeaway("sensitivity-hist", df=df, ds=ds),
              caution="Seuls les panels complets sont comptés. Deux patients ayant le même total peuvent détecter des allergènes différents.")
        ]),
        panel("Quels signaux se combinent chez les mêmes patients ?",
              "La carte complète le total de détections en montrant où se trouvent les signaux, patient par patient.",
              charts.patient_heatmap(plotted, common, max_patients=120, selected_allergen=selected, sort_by=controls["heatmap_sort"]), "patient-heatmap", "ÉCHANTILLON ≤ 120 PATIENTS",
              lecture="Colonnes : allergènes ; lignes : patients pseudonymisés. La couleur représente log(1 + IgE), pour rendre visibles des intensités très différentes.",
              insight=_diversity_message(df, common),
              caution="L’échantillon est déterministe et stratifié. Les couleurs proviennent des intensités brutes transformées ; elles ne constituent pas une échelle clinique harmonisée entre technologies."),
        exploration_section("Ces profils diffèrent-ils selon l’âge ?", [
            panel("Comment les profils varient-ils entre classes d’âge ?",
                  "Cette comparaison situe la diversité biologique dans des sous-populations d’âges différents.",
                  charts.age_groups(df, controls["age_mode"]), "age-chart",
                  lecture="Haut, turquoise : sensibilisation source et IC 95 %. Bas, violet : médiane des détections et quartiles Q1–Q3.",
                  insight=chart_takeaway("age-chart", df=df, ds=ds, controls=controls),
                  caution="Il s’agit de patients différents, pas du suivi d’un même patient au cours de sa vie. Les âges inconnus sont exclus de cette vue."),
        ]),
        transition_question("Cette diversité biologique se retrouve-t-elle dans les informations cliniques ?",
                            "#clinical", "Comparer aux informations cliniques →",
                            "Les profils peuvent maintenant être rapprochés des symptômes et traitements réellement renseignés."),
    ]


def clinical(df, ds, controls, **_):
    outcome = controls["outcome"]
    clinical_factor = "les symptômes cutanés" if outcome == "skin" else "le " + CLINICAL[outcome].lower()
    positive = int(df[outcome].eq("Oui").sum())
    negative = int(df[outcome].eq("Non").sum())
    missing = len(df) - positive - negative
    example = clinical_example(df, ds.common_allergens, outcome=outcome)
    example_block = note("Un exemple ne peut pas être calculé ici", example["reason"])
    if example["available"]:
        delta = example["difference"]
        example_block = html.Section([
            html.Span("UN EXEMPLE DANS LA SÉLECTION", className="eyebrow"),
            html.H3(str(example["allergen"]).replace("_", " ")),
            html.P(CLINICAL[outcome], className="context-caption"),
            html.Div([
                metric("GROUPE OUI", f"{number(example['yes_rate'], 1)} %", f"n IgE observé = {number(example['yes_n'])}"),
                metric("GROUPE NON", f"{number(example['no_rate'], 1)} %", f"n IgE observé = {number(example['no_n'])}"),
                metric("ÉCART OUI − NON", f"{'+' if delta > 0 else ''}{number(delta, 1)} points", "différence de fréquence de détection", True),
            ], className="metrics-row compact"),
            interpretation(example["conclusion"], label="CE QUE L’ON PEUT DIRE"),
            html.P("Cet écart ne démontre pas que l’allergène provoque les symptômes, ni qu’il prédit à lui seul une allergie sévère.", className="chart-footnote"),
        ], className="clinical-example")
    return [
        page_heading("04", "Certains profils IgE sont-ils liés à des symptômes ?",
                     "Nous pouvons comparer les signatures selon la clinique disponible. La variable Severe_Allergy, documentée dans le dictionnaire, est absente du fichier CSV."),
        html.Div([
            note("Ce que nous pouvons faire", "Comparer les détections selon les symptômes cutanés ou les traitements de l’asthme, de la rhinite et de la dermatite."),
            note("Ce que nous ne pouvons pas faire", "Transformer un traitement ou une somme d’IgE en score de sévérité. Un signal biologique n’est pas un diagnostic.", "warning"),
        ], className="clinical-contrast two-columns equal"),
        story_question(f"Les détections diffèrent-elles selon {clinical_factor} ?",
                       "Le statut clinique inconnu est exclu du calcul Oui/Non. Pour chaque allergène, le dénominateur est le nombre de mesures IgE effectivement disponibles."),
        html.Div([
            metric("OUI / PRÉSENT", number(positive), CLINICAL[outcome], True),
            metric("NON / ABSENT", number(negative), "groupe de comparaison"),
            metric("NON RENSEIGNÉ / NON PERTINENT", number(missing), f"{number(100 * missing / len(df), 1) if len(df) else '—'} % de la sélection"),
            metric("INFORMATION CLINIQUE CONNUE", number(positive + negative), "avant vérification de chaque mesure IgE"),
        ], className="metrics-row"),
        panel("Quelles détections distinguent les groupes Oui et Non ?",
              f"Comparer les fréquences selon {clinical_factor} pour repérer des signaux à approfondir.",
              charts.clinical_differential(df, outcome, ds.common_allergens), "clinical-difference", badge="LIEN OBSERVÉ ≠ CAUSE DÉMONTRÉE",
              lecture="Chaque barre mesure l’écart Oui − Non, en points de pourcentage. À droite : plus fréquent dans Oui ; à gauche : plus fréquent dans Non.",
              insight=chart_takeaway("clinical-difference", df=df, ds=ds, controls=controls),
              caution="Différences descriptives non ajustées : âge, sexe, technologie et données cliniques manquantes peuvent influencer les écarts. IgE > 0 est un seuil technique de lecture, pas un diagnostic."),
        html.P("Exemple illustratif fixé à l’avance : Ara h 2, une composante de l’arachide. Le choix ne découle pas d’un classement automatique des plus grands écarts ; il sert à expliquer comment lire une comparaison.", className="context-caption"),
        example_block,
        exploration_section("Composition clinique et caractéristiques croisées", [
            panel("La clinique renseignée se répartit-elle de la même façon ?",
                  "La composition montre les effectifs relatifs et la place des informations inconnues dans les sous-populations.",
                  charts.clinical_composition(df, outcome, controls["dimension"], show_missing=True), "clinical-composition",
                  lecture="Une barre par sous-population ; les segments représentent Oui, Non et Inconnu, avec leur part dans le groupe.",
                  insight=chart_takeaway("clinical-composition", df=df, ds=ds, controls=controls),
                  caution="Une part inconnue élevée limite l’interprétation. Un traitement déclaré ne mesure pas directement la sévérité."),
            panel("Quelles caractéristiques cliniques se retrouvent ensemble ?",
                  "La vue croisée replace les symptômes dans plusieurs caractéristiques observées chez les mêmes patients.",
                  charts.parallel_categories(df), "clinical-flow", "CAS COMPLETS UNIQUEMENT",
                  lecture="De gauche à droite : âge, sensibilisation source, symptômes cutanés, traitement de l’asthme. L’épaisseur des liens représente les effectifs.",
                  insight=chart_takeaway("clinical-flow", df=df, ds=ds, controls=controls),
                  caution="Ces liens ne sont ni des trajectoires dans le temps ni des mécanismes causaux. Les cas incomplets sur ces variables sont exclus."),
        ]),
        transition_question(f"Et si nous regardions les {len(ds.common_allergens)} mesures ensemble ?",
                            "#profiles", "Faire émerger des groupes de profils →",
                            "Comparer un allergène à la fois reste limité : chaque patient possède une signature complète. Cherchons des profils proches sans utiliser la clinique pour les construire."),
    ]


def profiles(df, ds, model, cross, controls, reference_frame, **_):
    requested = cross.get("cluster") or (controls["clusters"][0] if len(controls.get("clusters") or []) == 1 else None)
    assigned = df.loc[df.cluster.ne("Non attribué")]
    selected = requested or (assigned.cluster.mode().iloc[0] if not assigned.empty else None)
    shown = df.loc[df.cluster.eq(str(selected))]
    eligible = df.index.intersection(model.standardized.index)
    # Use a stable set of characteristic allergens from the source model.
    columns = model.fingerprints.var(axis=0, ddof=0).nlargest(25).index
    standardized = model.standardized.loc[:, columns]
    score = model.scores.loc[model.scores.k.eq(model.k), "silhouette"].iloc[0]
    scaling = "au sein de chaque technologie" if model.within_chip else "sur toute la cohorte"
    platform = model.platform_cramers_v
    platform_message = (
        f"V de Cramér = {number(platform, 3)} sur le modèle source : le lien avec la technologie est faible dans cette solution. "
        "Cela ne suffit toutefois pas à exclure un effet de technologie ou de recrutement."
        if np.isfinite(platform) and platform < .1 else
        f"V de Cramér = {number(platform, 3)} sur le modèle source. La composition par technologie doit être prise en compte pour interpréter cette solution."
    )
    pca_figure = charts.pca_scatter(df, model.explained_variance)
    if controls.get("mode") == "story":
        pca_figure.update_layout(dragmode="zoom")
    return [
        page_heading("05", "Peut-on faire émerger des groupes de patients aux profils proches ?",
                     f"Chaque patient est décrit par {len(ds.common_allergens)} mesures simultanément. Regardons maintenant toute sa signature, au lieu de comparer les allergènes séparément."),
        story_question("Pourquoi regrouper les profils ?",
                       "Pour rapprocher les patients dont les signatures IgE se ressemblent. Les informations cliniques ne servent pas à former les groupes ; elles permettent ensuite de les décrire."),
        interpretation("KMeans regroupe les profils à partir des 91 mesures IgE ; la PCA sert à les représenter sur deux axes. Ce ne sont pas des catégories diagnostiques.", label="COMMENT SONT CONSTRUITS LES GROUPES"),
        exploration_section("Pourquoi KMeans, cette standardisation et ce nombre de groupes ?", [
        method_decision("3", "Regarder les 91 mesures ensemble",
                        f"La transformation log1p réduit le poids des grandes valeurs. La standardisation {scaling} met les mesures sur une échelle de travail commune.",
                        steps=[("91 mesures", "panel commun · cas complets"), ("log1p", "log(1 + IgE)"),
                               ("Standardisation", scaling), ("KMeans", "regrouper dans les 91 dimensions")]),
        interpretation("KMeans compare les 91 mesures. La PCA — une carte simplifiée des profils — sert uniquement à les représenter sur deux axes.",
                       label="REGROUPER, PUIS VISUALISER"),
        html.Section([
            html.Div([html.H3(f"Pourquoi proposer {model.best_k} groupes ?"),
                      html.P("La silhouette mesure si les patients sont plus proches de leur groupe que des autres. Plus le score est élevé, mieux les groupes sont séparés selon ce critère.")], className="panel-heading"),
            html.Div(html.Table([
                html.Thead(html.Tr([html.Th("Nombre de groupes"), html.Th("Silhouette"), html.Th("Plus petit groupe"), html.Th("Plus grand groupe")])),
                html.Tbody([html.Tr([
                    html.Td([str(int(row.k)), " · proposé" if int(row.k) == model.best_k else ""]),
                    html.Td(number(row.silhouette, 3)), html.Td(number(row.smallest_cluster)), html.Td(number(row.largest_cluster)),
                ], className="model-score-best" if int(row.k) == model.best_k else "") for row in model.scores.itertuples()]),
            ], className="data-table"), className="table-scroll"),
            takeaway(f"Parmi les solutions testées, {model.best_k} groupes donnent la meilleure séparation selon ce critère. Cela décrit une structure statistique, pas des catégories médicales."),
            html.P(f"Cohorte source : {number(len(model.labels))} patients complets. Scores calculés sur le même échantillon fixe de {number(model.scores.sample_n.iloc[0])} patients. "
                   f"Solution affichée : K = {model.k}, silhouette {number(score, 3)}. Explore permet de changer K et la standardisation.", className="chart-footnote"),
        ], className="chart-panel model-choice")
        ]),
        panel("Des groupes de profils proches apparaissent-ils ?",
              "La carte PCA situe les patients et permet de voir comment les groupes se répartissent dans une projection simplifiée.",
              pca_figure, "pca-chart", "PCA · CARTE DES PROFILS",
              lecture="Un point représente un patient ; sa couleur indique son groupe et sa forme sa technologie. En Explore, le lasso sélectionne une région de la carte.",
              insight=chart_takeaway("pca-chart", df=df, ds=ds, model=model),
              caution=f"Les deux axes ne résument que {number(100 * sum(model.explained_variance[:2]), 1)} % de la variation des mesures. Une proximité sur la carte ne constitue pas une proximité clinique démontrée."),
        story_question("Quels signaux IgE distinguent les groupes ?",
                       "Les empreintes décrivent leur signature biologique, avant d’examiner la clinique renseignée."),
        panel("Quels allergènes caractérisent les groupes affichés ?",
              "L’empreinte donne un contenu biologique aux groupes, au-delà de leur position sur la carte.",
              charts.cluster_fingerprints(standardized.loc[eligible], model.labels.reindex(eligible)), "cluster-fingerprints",
              lecture="Lignes : groupes ; colonnes : 25 allergènes caractéristiques du modèle source. Turquoise : moyenne standardisée positive ; violet : négative.",
              insight=chart_takeaway("cluster-fingerprints", df=df, ds=ds, model=model),
              caution="Les moyennes suivent la sélection affichée. Les couleurs décrivent des mesures transformées, sans seuil de diagnostic ni ordre de gravité."),
        story_question("Ces groupes présentent-ils des caractéristiques cliniques différentes ?",
                       "Décrivons les informations disponibles après la création des groupes, sans utiliser la clinique pour les construire."),
        exploration_section("Clinique détaillée du groupe sélectionné", [
        html.Div([html.H3(f"Quelle clinique est renseignée dans le groupe {selected or '—'} ?"),
                      cohort_metrics(shown, ds),
                      html.Div([metric(CLINICAL[column], f"{number(prevalence(shown, column)[0], 1)} %" if prevalence(shown, column)[1] else "—",
                                       f"Oui parmi {number(prevalence(shown, column)[1])} patients renseignés") for column in CLINICAL], className="metrics-row compact"),
                      takeaway(chart_takeaway("profile-summary", df=shown, ds=ds, model=model))], className="profile-summary"),
        ]),
        cluster_clinical_table(df),
        exploration_section("Les groupes sont-ils liés à la technologie de mesure ?", [
        story_question("Ces groupes sont-ils simplement dus aux technologies de mesure ?",
                       "Vérifier leur composition par puce aide à repérer un effet technique qui pourrait se faire passer pour une différence biologique."),
        panel("Chaque groupe mélange-t-il plusieurs technologies ?",
              "Cette vérification aide à distinguer un profil biologique apparent d’un possible effet lié aux plateformes.",
              charts.cluster_platform_composition(df), "cluster-platform",
              lecture="Une barre par groupe ; les segments colorés indiquent la part de chaque technologie dans les patients affichés.",
              insight=chart_takeaway("cluster-platform", df=df, ds=ds, model=model),
              caution="La standardisation n’élimine ni les différences de calibration ni les biais de recrutement. Le V de Cramér faible ne prouve pas l’absence d’effet de plateforme."),
        interpretation(platform_message)
        ]),
        exploration_section("Comparer en détail un groupe à la cohorte", [
            panel(f"Quelles détections distinguent le groupe {selected or '—'} ?",
                  "Comparer le groupe retenu à la population avant sélection de profil ou lasso, en conservant les autres filtres.",
                  charts.cluster_excess(reference_frame.loc[reference_frame.cluster.ne("Non attribué")], ds.common_allergens,
                                        selected_cluster=selected, selected_df=df), "cluster-excess",
                  lecture="Une barre par allergène ; écart de fréquence groupe − population de référence, en points de pourcentage.",
                  insight=chart_takeaway("cluster-excess", df=df, ds=ds, model=model, reference_frame=reference_frame, selected_cluster=selected),
                  caution="Le groupe appartient à la référence : cette comparaison descriptive n’oppose pas deux populations indépendantes.")
        ]),
        exploration_section("Reproductibilité et limites de la méthode", [
            note("Un modèle fixe pour une exploration cohérente", model.method),
            html.P(f"{number(model.excluded_count)} patients incomplets sont exclus du regroupement, sans imputation ; ils restent disponibles dans les autres analyses. "
                   "Les filtres changent les patients affichés, sans réapprendre les groupes. Les numéros ordonnent le nombre moyen de détections, pas la sévérité.", className="context-caption"),
        ]),
        transition_question("Des profils apparaissent. Qu’est-ce que cela nous permet réellement de conclure ?",
                            "#conclusions", "Distinguer les constats et les limites",
                            "Ces groupes rendent les profils IgE plus lisibles. Leur portée clinique reste à examiner."),
    ]



def cluster_clinical_table(df):
    """Clinical status frequencies per displayed cluster, excluding unknown responses."""
    assigned = df.loc[df.cluster.ne("Non attribué")]
    labels = sorted(assigned.cluster.dropna().unique(), key=str)
    if not labels:
        return note("Aucun groupe attribué", "Aucun patient doté d’un profil complet dans cette sélection.")
    headers = [html.Th("Groupe · effectif")] + [html.Th(title) for title in CLINICAL.values()]
    rows = []
    for label in labels:
        cohort = assigned.loc[assigned.cluster.eq(label)]
        cells = [html.Td(f"{label} · n = {number(len(cohort))}")]
        for key in CLINICAL:
            value, known = prevalence(cohort, key)
            cells.append(html.Td(f"{number(value, 1)} % (n={number(known)})" if known else "Non calculable (n=0)"))
        rows.append(html.Tr(cells))
    return html.Section([
        html.H3("Les manifestations cliniques diffèrent-elles entre les groupes ?"),
        html.P("Pour chaque groupe, proportion de réponses Oui parmi les seules réponses Oui/Non. Le n de chaque cellule est le dénominateur clinique connu.", className="context-caption"),
        html.Div(html.Table([html.Thead(html.Tr(headers)), html.Tbody(rows)], className="data-table"), className="table-scroll"),
        html.P("Ces pourcentages sont descriptifs, non ajustés et parfois calculés sur de petits sous-ensembles renseignés. Ils ne valident pas médicalement les groupes.", className="chart-footnote"),
    ], className="chart-panel clinical-cluster-summary")


def comparison_value(df, key):
    if df is None:
        return "—"
    if key == "n":
        return number(len(df))
    if key == "age":
        return f"{number(df.age.median(), 1)} ans · n={number(df.age.notna().sum())}"
    if key == "count":
        return number(df.common_count.median(), 1)
    rate, n = prevalence(df, key)
    return f"{number(rate, 1)} % · n={number(n)}" if n else "— · n=0"


def explorer(df, ds, model, cohorts, **_):
    snapshots = {letter: model.frame.loc[model.frame.id.isin(cohorts[letter]["ids"])] if letter in cohorts else None for letter in ("a", "b")}
    a, b = snapshots["a"], snapshots["b"]
    both = a is not None and b is not None
    rows = [("Patients", "n"), ("Âge médian", "age"), ("Sensibilisation · source", "sensitization"),
            ("Détections · médiane sur le panel commun", "count"), ("Symptômes cutanés", "skin"),
            ("Traitement de l’asthme", "asthma"), ("Traitement de la rhinite", "rhinitis")]
    return [
        page_heading("lab", "À vous d’explorer",
                     "Maintenant que la méthode est posée, comparez directement deux populations de votre choix. Ce laboratoire est indépendant du parcours de présentation."),
        story_question("Quelles populations souhaitez-vous comparer ?",
                       "Partir d’un exemple, ou appliquer les filtres puis enregistrer successivement les sélections en A et en B."),
        html.Div([html.Button(label, id={"type": "cohort-preset", "key": key}, n_clicks=0, className="preset-button")
                  for key, label in [("age", "Enfants / adultes"), ("sex", "Hommes / femmes"),
                                     ("skin", "Avec / sans symptômes cutanés"), ("cluster", "Groupe 1 / groupe 2")]], className="cohort-presets"),
        html.P("Un exemple remplace A et B à partir de la cohorte entière, sans appliquer les filtres. Les âges, sexes ou statuts cliniques inconnus sont exclus des comparaisons correspondantes. "
               f"Groupes 1/2 : modèle courant K = {model.k}, standardisation {'par technologie' if model.within_chip else 'globale'}.", className="context-caption"),
        html.Div([
            html.Div([html.Span(f"COHORTE {letter.upper()}", className="eyebrow"),
                      html.H2(number(len(snapshots[letter])) if snapshots[letter] is not None else "À construire"),
                      html.P(cohorts[letter].get("description", "") if snapshots[letter] is not None else "Utilisez un exemple ou enregistrez votre sélection."),
                      html.Button(f"Enregistrer la sélection en {letter.upper()}", id=f"save-{letter}",
                                  className="primary-button" + (" secondary" if letter == "b" else ""))], className=f"cohort-card cohort-{letter}")
            for letter in ("a", "b")
        ], className="two-columns equal"),
        html.Div([html.Span(f"Sélection actuelle : {number(len(df))} patients"),
                  html.Button("Exporter la sélection CSV ↓", id="export-cohort", className="text-button"),
                  html.Button("Effacer A et B", id="clear-cohorts", className="text-button")], className="cohort-actions"),
        html.Section([
            html.Div([html.H3("En quoi les populations A et B diffèrent-elles ?"), html.P("Effectifs, âge et clinique situent la comparaison avant de regarder les IgE.")], className="panel-heading"),
            html.Div(html.Table([html.Thead(html.Tr([html.Th("Indicateur"), html.Th("Cohorte A"), html.Th("Cohorte B")])),
                                html.Tbody([html.Tr([html.Td(label), html.Td(comparison_value(a, key)), html.Td(comparison_value(b, key))]) for label, key in rows])], className="data-table"), className="table-scroll"),
            takeaway(chart_takeaway("cohort-table", df=df, ds=ds, cohort_a=a, cohort_b=b)),
            html.P("Les fréquences utilisent les statuts renseignés ; la médiane des détections utilise les panels complets. n indique le dénominateur connu.", className="chart-footnote"),
        ], className="chart-panel"),
        note("Chevauchement des populations", f"{number(len(set(a.id) & set(b.id)))} patients appartiennent aux deux cohortes. Les différences restent descriptives.") if both else
        note("Vos cohortes restent mémorisées", "Les identifiants des patients sont conservés dans ce navigateur. Changer les filtres ou le mode de lecture ne modifie pas A et B."),
        panel("Quelles détections distinguent A et B ?", "Comparer les fréquences sur le même panel pour repérer des signaux à approfondir.",
              charts.cohort_difference(a, b, ds.common_allergens), "cohort-difference",
              lecture="Écart B − A en points de pourcentage : à gauche, plus fréquent dans A ; à droite, plus fréquent dans B.",
              insight=chart_takeaway("cohort-difference", df=df, ds=ds, cohort_a=a, cohort_b=b),
              caution="Les écarts ne sont pas ajustés pour les différences d’âge, de sexe ou de technologie. Ils n’établissent pas une cause.") if both else
        html.Div([html.Span("A ↔ B"), html.H3("La comparaison commence avec deux populations."), html.P("Choisissez un exemple ou enregistrez A puis B.")], className="empty-comparison"),
        transition_question("Comment interpréter ces différences ?", "#conclusions", "Relire les conclusions et leurs limites"),
    ]


def conclusions(df, ds, model, **_):
    source = ds.frame
    q1, q3 = source.common_count.quantile([.25, .75])
    groups = [
        ("established", "Ce que nous avons établi", "✓", [
            f"Les profils IgE diffèrent d’un patient à l’autre : les 50 % centraux comptent {number(q1)} à {number(q3)} détections sur le panel commun.",
            f"Les technologies imposent un périmètre commun : {len(ds.common_allergens)} allergènes sur les {len(ds.allergens)} présents dans le fichier.",
            "Les taux de détection peuvent différer selon les manifestations cliniques renseignées ; ces comparaisons restent descriptives et non ajustées.",
            "L’analyse des 91 mesures fait apparaître des groupes exploratoires, à décrire biologiquement puis à confronter aux informations cliniques connues.",
        ]),
        ("suggested", "Ce que cela suggère", "→", [
            "Les profils IgE contiennent plus d’information qu’un seul statut sensibilisé / non sensibilisé.",
            "Considérer plusieurs mesures ensemble aide à structurer la diversité des patients.",
            "Certains profils et écarts méritent des analyses cliniques complémentaires.",
        ]),
        ("boundaries", "Ce que nous ne pouvons pas conclure", "×", [
            "Prédire directement la sévérité : Severe_Allergy est absente du CSV.",
            "Établir une causalité à partir des écarts observés.",
            "Transformer un groupe statistique en diagnostic.",
            "Généraliser ces résultats à toute la population.",
        ]),
    ]
    return [
        page_heading("06", "Qu’est-ce que cette exploration nous apprend réellement ?",
                     "Les données rendent les profils biologiques plus lisibles. Leur portée clinique reste limitée par les informations disponibles et par la méthode de comparaison."),
        html.P("Synthèse de la cohorte source complète ; les filtres Explore ne modifient pas ces constats.", className="context-caption"),
        html.Div([html.Section([html.H2(title), html.Ul([html.Li([html.Span(symbol, **{"aria-hidden": "true"}), html.Span(text)]) for text in items], className="findings-list")],
                              className=f"conclusion-level {kind}") for kind, title, symbol, items in groups], className="conclusion-levels"),
        html.Div([html.Span("LA RÉPONSE À NOTRE QUESTION", className="eyebrow"),
                  html.H2("Des centaines de mesures IgE deviennent des profils plus lisibles."),
                  html.P("Allergy Atlas est une application d’exploration de cohorte pour les allergologues impliqués dans la recherche clinique : elle aide à comparer les signatures IgE et à générer des hypothèses, sans guider la prise en charge individuelle."),
                  html.P("Ces résultats restent exploratoires : ils ne constituent ni un diagnostic ni une prédiction individuelle de sévérité.")], className="closing-statement"),
        exploration_section("Sources, limites et prolongements", [
            note("Prochaine étape clinique", "Disposer d’une cible clinique validée et documenter les biais de recrutement permettrait d’évaluer la pertinence des profils sur une cohorte indépendante."),
            html.Ul([html.Li("Source : allergenchipchallenge-data-corrected-final-hdh-sfa.csv, fourni localement."),
                     html.Li("Codages : acc-dictionnaire-final.xls et dictionnaire-acc-english.pdf. Severe_Allergy est documentée mais absente du CSV."),
                     html.Li("52 mesures négatives non documentées sont masquées ; les mesures et informations inconnues ne deviennent jamais zéro."),
                     html.Li("Le panel commun n’efface pas les différences d’unités, de calibration et de détection entre technologies."),
                     html.Li("Les données cliniques sont incomplètes ; les écarts ne sont pas ajustés pour l’âge, le sexe ni la technologie et ne prouvent aucune causalité."),
                     html.Li("Les régions et départements sont pseudonymisés ; aucune localisation réelle n’est inférée.")], className="source-list"),
        ]),
        html.Div([html.A("À vous d’explorer les cohortes →", href="#explorer", className="primary-button inline-button"),
                  html.A("Reprendre le parcours", href="#overview")], className="conclusion-actions"),
    ]


PAGES = {"overview": overview, "landscape": landscape, "sensitization": sensitization,
         "clinical": clinical, "profiles": profiles, "explorer": explorer,
         "conclusions": conclusions, "glossary": glossary}
