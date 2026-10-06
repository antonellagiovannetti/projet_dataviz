# Un signal global, des profils qui divergent

Dashboard narratif réalisé avec **Dash et Plotly** pour le cours de data visualisation (M2 IA / Data), à partir des données publiques de l’Allergen Chip Challenge.

## Problématique

**La diversité des sensibilisations IgE varie-t-elle avec l’âge et les symptômes cutanés, et cette relation se retrouve-t-elle selon la puce utilisée ?**

Le fil rouge part d’un signal global presque parfaitement concordant avec les mesures moléculaires, puis montre que la puce définit la fenêtre d’observation. Il compare ensuite la part de composants au seuil selon l’âge et les symptômes cutanés, avant de laisser le lecteur explorer les composants.

Cette question est volontairement plus rigoureuse qu’une prédiction de sévérité : le CSV fourni ne contient pas les variables `Allergy_Present` ni `Severe_Allergy` décrites dans le dictionnaire. Le dashboard ne prétend donc pas prédire la sévérité d’une allergie.

## Parcours de lecture

1. **Le statut global et le signal moléculaire** — matrice de concordance entre `Sensitization` et la présence d’au moins une mesure de composant à 0,30 ou plus. C’est un contrôle interne, pas une validation clinique indépendante.
2. **La fenêtre de mesure** — nombre médian de composants observés pour chaque puce. Une cellule absente du panel reste manquante ; elle ne devient pas un zéro.
3. **L’âge** — part moyenne des composants mesurés au seuil par patient et par classe d’âge, avec intervalles bootstrap à 95 %.
4. **Les symptômes cutanés** — écart entre dossiers avec et sans symptômes, standardisé sur la distribution d’âge de chaque puce. Le résultat est présenté séparément par plateforme.
5. **L’exploration** — filtre d’âge, choix de puce et de composant ; la sélection est reflétée dans l’URL et peut être partagée. La carte retient les 16 composants les plus souvent au seuil en moyennant les taux par puce ; les cellules avec moins de 20 mesures sont masquées.

## Méthode et limites

- Le seuil exploratoire `0.30` est appliqué dans l’unité propre à la plateforme. Il sert ici à comparer qualitativement des signaux moléculaires, jamais à définir un grade de sévérité.
- Pour chaque patient, la **diversité observée** est le nombre de composants mesurés à `≥ 0.30`, divisé par le nombre de composants effectivement mesurés. La moyenne est calculée ensuite au niveau des patients, afin qu’un panel plus grand ne pèse pas mécaniquement davantage.
- Les classes d’âge sont `0–5`, `6–11`, `12–17`, `18–39` et `40+`. Les comparaisons sont transversales : elles ne suivent pas les mêmes personnes dans le temps.
- Les intervalles des moyennes par âge utilisent un bootstrap patient (600 réplications). Le contraste cutané est standardisé directement sur la distribution d’âge observée parmi les dossiers avec statut cutané connu, séparément pour chaque puce ; son intervalle bootstrap rééchantillonne les patients dans chaque classe d’âge et statut cutané.
- Le contraste cutané est défini comme **symptômes oui − symptômes non**. Les intervalles qui recoupent zéro restent compatibles avec l’absence de différence dans cette analyse.
- Les symptômes cutanés inconnus et les mesures absentes sont conservés comme tels. Les valeurs négatives `−1` présentes dans le fichier sont traitées comme codes de mesure absente.
- L’analyse est descriptive et rétrospective. Elle ne démontre ni causalité, ni performance prédictive, ni validité clinique indépendante. L’âge n’est pas le seul facteur de confusion possible et la composition des cohortes peut différer entre plateformes.

## Lancer le dashboard sous Windows

Le fichier CSV reste local dans le dossier Téléchargements. Le programme essaie automatiquement de le trouver à cet emplacement ; il n’est pas nécessaire de le copier dans le dépôt.

```powershell
cd C:\Users\yoanv\Desktop\DataViz\projet_dataviz
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python app.py
```

Ouvrir ensuite [http://127.0.0.1:8050](http://127.0.0.1:8050).

Si le CSV est ailleurs, définir son chemin avant de lancer l’application :

```powershell
$env:ACC_CSV_PATH = "C:\chemin\vers\allergenchipchallenge-data-corrected-final-hdh-sfa.csv"
python app.py
```

Les versions de Python 3.10 ou ultérieures sont recommandées. Le dashboard se lance sur la machine locale et n’envoie pas les données vers un service externe.

## Trame possible pour la soutenance

Présenter la question, le périmètre des données et l’absence de cible de sévérité ; faire lire la concordance globale ; expliquer pourquoi les panels ne sont pas interchangeables ; comparer la diversité par âge puis le contraste cutané standardisé ; terminer par l’exploration et rappeler ce que les résultats ne permettent pas de conclure. Le principal choix de visualisation est de rendre les dénominateurs, les intervalles et les valeurs manquantes visibles, pour éviter qu’une carte ou un taux masque les différences de couverture.

## Sources

- [Page du défi : Identifier et prévoir les facteurs de sévérité des allergies](https://defis.data.gouv.fr/defis/identifier-et-prevoir-les-facteurs-de-severite-des-allergies)
- [Jeu de données Allergen Chip Challenge sur data.gouv.fr](https://www.data.gouv.fr/datasets/allergen-chip-challenge/)
- [Étude comparative mentionnant le seuil qualitatif de 0,30 pour les dosages ISAC et ALEX](https://www.mdpi.com/2075-4418/14/10/976)

## Fichiers du projet

- `app.py` : récit, graphiques Plotly, interface Dash et filtres partageables.
- `acc_data.py` : lecture locale, nettoyage des codes manquants et calculs statistiques.
- `assets/style.css` : mise en page responsive et styles d’accessibilité.
- `requirements.txt` : dépendances Python.
