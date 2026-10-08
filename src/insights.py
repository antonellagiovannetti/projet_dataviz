"""Short, evidence-bound reading notes for the currently displayed population.

Descriptive captions share the charts' valid-measurement denominators. They do
not infer diagnoses, significance, causality or trends from an empty selection.
"""
import numpy as np
import pandas as pd
from .metrics import allergen_statistics, cohort_difference
from .preprocessing import clinical_quality

EMPTY = "Aucun patient sélectionné : aucune observation ne peut être formulée pour cette vue."


def _n(value, digits=0):
    return f"{value:,.{digits}f}".replace(",", "\u202f").replace(".", ",")


def _name(value):
    return str(value).replace("_", " ")


def clinical_example(df, allergens, outcome="skin"):
    """Describe Ara h 2 in the selected cohort, using valid IgE denominators.

    Clinical group sizes include all patients with the corresponding status;
    rate denominators include only measured Ara h 2 values within those groups.
    The input is the prepared frame, where invalid negative values are missing.
    An unavailable comparison keeps its counts but has no rates or conclusion.
    """
    result = dict(available=False, reason="", allergen="Ara_h_2",
                  yes_count=0, no_count=0, unknown_count=0,
                  yes_n=0, no_n=0, yes_rate=None, no_rate=None,
                  difference=None, conclusion="")
    if df is None or df.empty:
        result["reason"] = "Aucun patient sélectionné : cet exemple ne peut pas être comparé."
        return result
    if outcome not in df:
        result["unknown_count"] = len(df)
        result["reason"] = "Cette information clinique n’est pas disponible dans la sélection."
        return result

    yes = df.loc[df[outcome].eq("Oui")]
    no = df.loc[df[outcome].eq("Non")]
    result.update(yes_count=len(yes), no_count=len(no),
                  unknown_count=len(df) - len(yes) - len(no))
    if "Ara_h_2" not in allergens or "Ara_h_2" not in df:
        result["reason"] = "Ara h 2 n’est pas disponible sur le panel sélectionné."
        return result

    result.update(yes_n=int(yes["Ara_h_2"].notna().sum()),
                  no_n=int(no["Ara_h_2"].notna().sum()))
    if yes.empty or no.empty:
        result["reason"] = "Deux groupes cliniques Oui et Non non vides sont nécessaires pour comparer Ara h 2."
        return result
    if not result["yes_n"] or not result["no_n"]:
        result["reason"] = "Chaque groupe doit avoir au moins une mesure valide d’Ara h 2 pour être comparé."
        return result

    comparison = cohort_difference(yes, no, ["Ara_h_2"]).iloc[0]
    delta = float(comparison.difference)
    result.update(available=True, yes_rate=float(comparison.prevalence_a),
                  no_rate=float(comparison.prevalence_b), difference=delta)
    manifestations = {
        "skin": ("avec symptômes cutanés", "sans symptômes cutanés"),
        "asthma": ("avec un traitement de l’asthme", "sans traitement de l’asthme"),
        "rhinitis": ("avec un traitement de la rhinite", "sans traitement de la rhinite"),
        "dermatitis": ("avec un traitement de la dermatite", "sans traitement de la dermatite"),
    }
    labels = manifestations.get(outcome, ("du groupe Oui", "du groupe Non"))
    if np.isclose(delta, 0):
        result["conclusion"] = "Ara h 2 est détecté aussi souvent dans les deux groupes renseignés."
    else:
        higher = labels[0] if delta > 0 else labels[1]
        result["conclusion"] = (f"Ara h 2 est plus souvent détecté chez les patients {higher}, "
                                "parmi les mesures renseignées. Ce lien ne démontre pas une cause.")
    return result


def _difference_note(a, b, allergens, labels, *, invert=False):
    if a is None or b is None or a.empty or b.empty:
        return "Deux groupes renseignés et non vides sont nécessaires pour observer une différence de signature."
    differences = cohort_difference(a, b, allergens).dropna(subset=["difference"])
    if differences.empty:
        return "Aucune mesure valide commune aux deux groupes : les signatures ne peuvent pas être comparées."
    # Preserve the same source-column tie order as the plotted ranking.
    differences = differences.set_index("allergen").reindex(allergens).reset_index().dropna(subset=["difference"])
    row = differences.loc[differences.absolute_difference.idxmax()]
    delta = float(row.difference) * (-1 if invert else 1)
    if np.isclose(delta, 0):
        return "Les fréquences de détection sont identiques dans les deux groupes pour les allergènes comparables."
    higher = labels[0] if float(row.difference) > 0 else labels[1]
    return (f"{_name(row.allergen)} présente l’un des plus grands écarts : "
            f"{_n(abs(delta), 1)} points de plus {higher}. Cet écart est descriptif, sans preuve de causalité.")


def chart_takeaway(graph_id, *, df=None, ds=None, model=None, controls=None,
                   reference_frame=None, selected_cluster=None, cohort_a=None, cohort_b=None):
    controls = controls or {}
    if graph_id == "coverage-chart":
        return (f"Seuls {len(ds.common_allergens)} des {len(ds.allergens)} allergènes sont communs aux trois puces : "
                "ce périmètre permet de comparer les profils sans confondre détections et couverture.")
    if graph_id == "model-scores":
        score = model.scores.loc[model.scores.k.eq(model.best_k), "silhouette"].iloc[0]
        return (f"Sur la cohorte source, K = {model.best_k} maximise la silhouette ({_n(score, 3)}). "
                "C’est un repère statistique pour choisir les profils, pas une validation clinique.")
    if graph_id in ("cohort-difference", "cohort-table"):
        if cohort_a is None or cohort_b is None:
            return "Enregistrez deux cohortes pour observer leurs différences de composition et de signature IgE."
        if graph_id == "cohort-difference":
            return _difference_note(cohort_a, cohort_b, ds.common_allergens,
                                    ("dans A", "dans B"), invert=True)
        if cohort_a.empty or cohort_b.empty:
            return "Une cohorte est vide : aucune comparaison entre A et B ne peut être interprétée."
        med_a, med_b = cohort_a.common_count.median(), cohort_b.common_count.median()
        if pd.isna(med_a) or pd.isna(med_b):
            return "Les effectifs et la clinique restent comparables ; les médianes IgE nécessitent des profils complets dans chaque cohorte."
        if np.isclose(med_a, med_b):
            return (f"A et B ont la même médiane de {_n(med_a, 1)} IgE détectées. "
                    "Un même nombre de signaux peut néanmoins recouvrir des allergènes différents.")
        return (f"La médiane est de {_n(med_a, 1)} détections dans A et {_n(med_b, 1)} dans B. "
                "Cela décrit une différence de nombre de signaux, pas de sévérité.")
    if df is None or df.empty:
        return EMPTY
    if graph_id in ("overview-hist", "sensitivity-hist"):
        values = df.common_count.dropna()
        if values.empty:
            return "Aucun panel commun complet : le nombre total de détections ne peut pas être comparé ici."
        if values.nunique() == 1:
            return f"Les {_n(len(values))} patients analysables ont chacun {_n(values.iloc[0])} détections ; leurs allergènes peuvent toutefois différer."
        q1, q3 = values.quantile([.25, .75])
        return (f"Médiane : {_n(values.median(), 1)} détections ; quartiles : {_n(q1, 1)}–{_n(q3, 1)}. "
                "Cette dispersion décrit la diversité des profils sur le même panel d’allergènes.")
    if graph_id == "overview-chips":
        chips = df.chip.value_counts()
        if len(chips) == 1:
            return f"Tous les patients retenus ont été mesurés avec {chips.index[0]} ; aucune comparaison entre technologies n’est possible dans cette sélection."
        return (f"{chips.index[0]} représente {_n(100*chips.iloc[0]/len(df), 1)} % des patients retenus. "
                "Tenir compte de cette composition aide à interpréter les signatures observées.")
    if graph_id == "missing-chart":
        quality = clinical_quality(df)
        row = quality.sort_values("missing_pct", ascending=False).iloc[0]
        if row.missing == 0:
            return "Les informations affichées sont toutes renseignées dans cette sélection ; leur complétude ne garantit toutefois pas l’absence d’autres biais."
        return (f"{row.label} est non renseigné pour {_n(row.missing_pct, 1)} % de la sélection. "
                "Les liens cliniques doivent être lus sur les seuls patients renseignés.")
    if graph_id == "top-allergens":
        metric = controls.get("metric", "prevalence")
        stats = allergen_statistics(df, ds.common_allergens).dropna(subset=[metric])
        if stats.empty:
            return "Aucune mesure IgE valide : aucun allergène ne peut être classé dans cette sélection."
        if metric != "prevalence" and df.chip.nunique() > 1:
            return "Ce classement montre les intensités brutes ; choisir une seule puce permet de les lire sans mélanger des unités non harmonisées."
        stats = stats.set_index("allergen").reindex(ds.common_allergens).reset_index()
        row = stats.nlargest(1, metric).iloc[0]
        if row[metric] == 0:
            if metric == "median":
                return "Les médianes sont toutes nulles : elles ne distinguent pas les allergènes, même si certains patients présentent des détections."
            return "Aucune IgE positive n’est observée sur le panel commun ; ce classement ne distingue donc pas de signal dominant."
        if metric == "prevalence":
            return (f"{_name(row.allergen)} figure en tête : {_n(row.prevalence, 1)} % des {_n(row.measured)} mesures valides sont positives. "
                    "Cela indique une détection fréquente, pas une allergie clinique.")
        label = "moyenne" if metric == "mean" else "médiane"
        return (f"{_name(row.allergen)} figure en tête pour l’IgE {label} ({_n(row[metric], 2)}, unité source). "
                "L’intensité du signal ne mesure pas la sévérité clinique.")
    if graph_id == "age-chart":
        bounds = [(0, 17), (18, 50), (51, 120)] if controls.get("age_mode") == "broad" else [(0, 5), (6, 12), (13, 17), (18, 30), (31, 50), (51, 120)]
        medians = [df.loc[df.age.between(lo, hi), "common_count"].median() for lo, hi in bounds]
        medians = [v for v in medians if pd.notna(v)]
        if len(medians) < 2:
            return "Moins de deux classes d’âge disposent de profils complets : aucune comparaison entre âges n’est possible pour le nombre de détections."
        if np.isclose(min(medians), max(medians)):
            return (f"Les classes analysables ont la même médiane de {_n(medians[0], 1)} détections. "
                    "Cela ne signifie pas que leurs signatures IgE sont identiques.")
        return (f"Selon la classe d’âge, la médiane varie de {_n(min(medians), 1)} à {_n(max(medians), 1)} détections. "
                "Cette comparaison entre patients ne décrit pas une évolution individuelle.")
    if graph_id == "patient-heatmap":
        return "Cette vue permet de repérer les signaux qui coexistent chez un patient et de comparer leur répartition entre patients, au-delà d’un simple nombre de détections."
    if graph_id == "clinical-difference":
        variable = controls.get("outcome", "skin")
        return _difference_note(df.loc[df[variable].eq("Oui")], df.loc[df[variable].eq("Non")],
                                ds.common_allergens, ("dans le groupe Oui", "dans le groupe Non"))
    if graph_id == "clinical-composition":
        variable = controls.get("outcome", "skin")
        known = df[variable].isin(["Oui", "Non"])
        if not known.any():
            return "Aucun statut clinique n’est renseigné : les barres montrent l’absence d’information, pas l’absence de manifestations."
        return (f"{_n(100*(~known).mean(), 1)} % des statuts sont non renseignés. "
                "Comparer les parts Oui et Non exige donc aussi de regarder la part inconnue dans chaque groupe.")
    if graph_id == "clinical-flow":
        columns = ["age_group", "sensitization", "skin", "asthma"]
        complete = df[columns].notna().all(axis=1) & ~df[columns].eq("Inconnu").any(axis=1)
        n = int(complete.sum())
        if not n:
            return "Aucun patient ne renseigne les quatre dimensions : aucune combinaison de caractéristiques ne peut être observée ici."
        description = "patient complètement renseigné" if n == 1 else "patients complètement renseignés"
        return (f"Les liens résument les caractéristiques conjointes de {_n(n)} {description}. "
                "Ils montrent des cooccurrences, pas un parcours temporel ou une causalité.")
    if graph_id in ("pca-chart", "cluster-fingerprints", "cluster-platform"):
        projected = df.dropna(subset=["pc1", "pc2"])
        if projected.empty:
            return "Aucun patient de cette sélection ne dispose d’un profil IgE complet : aucune structure de groupes ne peut être décrite."
        n_clusters = projected.cluster.nunique()
        if graph_id == "pca-chart":
            return (f"{_n(len(projected))} patients projetés ; les deux axes résument {_n(100*sum(model.explained_variance[:2]), 1)} % de la variance du modèle. "
                    "La proximité visuelle ne résume donc qu’une partie des différences IgE.")
        if graph_id == "cluster-fingerprints":
            if n_clusters == 1:
                return "Un seul profil est affiché : ses couleurs décrivent les signaux caractéristiques, mais ne permettent pas de comparer plusieurs profils dans cette sélection."
            return "Les contrastes entre lignes indiquent les allergènes qui différencient les profils ; ils rendent les groupes biologiquement descriptibles, sans en faire des diagnostics."
        if projected.chip.nunique() == 1:
            return "Une seule puce est représentée dans cette sélection : ce graphique ne permet pas d’évaluer l’effet de technologie entre les profils."
        if n_clusters == 1:
            return "La sélection ne montre qu’un profil : on peut lire sa composition par puce, mais pas la comparer à celle des autres profils."
        return "Comparer la composition par puce permet de vérifier si les groupes reflètent surtout une différence de technologie plutôt qu’une structure biologique."
    if graph_id == "cluster-excess":
        reference = reference_frame.loc[reference_frame.cluster.ne("Non attribué")]
        selected = df.loc[df.cluster.eq(str(selected_cluster))]
        return _difference_note(selected, reference, ds.common_allergens,
                                (f"dans le profil {selected_cluster} retenu", "dans la référence"))
    if graph_id == "profile-summary":
        known = df.skin.isin(["Oui", "Non"])
        if not known.any():
            return "Les IgE décrivent ce groupe, mais les symptômes cutanés ne sont pas renseignés : aucun lien avec cette manifestation ne peut être décrit."
        rate = 100*df.loc[known, "skin"].eq("Oui").mean()
        return (f"Symptômes cutanés : {_n(rate, 1)} % parmi {_n(known.sum())} patients renseignés. "
                "La clinique décrit ainsi le profil, sans avoir servi à le construire.")
    raise ValueError(f"Graphique sans texte de lecture : {graph_id}")
