# Allergy Atlas

**Explorer les profils de détection IgE et leurs associations cliniques dans l'Allergen Chip Challenge (ACC)**
Projet de Data Visualisation — Master 2 IA/Data — Dash / Plotly

**Public cible :** allergologues impliqués dans la recherche clinique et chercheurs en allergologie.  
**Usage :** exploration descriptive d'une population de patients et génération d'hypothèses ; ni diagnostic ni décision médicale individuelle.

## Problématique

**Comment se structurent les profils de détection IgE dans la cohorte ACC, et quelles associations observe-t-on avec les informations cliniques disponibles ?**

L'application répond à la question en deux étapes, accessibles dans deux onglets. Chaque onglet tient sur un écran d'ordinateur sans défilement principal (cible : 1366 × 768 ou supérieur, navigateur à 100 %). Dans une fenêtre étroite ou peu haute, sur tablette et sur mobile, le défilement vertical préserve la hauteur et la lisibilité des graphiques. Les contrôles et KPI se réorganisent, les deux onglets restent accessibles, et les libellés et effectifs du graphique clinique s'adaptent à la largeur du panneau.

## Les deux onglets

| Onglet | Question | Fonctionnalités |
| --- | --- | --- |
| **01 — Identifier les profils IgE** | Comment se structurent les profils de détection IgE ? | Distribution du nombre de détections, classement des allergènes, projection PCA et écarts de détection entre le profil sélectionné et les autres patients filtrés |
| **02 — Explorer les liens cliniques** | Quelles associations observe-t-on avec les informations cliniques ? | Écart de détection Oui/Non, fréquence du statut clinique Oui par profil, caractérisation clinique du profil sélectionné face au reste de la cohorte filtrée, réponse et limites |

La problématique reste affichée dans l'en-tête. Les deux onglets correspondent à ses deux sous-questions. Les groupes sont créés à partir des données biologiques **sans utiliser les variables cliniques** ; celles-ci servent seulement à caractériser les groupes a posteriori. Les groupes se différencient principalement par l'étendue de leurs détections IgE : ce sont des profils exploratoires, **pas des phénotypes cliniques établis**.

## Filtres et lecture

Un bandeau commun permet de choisir :

- **Population :** tous, moins de 18 ans ou 18 ans et plus ;
- **Technologie :** toutes, ISAC V1, ISAC V2 ou ALEX ;
- **Information clinique :** symptômes cutanés, traitements de l'asthme, de la rhinite ou de la dermatite ;
- **Groupe clinique :** tous, Oui ou Non.

Les résultats se recalculent selon la sélection ; l'effectif actif et les nombres de statuts cliniques renseignés et inconnus sont indiqués. **Pour comparer Oui et Non**, conserver le filtre « Groupe clinique » sur « Tous » : choisir uniquement Oui ou Non retire l'autre groupe de comparaison. Ce filtre s'applique aussi à la caractérisation clinique : pour la variable ainsi filtrée, le taux de Oui, lorsqu'il est calculable, vaut alors 100 % ou 0 % par construction. Les filtres n'entraînent pas de nouvel apprentissage de KMeans.

Les menus « Allergène à suivre » et « Profil à explorer » offrent une alternative aux clics sur les graphiques. Une barre d'allergène sélectionne cet allergène ; un point PCA ou une barre de fréquence clinique par profil sélectionne le profil. Le bouton « Réinitialiser les filtres » rétablit les valeurs initiales et efface les sélections.

Les quatre indicateurs affichés sont : « Patients dans les filtres », « Détections médianes / 91 », « Profils IgE complets » et « Statuts cliniques renseignés ». Le dernier porte sur l'information clinique choisie et indique aussi les inconnus.

Le graphique « Qu'est-ce qui distingue le profil ? » compare les pourcentages de détection du profil aux **autres patients de la cohorte filtrée**, en excluant le profil du groupe de référence. Sans sélection explicite, il décrit le profil le plus nombreux, indiqué dans le sous-titre. Les patients sans profil attribué restent dans le groupe de référence ; chaque taux utilise uniquement les mesures IgE disponibles pour l'allergène concerné.

Le graphique « Quel profil clinique accompagne le groupe sélectionné ? » nécessite une sélection de profil. Pour chacune des quatre variables — symptômes cutanés, traitement de l'asthme, traitement de la rhinite, traitement de la dermatite — il compare le profil au reste de la cohorte filtrée. **Le pourcentage de Oui est calculé parmi les seuls statuts Oui/Non renseignés, séparément pour chaque variable et chaque groupe.** Les effectifs renseignés et inconnus sont explicités ; le survol détaille les dénominateurs. Si aucun statut n'est renseigné, le taux est indisponible, jamais remplacé par 0 %. Les sélections vides ou les comparaisons impossibles produisent un message explicite.

## Données et règles scientifiques

Le CSV ACC contient **4 271 patients**, **256 colonnes**, dont **241 mesures IgE**. Les patients ont été analysés avec trois technologies (ISAC V1, ISAC V2, ALEX) dont la couverture en allergènes diffère. Les comparaisons transversales reposent donc sur les **91 allergènes communs** ; **4 241 patients** ont un profil complet sur ce panel.

- La règle `IgE > 0` est un **seuil descriptif de détection dans l'application**, et non un diagnostic clinique de sensibilisation ou d'allergie.
- Les valeurs biologiques non mesurées et les codes cliniques inconnus ne sont **pas assimilés à zéro ou à Non**.
- Le pipeline utilise les **cas complets sur les 91 allergènes communs**, une transformation `log1p`, puis une **standardisation par technologie**. KMeans est ajusté sur toutes ces dimensions pour **K de 2 à 8** ; le choix de K maximise la silhouette sur un échantillon fixe d'au plus 1 500 patients. La PCA fournit seulement une représentation en deux dimensions ; elle **ne sert pas** à créer les groupes. Les patients incomplets conservent un profil « Non attribué » et ne sont pas projetés.
- La standardisation par technologie réduit les différences de moyenne et de variance entre puces ; elle ne constitue pas une calibration clinique des mesures.
- Les variables de traitement décrivent un **traitement**, pas un diagnostic. La variable source `Sensitization` reste distincte des détections dérivées de `IgE > 0`.
- **Associations descriptives : ces résultats ne constituent ni un diagnostic individuel ni une preuve de causalité.** Les comparaisons sont non ajustées et ne démontrent pas de facteur de risque indépendant.
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
src/clustering.py       KMeans et projection PCA de visualisation
src/insights.py         Résultats descriptifs et textes calculés
data/raw/               CSV ACC utilisé par le chargeur
data/dictionaries/      Dictionnaires ACC
tests/                  Tests des données, analyses, graphiques et callbacks compacts
README.md               Documentation du projet
```

**Le point d'entrée est `app.py`.** Ses imports utilisent les six modules `src/` décrits ci-dessus. Dash charge automatiquement les assets : `assets/compact.css` définit les dispositions responsive, `assets/responsive.js` adapte les annotations Plotly à la taille des panneaux sans recalculer les données, et `assets/style.css` reste nécessaire pour certaines règles globales de typographie et de contrôles.

## Tests et dépannage

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

Les tests couvrent les données et leurs manquants, les dénominateurs des comparaisons, les groupes de référence disjoints, les états vides et les callbacks de la version compacte via des requêtes Dash réelles. Ils vérifient notamment les deux onglets, les filtres, les sélections et la réinitialisation. La vérification dans un navigateur complète ces tests : survols, lisibilité et absence de défilement principal à la résolution utilisée pour la soutenance.

- **`ModuleNotFoundError` :** installer les dépendances avec le même interpréteur Python que celui utilisé pour lancer `app.py`.
- **Port 8050 occupé :** arrêter le serveur précédent ou définir `PORT`.
- **CSV introuvable :** vérifier `data/raw/allergenchipchallenge-data-corrected-final-hdh-sfa.csv`, utilisé par `src/data_loader.py`.
- **Changements invisibles :** arrêter le serveur, relancer puis rafraîchir le navigateur.

## Démonstration orale — 10 minutes

Présenter la problématique, expliquer pourquoi les mesures des trois puces sont comparées sur un panel commun, puis montrer l'onglet 1 : étendue des détections, allergènes les plus détectés et groupes exploratoires. Sélectionner un profil et examiner ses écarts par rapport aux autres patients filtrés. Passer ensuite à l'onglet 2 pour explorer les associations avec les informations cliniques, comparer les quatre variables du profil au reste de la cohorte et rappeler les effectifs renseignés et inconnus. Conclure sur les limites des associations descriptives.

**Sources :** Société Française d'Allergologie / Health Data Hub — Allergen Chip Challenge (ACC). Les dictionnaires et le fichier CSV accompagnent le projet.
