# Allergy Atlas

**Explorer les profils IgE de l’Allergen Chip Challenge (ACC)**  
Projet de Data Visualisation — Master 2 IA / Data · Application interactive Python / Dash / Plotly

> **Public cible :** allergologues impliqués dans la recherche clinique et chercheurs en allergologie.  
> **Usage :** exploration d’une population de patients, comparaison de sous-populations et formulation d’hypothèses. L’application n’est pas un dispositif de diagnostic, de prédiction de la sévérité ou de décision médicale individuelle.

## Sommaire

- [Allergy Atlas](#allergy-atlas)
  - [Sommaire](#sommaire)
  - [Objectif et question de recherche](#objectif-et-question-de-recherche)
  - [Données utilisées](#données-utilisées)
  - [Organisation de l’interface](#organisation-de-linterface)
    - [Onglet 1 — Comprendre la cohorte](#onglet-1--comprendre-la-cohorte)
    - [Onglet 2 — Explorer les profils](#onglet-2--explorer-les-profils)
  - [Filtres et interactions](#filtres-et-interactions)
  - [Indicateurs et interprétation](#indicateurs-et-interprétation)
  - [Installation et lancement](#installation-et-lancement)
    - [Prérequis](#prérequis)
    - [Windows — PowerShell](#windows--powershell)
    - [macOS / Linux](#macos--linux)
    - [Changer de port](#changer-de-port)
  - [Architecture du projet](#architecture-du-projet)
  - [Technologies utilisées](#technologies-utilisées)
  - [Méthodes et limites](#méthodes-et-limites)
    - [Comparabilité biologique](#comparabilité-biologique)
    - [Détection IgE et données manquantes](#détection-ige-et-données-manquantes)
    - [Regroupement exploratoire](#regroupement-exploratoire)
    - [Portée clinique et statistique](#portée-clinique-et-statistique)
  - [Tests et résolution des problèmes](#tests-et-résolution-des-problèmes)
    - [Exécuter les tests](#exécuter-les-tests)
    - [Problèmes courants](#problèmes-courants)

## Objectif et question de recherche

**Question principale :** *Comment les profils de sensibilisation IgE se structurent-ils dans ACC, et quelles associations présentent-ils avec les informations cliniques disponibles ?*

Allergy Atlas est une application d’**exploration de population clinique**. Elle aide un professionnel de l’allergologie à :

1. décrire la diversité des détections IgE dans la population étudiée ;
2. identifier les allergènes fréquemment détectés sur un panel comparable ;
3. comparer les profils biologiques selon des informations cliniques disponibles ;
4. examiner des groupes de patients aux profils IgE proches ;
5. repérer des observations à approfondir dans de futures recherches.

Le tableau de bord suit une progression simple : **décrire la diversité → étudier les associations cliniques → explorer les profils multidimensionnels → interpréter avec prudence**. Les résultats sont descriptifs et exploratoires : une association observée ne démontre pas une causalité.

## Données utilisées

Le jeu de données provient de l’**Allergen Chip Challenge**, porté par la **Société Française d’Allergologie (SFA)** et le **Health Data Hub**, et diffusé sur [data.gouv.fr](https://www.data.gouv.fr/datasets/allergen-chip-challenge).

| Caractéristique | Description |
|---|---|
| Population | **4 271 patients**, une ligne par patient |
| Variables | **256 colonnes** : 15 variables démographiques, techniques et cliniques ; 241 mesures d’IgE spécifiques |
| Technologies | ISAC v1, ISAC v2 et ALEX² |
| Panel d’analyse commun | **91 allergènes mesurés par les trois technologies** |
| Profils complets sur le panel commun | **4 241 patients** |
| Format source | CSV local, séparateur `;`, décimales avec virgule |

Les données biologiques correspondent à des mesures d’IgE dirigées contre des allergènes. Les informations démographiques et cliniques disponibles permettent certaines descriptions et comparaisons, mais sont incomplètes. La population ACC, recrutée dans des structures spécialisées, **n’est pas représentative de la population française**.

Fichiers fournis dans le projet :

- `data/raw/allergenchipchallenge-data-corrected-final-hdh-sfa.csv` : données principales utilisées par l’application ;
- `data/dictionaries/acc-dictionnaire-final.xls` : dictionnaire et codages des variables ;
- `data/dictionaries/dictionnaire-acc-english.pdf` : documentation des variables (certaines variables documentées ne sont pas disponibles dans le CSV).

Le CSV source est lu localement ; les transformations et calculs se font en Python, sans modifier le fichier d’origine. **Aucune base de données, clé API ou connexion à un service externe n’est requise** pour utiliser l’application.

## Organisation de l’interface

L’application comporte **deux onglets**. Son interface de bureau est organisée autour d’un bandeau de filtres, de quatre indicateurs synthétiques et de quatre panneaux par onglet. Elle est conçue pour limiter le défilement vertical à partir d’une résolution d’environ **1366 × 768** avec un zoom navigateur à 100 %. Sur les écrans plus étroits, le défilement est autorisé pour conserver des graphiques lisibles.

### Onglet 1 — Comprendre la cohorte

Ce premier écran donne une lecture guidée des données :

| Zone | Question traitée | Contenu |
|---|---|---|
| **1. Combien de signaux IgE ?** | La diversité des détections est-elle importante entre patients ? | Distribution du nombre de mesures IgE détectées sur les 91 allergènes communs |
| **2. Quels allergènes dominent ?** | Quels allergènes sont les plus fréquemment détectés ? | Classement des huit allergènes les plus détectés dans la sélection |
| **3. Quel lien avec la clinique ?** | Les taux de détection diffèrent-ils entre les groupes cliniques « Oui » et « Non » ? | Écarts descriptifs de détection selon l’information clinique sélectionnée |
| **Ce que nous pouvons conclure** | Que montrent les résultats, et que ne permettent-ils pas d’affirmer ? | Synthèse contextuelle, exemple sur Ara h 2 lorsqu’il est calculable, effectifs renseignés et précautions |

**Logique de lecture :** constater la diversité des signaux, reconnaître les allergènes dominants, rechercher d’éventuelles différences cliniques, puis qualifier la portée de l’observation.

### Onglet 2 — Explorer les profils

Ce second écran examine simultanément les mesures biologiques et les regroupements exploratoires :

| Zone | Question traitée | Contenu |
|---|---|---|
| **1. Les patients se ressemblent-ils ?** | Observe-t-on des patients aux profils biologiques proches ? | Projection PCA en deux dimensions, à partir des profils calculés |
| **2. Quels allergènes distinguent les groupes ?** | Quelles détections caractérisent les groupes exploratoires ? | Écarts de détection pour un groupe par rapport à la population affichée |
| **3. Comparer deux populations** | Les profils diffèrent-ils entre enfants et adultes ? | Comparaison descriptive des taux de détection entre ces deux sous-populations lorsqu’elles sont présentes |
| **Interpréter les groupes** | Comment se répartissent les informations cliniques dans les groupes ? | Effectifs par groupe et proportion de réponses cliniques « Oui » parmi les statuts connus |

Le **clustering n’est pas un outil de diagnostic**. Il sert à structurer la diversité des mesures et à suggérer des questions de recherche. La PCA est une projection visuelle ; les groupes ont été calculés à partir des 91 mesures, et non à partir des deux axes affichés.

## Filtres et interactions

Les quatre filtres situés en haut de l’application s’appliquent aux deux onglets :

| Filtre | Choix proposés | Effet |
|---|---|---|
| **Population** | Tous les patients ; moins de 18 ans ; 18 ans et plus | Limite la population par âge |
| **Technologie** | Toutes les puces ; ISAC V1 ; ISAC V2 ; ALEX | Limite l’analyse à une technologie |
| **Information clinique** | Symptômes cutanés ; traitement de l’asthme ; traitement de la rhinite ; traitement de la dermatite | Choisit l’information clinique étudiée |
| **Groupe clinique** | Tous, y compris inconnus ; Oui ; Non | Restreint les patients selon la valeur de l’information clinique sélectionnée |

Les graphiques, effectifs et commentaires sont mis à jour avec les filtres. Les graphiques Plotly permettent notamment la consultation des informations au survol et les interactions natives proposées par chaque graphique.

**Attention aux comparaisons cliniques :** choisir uniquement « Oui » ou « Non » peut retirer le groupe de comparaison nécessaire. Pour étudier l’écart entre **Oui et Non**, conserver **« Tous (dont inconnus) »** dans le filtre *Groupe clinique* ; le calcul comparatif n’utilise que les réponses cliniques connues.

La comparaison enfants/adultes de l’onglet 2 est une **comparaison prédéfinie**, et non un outil de création et d’enregistrement arbitraire de deux cohortes A/B. L’application conserve les clusters calculés sur la population de référence : **les filtres ne réentraînent pas KMeans**.

## Indicateurs et interprétation

Quatre indicateurs sont affichés sur les deux onglets :

| Indicateur | Définition |
|---|---|
| **Patients dans la sélection** | Nombre de patients après application des filtres |
| **Détections médianes / 91** | Médiane du nombre d’allergènes détectés sur le panel commun, parmi les mesures exploitables |
| **Profils analysables** | Nombre de patients disposant du panel commun complet |
| **Données cliniques Oui / Non** | Nombre de patients avec un statut exploitable pour l’information clinique choisie, rapporté à l’effectif filtré |

Autres mesures utilisées dans les graphiques :

- **Taux de détection d’un allergène** : proportion de patients dont la mesure dépasse le seuil descriptif retenu, sur les observations exploitables.
- **Écart de taux de détection** : différence entre deux proportions, exprimée en **points de pourcentage**.
- **Nombre de détections par patient** : nombre de mesures positives parmi les allergènes du panel commun.
- **Composition clinique d’un groupe** : nombre de réponses « Oui » parmi les réponses « Oui » et « Non » renseignées dans ce groupe.

Les valeurs affichées sont propres à la sélection en cours : un pourcentage n’est interprétable qu’avec son **dénominateur**. Un groupe très petit ou présentant de nombreux statuts inconnus appelle une vigilance particulière.

## Installation et lancement

### Prérequis

- Python **3.13** recommandé (versions des bibliothèques fixées dans `requirements.txt`) ;
- un navigateur récent ;
- les fichiers CSV et le dossier `src/` présents dans l’arborescence du projet.

### Windows — PowerShell

Depuis la racine du projet :

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe app.py
```

### macOS / Linux

```bash
python3.13 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python app.py
```

Ouvrir ensuite **http://127.0.0.1:8050** dans le navigateur. Le démarrage peut demander quelques secondes pour charger les données et préparer la projection et les groupes exploratoires.

Arrêter le serveur avec **`Ctrl+C`** dans le terminal. Aux lancements suivants, si l’environnement existe déjà, la commande de lancement suffit.

### Changer de port

Sous PowerShell :

```powershell
$env:PORT = "8051"
.\.venv\Scripts\python.exe app.py
```

Sous macOS / Linux :

```bash
PORT=8051 .venv/bin/python app.py
```

Ouvrir alors `http://127.0.0.1:8051`.

Le serveur est configuré pour écouter sur **`127.0.0.1`**, c’est-à-dire uniquement en local. Un déploiement public nécessiterait une configuration de production et une revue adaptée à la diffusion de données de santé.

## Architecture du projet

```text
Allergy_Atlas/
├── app.py                    # Point d'entrée : interface compacte et callbacks
├── requirements.txt          # Dépendances Python
├── README.md                 # Documentation générale
├── .gitignore
├── assets/
│   ├── compact.css           # Grille compacte, responsive, deux onglets
│   ├── style.css             # Styles partagés
│   ├── motion.js             # Ressource d'interface présente dans le projet
│   └── logo.svg
├── src/
│   ├── data_loader.py        # Chargement, contrôle et couverture des puces
│   ├── preprocessing.py     # Typage, variables dérivées, statuts cliniques
│   ├── metrics.py           # Indicateurs et filtres de population
│   ├── charts.py            # Figures Plotly
│   ├── insights.py          # Calculs des messages descriptifs
│   ├── clustering.py        # KMeans, PCA, diagnostics des profils
│   └── callbacks.py         # Callbacks complémentaires du projet
├── data/
│   ├── raw/                 # Jeu de données ACC utilisé par app.py
│   └── dictionaries/        # Dictionnaires PDF et XLS
├── components/              # Composants Dash partagés
├── pages/                   # Composants de pages présents dans le projet
├── docs/
│   ├── brief/               # Consignes du module (PDF)
│   └── images/              # Illustrations et captures du projet
└── tests/                   # Tests Python du traitement et des composants
```

Le **point d’entrée à utiliser est `app.py`**. Ses deux onglets et leurs callbacks sont définis directement dans ce fichier. Les modules `src/` mutualisent le chargement des données, la préparation, les figures, les indicateurs et les calculs exploratoires. Les répertoires `components/` et `pages/` restent présents dans le projet, mais ne constituent pas la navigation de l’interface compacte.

Pour retrouver rapidement une responsabilité technique :

| Intervention | Fichier |
|---|---|
| Modifier l’organisation des deux onglets, les filtres ou les callbacks de l’interface compacte | `app.py` |
| Modifier la disposition ou la hauteur des panneaux | `assets/compact.css` |
| Changer le chargement et les contrôles des sources | `src/data_loader.py` |
| Changer les règles de préparation | `src/preprocessing.py` |
| Modifier les calculs de population et les KPI | `src/metrics.py` |
| Modifier les graphiques | `src/charts.py` |
| Modifier les calculs descriptifs des messages | `src/insights.py` |
| Modifier PCA ou KMeans | `src/clustering.py` |

## Technologies utilisées

| Outil | Usage |
|---|---|
| **Python 3.13** | Traitements, calculs et exécution de l’application |
| **Dash 4.4.1** | Interface web, filtres, onglets et callbacks |
| **Plotly 5.24.0** | Visualisations interactives |
| **pandas 2.3.3 / NumPy 2.4.1** | Manipulations et calculs sur les données |
| **scikit-learn 1.8.0** | Standardisation, KMeans et PCA |
| **SciPy 1.17.0** | Calculs statistiques complémentaires |
| **CSS** | Mise en page compacte et adaptation aux écrans |
| **pytest 9.1.0** | Tests automatisés |

La liste exacte des dépendances et de leurs versions figure dans `requirements.txt`.

## Méthodes et limites

### Comparabilité biologique

Les technologies ISAC v1, ISAC v2 et ALEX² ne mesurent pas les mêmes ensembles d’allergènes. Pour les analyses transversales, l’application utilise les **91 allergènes communs**. Ce choix limite le biais lié au nombre de mesures disponibles, mais **ne garantit pas une équivalence parfaite entre les plateformes**.

### Détection IgE et données manquantes

Dans les graphiques, la détection descriptive correspond à une **mesure IgE strictement supérieure à zéro** (`IgE > 0`). Ce choix technique doit être distingué d’un seuil clinique de sensibilisation, du statut `Sensitization` fourni par la source et de tout diagnostic. Les mesures négatives non documentées sont exclues des calculs plutôt que transformées en zéros ; les informations cliniques inconnues ne sont pas assimilées à « Non ».

### Regroupement exploratoire

Les profils sont construits à partir des mesures du panel commun complet, après transformation `log1p` et standardisation. KMeans rapproche les patients selon les 91 variables biologiques ; la PCA représente ensuite les profils en deux dimensions. Les variables cliniques **ne servent pas à entraîner les groupes** : elles permettent seulement de les décrire a posteriori.

Le modèle est préparé sur la population de référence, puis les filtres limitent les profils affichés. La séparation statistique entre groupes n’équivaut ni à l’existence de catégories médicales naturelles ni à une validation clinique.

### Portée clinique et statistique

- Les comparaisons cliniques sont **descriptives et non ajustées** : d’autres facteurs peuvent expliquer les écarts observés.
- Les informations cliniques sont incomplètes, ce qui réduit les effectifs exploitables et peut introduire des biais de sélection.
- L’échantillon ACC ne permet pas de produire des estimations de prévalence applicables à la France entière.
- La variable de sévérité `Severe_Allergy` n’est pas présente dans le CSV utilisé. **La sévérité ne peut donc pas être prédite directement à partir d’une cible clinique disponible** ; ni les traitements, ni les niveaux IgE, ni les clusters ne doivent être assimilés à un score de gravité.
- L’application ne fournit **aucun diagnostic ni recommandation médicale individualisée**.

## Tests et résolution des problèmes

### Exécuter les tests

Windows :

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

macOS / Linux :

```bash
.venv/bin/python -m pytest -q
```

Les tests présents dans `tests/` concernent principalement la préparation des données, les indicateurs et des composants du projet. **Leur réussite ne dispense pas d’une vérification manuelle des deux onglets de `app.py` dans un navigateur**, notamment au format 1366 × 768, avec plusieurs sélections de filtres et des populations vides ou réduites.

### Problèmes courants

| Symptôme | Solution |
|---|---|
| `ModuleNotFoundError` | Installer `requirements.txt` avec le Python de `.venv`, puis lancer l’application avec le même interpréteur. |
| Le CSV est introuvable | Vérifier le nom exact et la présence du fichier dans `data/raw/`. |
| Le port 8050 est occupé | Arrêter l’autre serveur ou choisir un port avec la variable `PORT`. |
| Le démarrage semble long | Patienter pendant les calculs initiaux des profils. |
| Un graphique est vide | Vérifier que les filtres laissent assez de patients ou que les deux catégories cliniques nécessaires sont présentes. |
| Les panneaux débordent | Utiliser un navigateur à 100 % de zoom, un écran de bureau d’au moins 1366 × 768, ou accepter le défilement sur un écran plus petit. |
| Une modification du code n’apparaît pas | Arrêter et relancer `python app.py` ; le mode debug est désactivé. |

---

**En résumé :** Allergy Atlas transforme une cohorte allergologique complexe en une exploration visuelle compacte. Son premier onglet décrit les détections IgE et leurs associations cliniques ; le second permet d’examiner des profils multidimensionnels. Les résultats servent à **formuler des hypothèses de recherche**, pas à diagnostiquer une allergie ou à prédire sa sévérité chez un patient.
