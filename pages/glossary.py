"""Plain-language reference for the terms actually used in Allergy Atlas."""
import unicodedata
from dash import dcc, html
from components.common import next_step


def term_groups(ds):
    """Definitions describe this dataset and the implemented analytical choices."""
    return [
        ("D’abord, trois notions à distinguer", "La mesure biologique et l’information clinique répondent à des questions différentes.", [
            ("Détection d’IgE", "Dans ce dashboard, une valeur strictement supérieure à zéro est comptée comme une détection. C’est une règle de lecture du fichier, pas un seuil diagnostique universel.", "signal positif seuil"),
            ("Sensibilisation", "Le système immunitaire reconnaît un allergène ; cela peut exister sans symptômes. Ici, l’indicateur « Sensibilisation · source » reprend la variable Sensitization fournie, sans la recalculer à partir des détections.", "sensitization sensibilise sensibilisé"),
            ("Allergie clinique", "Une réaction accompagnée de manifestations cliniques lors de l’exposition à un allergène. Une mesure d’IgE, seule, ne suffit pas à établir ce diagnostic.", "diagnostic symptome symptôme allergique"),
        ]),
        ("Comprendre les mesures et les patients", "Les mots employés dès la vue d’ensemble et dans « Les mesures ».", [
            ("IgE · immunoglobulines E", "Une famille d’anticorps impliquée dans certaines réactions allergiques. Les mesures du fichier portent sur les IgE dirigées contre différents allergènes.", "anticorps immunoglobuline"),
            ("Allergène", "Une substance reconnue par le système immunitaire, susceptible de déclencher une réaction allergique chez une personne sensibilisée. Dans le fichier, chaque colonne IgE correspond à une cible mesurée.", "molecule molécule extrait"),
            ("Puce / plateforme", "La technologie utilisée pour mesurer plusieurs IgE à la fois : ISAC V1, ISAC V2 ou ALEX. Leurs panels et leurs caractéristiques de mesure diffèrent.", "technologie multiplex ISAC ALEX"),
            ("Panel commun / couverture", f"La couverture indique quels allergènes une puce mesure. Le panel commun retient les {len(ds.common_allergens)} allergènes présents sur les trois plateformes, parmi {len(ds.allergens)} au total ; leurs unités et calibrations ne deviennent pas identiques pour autant.", "panel commun couverture comparabilite comparabilité"),
            ("Cohorte / sélection active", "Une cohorte est un ensemble de patients étudiés. Ici, les filtres définissent la sélection active ; les cohortes A et B sont des instantanés enregistrés pour comparer deux populations.", "population filtre echantillon échantillon"),
            ("Donnée manquante / cas complet", "Une valeur absente peut être non mesurée, non renseignée ou invalidée : elle ne vaut pas zéro. Pour les profils, un cas complet possède toutes les mesures valides du panel commun ; sinon, il reste « Non attribué ».", "inconnu absent non attribue non attribué imputation"),
            ("Manifestation clinique / traitement", "Les symptômes cutanés et les traitements renseignés décrivent la clinique disponible. Un traitement déclaré de l’asthme, de la rhinite ou de la dermatite ne mesure directement ni les symptômes actuels ni leur sévérité.", "peau asthme rhinite dermatite symptomes symptômes severe severe_allergy"),
        ]),
        ("Lire les graphiques et les écarts", "Quelques repères pour comprendre les pourcentages, les couleurs et les comparaisons.", [
            ("Prévalence / fréquence de détection", "Ici : la part des patients ayant une valeur > 0 pour un allergène, parmi ceux dont la mesure est disponible. Exemple fictif : 20 détections sur 80 mesures renseignées = 25 %.", "pourcentage proportion taux"),
            ("Effectif n / dénominateur observé", "n est le nombre d’observations utilisées. Le dénominateur d’un pourcentage comprend uniquement les patients renseignés pour la mesure ou le statut concerné ; il peut changer d’un indicateur à l’autre.", "nombre patients renseignes renseignés"),
            ("Médiane / quartiles Q1–Q3", "La médiane partage les valeurs ordonnées en deux moitiés. Q1 et Q3 délimitent les 50 % centraux : leur écart décrit la dispersion, sans être un intervalle de confiance.", "distribution interquartile IQR dispersion"),
            ("Points de pourcentage", "Une différence absolue entre deux pourcentages. Exemple fictif : passer de 20 % à 30 % représente +10 points, soit une hausse relative de 50 %.", "ecart écart difference différence delta points"),
            ("IC à 95 % · intervalle de confiance", "Un intervalle qui décrit l’incertitude statistique d’une estimation selon la méthode utilisée. Ici, il est exploratoire : il ne corrige pas les biais de sélection et ne représente pas la dispersion de 95 % des patients.", "incertitude IC95 bootstrap Wilson"),
            ("Heatmap · carte de chaleur", "Un tableau où la couleur code une valeur. La légende indique s’il s’agit d’une mesure transformée, d’un score standardisé ou d’une couverture ; une case vide ne veut pas dire zéro.", "matrice chaleur couleur signature"),
            ("Sankey · diagramme de flux", "La largeur des liens représente le nombre de patients partageant plusieurs caractéristiques. Ici, les liens décrivent des cooccurrences, pas une succession d’événements dans le temps.", "flux cooccurrence parcours"),
            ("Association / causalité", "Une association est une différence ou un lien observé entre variables. Elle ne prouve pas que l’une cause l’autre : l’âge, la technologie ou le recrutement peuvent aussi intervenir.", "correlation corrélation confusion biais"),
        ]),
        ("Comprendre les profils statistiques", "Les méthodes de la vue « Les profils », expliquées sans formule compliquée.", [
            ("Signature IgE / profil / cluster", "La signature est l’ensemble des mesures IgE d’un patient. Un profil, ou cluster, regroupe des signatures proches ; son numéro ne correspond ni à un diagnostic ni à un niveau de gravité.", "groupe regroupement empreinte"),
            ("log1p · transformation logarithmique", "On remplace une mesure x par log(1 + x) pour réduire le poids des très grandes valeurs tout en conservant les zéros. Cette transformation ne change pas la règle de détection > 0.", "logarithme log transformation"),
            ("Standardisation / score z", "Après log1p, chaque allergène est centré sur sa moyenne et rapporté à son écart-type. Par défaut, cela se fait séparément par puce ; un score positif signifie « au-dessus de cette moyenne », sans être un seuil clinique.", "centre centré reduit réduit z-score harmonisation normalisation"),
            ("KMeans / K", f"Une méthode qui répartit les patients en K groupes de signatures proches, à partir des {len(ds.common_allergens)} mesures communes transformées et standardisées. Les variables cliniques ne construisent pas les groupes ; elles servent ensuite à les décrire.", "k-means clustering non supervise non supervisé"),
            ("PCA / ACP · analyse en composantes principales", "Une projection des nombreuses mesures sur deux axes, PC1 et PC2, pour situer les patients sur un plan. Les groupes sont calculés dans toutes les dimensions, pas seulement sur ce dessin.", "projection dimension reduction réduction PC1 PC2"),
            ("Variance expliquée", "La part des différences entre patients résumée par les axes affichés, après transformation et standardisation. Le reste de l’information n’apparaît pas sur le plan ; ce pourcentage n’est pas une précision de prédiction.", "variance information axes"),
            ("Score de silhouette", "Un score de −1 à 1 qui compare la proximité d’un patient avec son groupe et avec le groupe voisin. Une valeur élevée suggère des groupes mieux séparés ; ici, ce score aide à choisir K, sans valider leur sens clinique.", "silhouette separation séparation"),
            ("V de Cramér", "Une mesure de l’association entre deux catégories, de 0 à 1. Ici, elle compare la puce au profil : une valeur proche de zéro indique une faible association globale, sans exclure tout effet de plateforme.", "cramer cramers cramer's technologie dependance dépendance"),
        ]),
    ]


def normalize(text):
    return "".join(c for c in unicodedata.normalize("NFKD", text.casefold()) if not unicodedata.combining(c))


def render_terms(query, ds):
    words = normalize(query or "").split()
    sections, count = [], 0
    for index, (title, intro, terms) in enumerate(term_groups(ds)):
        matches = [(name, definition) for name, definition, aliases in terms
                   if all(word in normalize(f"{name} {definition} {aliases}") for word in words)]
        if not matches:
            continue
        count += len(matches)
        sections.append(html.Section([
            html.Div([html.Span(f"{index+1:02d}", className="glossary-index"),
                      html.Div([html.H2(title), html.P(intro)])], className="glossary-section-heading"),
            html.Dl([html.Div([html.Dt(name), html.Dd(definition)], className="glossary-entry")
                     for name, definition in matches], className="glossary-terms essential-terms" if index == 0 else "glossary-terms"),
        ], className="glossary-section"))
    if not sections:
        sections = [html.Div([html.H2("Aucun terme trouvé"),
                              html.P("Essayez un sigle comme « PCA », un mot comme « médiane », ou effacez la recherche.")], className="glossary-empty")]
    return sections, f"{count} notion{'s' if count != 1 else ''}" + (" trouvée" + ("s" if count != 1 else "") if words else " à explorer")


def glossary(ds, **_):
    sections, count = render_terms("", ds)
    return [
        html.Div([
            html.Div([html.Span("REPÈRES & VOCABULAIRE"), html.Span("POUR LA PRÉSENTATION ET L’EXPLORATION", className="eyebrow-source")], className="eyebrow"),
            html.H1("Les mots pour lire les données."),
            html.P("Des définitions courtes pour suivre le fil conducteur : des mesures IgE aux profils, puis à leurs liens avec la clinique.", className="page-description"),
            html.A("Commencer l’exploration →", href="#overview", className="vocabulary-link"),
        ], className="page-heading"),
        html.Div([
            html.Div([html.Label("Retrouver un terme", htmlFor="glossary-search"),
                      dcc.Input(id="glossary-search", type="search", value="", placeholder="IgE, médiane, PCA…", debounce=0.2,
                                persistence=True, persistence_type="session", className="glossary-search")], className="glossary-search-field"),
            html.Span(count, id="glossary-count", role="status", **{"aria-live": "polite"}),
        ], className="glossary-searchbar"),
        html.P("Ces repères restent les mêmes quelle que soit la population sélectionnée. Les exemples chiffrés sont fictifs et servent uniquement à expliquer les calculs.", className="context-caption glossary-scope"),
        html.Div(sections, id="glossary-results"),
        html.Div([html.Span("POUR ALLER PLUS LOIN", className="eyebrow"),
                  html.P(["Définitions adaptées au dictionnaire ACC et aux méthodes de ce dashboard. Pour les notions biologiques : ",
                          html.A("dossier « Allergies » de l’Inserm ↗", href="https://www.inserm.fr/dossier/allergies/", target="_blank", rel="noopener noreferrer"), ". ",
                          html.A("Voir les limites et les sources du projet →", href="#conclusions")])], className="glossary-source"),
        next_step("#overview", "01 — Poser la problématique"),
    ]
