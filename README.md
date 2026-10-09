# Allergy Atlas

**Explorer les profils IgE et leurs associations cliniques dans l'Allergen Chip Challenge (ACC)**  
Projet de Data Visualisation — Master 2 IA/Data — Dash / Plotly

**Public cible :** allergologues impliqués dans la recherche clinique et chercheurs en allergologie.  
**Usage :** exploration descriptive d'une population de patients et génération d'hypothèses ; ni diagnostic ni décision médicale individuelle.

## Problématique

**Comment les profils de sensibilisation IgE se structurent-ils dans ACC, et quels liens présentent-ils avec les manifestations cliniques disponibles ?**

L'application répond à la question en deux étapes, accessibles dans deux onglets. Chaque onglet est conçu pour tenir sur un écran d'ordinateur sans défilement principal (cible : 1366 × 768 ou supérieur, navigateur à 100 %). Sur mobile, le défilement est autorisé pour la lisibilité.

## Les deux onglets

| Onglet | Question | Fonctionnalités |
| --- | --- | --- |
| **01 — Identifier les profils IgE** | Quels profils biologiques peut-on observer ? | Distribution du nombre de détections, classement des allergènes, projection PCA et caractérisation biologique des groupes exploratoires |
| **02 — Explorer les liens cliniques** | Ces profils sont-ils associés à certaines manifestations cliniques ? | Écart de détection Oui/Non selon l'information clinique choisie, fréquence de la caractéristique clinique par groupe, comparaison enfants/adultes, synthèse et limites |

La problématique reste affichée dans l'en-tête. Les deux onglets correspondent à ses deux sous-questions. Les groupes sont créés à partir des données biologiques **sans utiliser les variables cliniques** ; celles-ci servent seulement à caractériser les groupes a posteriori.

## Filtres et lecture

Un bandeau commun permet de choisir :

- **Population :** tous, moins de 18 ans ou 18 ans et plus ;
- **Technologie :** toutes, ISAC V1, ISAC V2 ou ALEX ;
- **Information clinique :** symptômes cutanés, traitements de l'asthme, de la rhinite ou de la dermatite ;
- **Groupe clinique :** tous, Oui ou Non.

Les résultats se recalculent selon la sélection ; l'effectif actif et le nombre d'observations cliniques exploitables sont indiqués. **Pour comparer Oui et Non**, conserver le filtre « Groupe clinique » sur « Tous » : choisir uniquement Oui ou Non retire l'autre groupe de comparaison. Les filtres n'entraînent pas de nouvel apprentissage de KMeans. Les détails des barres sont disponibles au survol.

Les quatre indicateurs affichés sont : patients sélectionnés, nombre médian de détections sur le panel commun, profils exploitables et données cliniques renseignées (Oui/Non). Les pourcentages cliniques utilisent exclusivement les statuts connus, avec effectifs visibles au survol.

## Données et règles scientifiques

Le CSV ACC contient **4 271 patients**, **256 colonnes**, dont **241 mesures IgE**. Les patients ont été analysés avec trois technologies (ISAC V1, ISAC V2, ALEX) dont la couverture en allergènes diffère. Les comparaisons transversales reposent donc sur les **91 allergènes communs** ; **4 241 patients** ont un profil complet sur ce panel.

- La règle `IgE > 0` est un **seuil descriptif de détection dans l'application**, et non un diagnostic clinique de sensibilisation ou d'allergie.
- Les valeurs biologiques non mesurées et les codes cliniques inconnus ne sont **pas assimilés à zéro ou à Non**.
- Les profils exploratoires reposent sur les 91 mesures communes, transformées par `log1p`, standardisées selon les paramètres du modèle, puis utilisées par KMeans. La PCA fournit une représentation en deux dimensions ; elle **ne sert pas** à créer les groupes.
- Les associations constatées sont **descriptives et non ajustées** : elles ne démontrent ni causalité ni facteur de risque indépendant.
- La variable clinique `Severe_Allergy` n'est pas disponible dans le CSV exploité : l'application **ne prédit pas la sévérité**.
- La population ACC est spécifique et **non représentative de la population française** ; les fréquences affichées ne sont pas des estimations nationales de prévalence.

## Installation et lancement

**Pré-requis :** Python 3.13 conseillé, accès local au répertoire du projet. Aucune base de données ni clé API n'est requise.

### Windows — PowerShell

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe app.py
```

### macOS et Linux

```bash
python3.13 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python app.py
```

Ouvrir **http://127.0.0.1:8050**. Au premier lancement, les profils PCA/KMeans sont préparés en mémoire : patienter jusqu'à l'apparition de l'adresse locale dans le terminal. Pour arrêter : `Ctrl+C`.

Changer de port, si nécessaire :

```powershell
$env:PORT = '8051'
.\.venv\Scripts\python.exe app.py
```

## Architecture

```text
app.py                  Application compacte : interface, graphiques, filtres et callbacks
requirements.txt        Dépendances Python
assets/                 Mise en forme CSS et ressources de l'interface
src/data_loader.py      Chargement et validation du CSV
src/preprocessing.py    Préparation des mesures, catégories et manquants
src/metrics.py          Cohortes filtrées et indicateurs
src/charts.py           Figures Plotly réutilisées
src/clustering.py       Construction du modèle PCA / KMeans
src/insights.py         Résultats descriptifs et textes calculés
data/                   CSV et dictionnaires ACC
tests/                  Tests de structure, métriques, analyses et application historique
README.md               Documentation du projet
```

Le projet conserve des fichiers de référence de l'application à chapitres (`app_historique.py`, `pages/`, `components/` et certains callbacks). **Le point d'entrée à utiliser est `app.py`** ; ces modules secondaires ne sont pas nécessaires au parcours compact, sauf lorsqu'ils sont importés explicitement.

## Tests et dépannage

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

Les tests existants couvrent principalement les traitements et certains composants de l'application à chapitres. La cohérence fonctionnelle de la version compacte doit aussi être vérifiée manuellement : changer chaque filtre, vérifier les dénominateurs, tester les sélections vides, basculer entre onglets et contrôler l'absence de scroll sur la résolution utilisée pour la soutenance.

- **`ModuleNotFoundError` :** installer les dépendances avec le même interpréteur Python que celui utilisé pour lancer `app.py`.
- **Port 8050 occupé :** arrêter le serveur précédent ou définir `PORT`.
- **CSV introuvable :** vérifier les données du dossier `data/` ; ne pas renommer les fichiers attendus par le chargeur.
- **Changements invisibles :** arrêter le serveur, relancer puis rafraîchir le navigateur.

## Démonstration orale — 10 minutes

Présenter la problématique, expliquer pourquoi les mesures des trois puces doivent être comparées sur un panel commun, puis montrer l'onglet 1 (diversité des détections, signaux dominants et groupes biologiques). Passer ensuite à l'onglet 2 pour examiner les différences selon une caractéristique clinique, rappeler les effectifs connus et conclure sur les limites. L'objectif est d'expliquer **ce que les données permettent d'observer**, pas de démontrer une prédiction clinique de sévérité.

**Sources :** Société Française d'Allergologie / Health Data Hub — Allergen Chip Challenge (ACC). Les dictionnaires et le fichier CSV accompagnent le projet.
