# Allergy Atlas — oral de dix minutes

*Public : allergologues, cliniciens et chercheurs en allergologie.*

> **Fil directeur : les profils IgE sont différents ; rendre les mesures comparables permet d’explorer cette diversité et ses liens cliniques, sans conclure à une sévérité individuelle.**

## Préparer la démonstration

Lancer `python app.py` dans l’environnement installé, attendre le chargement des modèles, puis ouvrir [Allergy Atlas](http://127.0.0.1:8050/#overview). Choisir **Story** : le récit utilise la cohorte complète et le modèle de référence, même si des réglages Explore ont été conservés. Il n’est pas nécessaire d’effacer les filtres ou les cohortes A/B.

Suivre les **six chapitres** ci-dessous. Les durées totalisent exactement dix minutes. Garder les sections d’approfondissement repliées ; le glossaire et le laboratoire sont disponibles pour les questions après l’oral. Le but est de faire comprendre le raisonnement, pas de montrer toutes les fonctionnalités.

## 0:00–1:00 — 01 · Complexité

**À l’écran :** question d’ouverture, quatre indicateurs et distribution des détections.

« Nous disposons de 4 271 patients et de 241 mesures IgE différentes dans le fichier. Elles ne sont pas toutes mesurées chez chaque patient. Comment rendre leurs profils lisibles pour explorer la cohorte ? »

Rappeler les **trois technologies** et les **83,8 % sensibilisés selon la variable source**. Montrer l’histogramme : sur le panel commun, médiane **11 détections**, quartiles **4–21**.

« Une variable sensibilisé / non sensibilisé ne suffit pas à résumer cette diversité. Mais avant de comparer les profils, peut-on vraiment comparer tous les patients ? »

**Transition :** ouvrir Comparabilité.

## 1:00–2:30 — 02 · Comparabilité

**À l’écran :** couverture des trois technologies, décision du panel commun, données non renseignées.

« ISAC V1 et V2 couvrent 112 mesures chacun, ALEX 223. Un compte sur toutes les mesures disponibles donnerait mécaniquement davantage d’occasions de détection avec ALEX. »

Montrer la matrice, puis le passage **241 mesures → 91 communes → 4 241 patients complets**.

« Nous retenons les 91 allergènes communs. Les 30 patients incomplets restent dans les autres analyses, mais ne construisent pas les groupes. Ce panel commun ne rend pas les instruments parfaitement interchangeables. »

Pointer la seconde décision : **une information inconnue ne devient jamais une absence de symptôme ni une valeur nulle**. Les symptômes cutanés ne sont pas exploitables pour **57,2 %** des patients. Les fréquences seront donc lues avec leurs dénominateurs.

« Nous savons maintenant sur quel périmètre comparer. Comment les signaux se combinent-ils ? »

## 2:30–4:30 — 03 · Profils IgE

**À l’écran :** classement des allergènes, distribution puis heatmap des patients.

« À l’échelle de la cohorte, Phl p 1 est le plus souvent détecté : environ 50 %. Mais cette fréquence ne montre pas quels signaux coexistent chez un patient. »

Passer à la lecture individuelle : rappeler la médiane **11**, les quartiles **4–21**, puis montrer les combinaisons de la heatmap. Elle illustre au plus **120 patients** ; les statistiques concernent toute la cohorte affichée.

« Les différences portent sur le nombre de signaux et sur leurs combinaisons. Ici, détecté signifie une mesure valide supérieure à zéro ; c’est une règle descriptive, pas un seuil diagnostique universel. »

Ne pas ouvrir la comparaison par âge pendant le parcours principal. Garder le temps pour expliquer ce que les représentations apportent : classement global, dispersion, puis coexistence chez les patients.

« Cette diversité biologique est visible. Retrouve-t-on aussi des différences du côté clinique ? »

## 4:30–6:30 — 04 · Clinique

**À l’écran :** périmètre clinique possible, effectifs cutanés, différences de fréquence et exemple Ara h 2.

« La variable Severe_Allergy figure dans le dictionnaire, mais pas dans le CSV. Nous pouvons comparer certaines informations disponibles ; nous ne pouvons pas inventer un score de sévérité. »

Présenter les symptômes cutanés : **1 140 Oui, 686 Non, 2 445 non renseignés ou non pertinents**. Le contraste repose sur **1 826 patients renseignés**.

« Ara h 2 est détecté chez 27,7 % des patients avec symptômes cutanés, contre 8,5 % sans symptômes : un écart de 19,3 points. »

Expliquer le sens des barres **Oui − Non**, puis la limite :

« Nous observons un lien ; nous ne démontrons pas une cause ni une prédiction d’allergie sévère. Les autres variables disponibles décrivent notamment des traitements, pas la gravité des maladies. »

« Comparer les allergènes un par un reste limité. Peut-on regarder les 91 mesures ensemble ? »

## 6:30–8:30 — 05 · Groupes

**À l’écran :** préparation des mesures, comparaison des K, PCA, empreintes et composition par technologie.

« Nous regroupons les patients dont les mesures se ressemblent, sans utiliser la clinique pour construire les groupes. La transformation log1p réduit le poids des grandes valeurs ; la standardisation par technologie limite certains écarts entre puces. »

**KMeans utilise les 91 mesures ; la PCA les représente sur une carte à deux axes.** Ne pas présenter la carte comme l’espace dans lequel KMeans est calculé.

« Parmi les solutions de deux à huit groupes, deux donnent la meilleure séparation selon la silhouette : 0,440. C’est un choix statistique, pas deux catégories médicales. »

Montrer ce qui distingue les empreintes. La carte représente **22,54 %** de la variance : elle est partielle. Les groupes rassemblent **3 433 et 808 patients**.

« Ces groupes reflètent-ils seulement les technologies ? Le V de Cramér vaut 0,010 dans cette solution : le lien global avec la puce est faible, sans exclure tout effet de mesure. »

« Des groupes de profils proches apparaissent. Ils restent exploratoires. Qu’avons-nous réellement appris ? »

## 8:30–10:00 — 06 · Conclusion

**À l’écran :** les trois niveaux de conclusion.

**Établi :** les profils IgE sont différents ; un panel commun est nécessaire ; certaines détections diffèrent selon la clinique renseignée ; les 91 mesures permettent de regrouper des profils proches.

**Suggéré :** les signatures apportent davantage qu’une variable binaire ; certains signaux méritent une analyse clinique complémentaire.

**Non démontré :** une cause, une prédiction de sévérité, un diagnostic à partir d’un groupe ou une généralisation à toute la population.

Terminer avant dix minutes :

« Allergy Atlas rend une cohorte complexe plus lisible pour un professionnel de santé. Le parcours explique ce que nous comparons, pourquoi nous le comparons et ce que chaque observation permet de conclure. Il aide à repérer des questions à approfondir ; il ne remplace pas leur validation clinique. »

## Après les dix minutes — démonstration facultative

Le laboratoire **« À vous d’explorer »** ouvre le mode Explore. Utiliser un exemple rapide pour comparer enfants / adultes, hommes / femmes, avec / sans symptômes cutanés ou groupes 1 / 2. **Ces boutons remplacent A et B à partir de la source entière**, indépendamment des filtres. Le contraste groupes 1 / 2 utilise le modèle courant ; avec K supérieur à 2, les autres groupes ne sont pas inclus.

Pour montrer une sélection personnalisée, appliquer un filtre ou un lasso PCA puis enregistrer A ou B. Une sauvegarde fige les identifiants ; les filtres suivants ne changent pas les cohortes enregistrées. Dans le graphique A/B, la différence est **B − A**. Revenir en Story conserve les réglages Explore et les cohortes.

Le glossaire sert à expliquer ponctuellement PCA, silhouette ou points de pourcentage. L’ouvrir seulement si une question le justifie.

## Réponses courtes aux questions probables

**Pourquoi ne pas utiliser les 241 mesures ?** Les trois technologies ne couvrent pas le même ensemble. Remplacer les mesures non disponibles par zéro inventerait des non-détections.

**Pourquoi ne pas prédire la sévérité ?** La cible n’est pas disponible. Un traitement ou une somme d’IgE n’en constitue pas un substitut validé.

**Pourquoi K = 2 ?** Il obtient la meilleure silhouette parmi K = 2 à 8 dans la préparation retenue. La clinique n’a pas servi à choisir ou former ces groupes.

**Pourquoi deux modes ?** Story fournit un parcours stable pour comprendre le raisonnement. Explore permet ensuite de tester des sous-populations et les choix du modèle, sans effacer les réglages en revenant au récit.

**Pourquoi Dash et Plotly ?** Les mêmes règles de calcul alimentent toutes les vues ; les interactions permettent de comparer des populations et de garder leurs effectifs visibles. La [présentation détaillée](presentation.md) explique les choix techniques et scientifiques.
