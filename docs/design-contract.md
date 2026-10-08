# Contrat de conception — Allergy Atlas

## Public, question et portée

**Public principal :** un allergologue, clinicien ou chercheur en allergologie qui veut comprendre rapidement une cohorte, comparer des sous-populations et identifier des profils ou des signaux à approfondir.

**Question :** comment rendre les profils IgE lisibles et explorer leurs liens avec les informations cliniques disponibles ?

**Message central :** les patients présentent des profils différents. Organiser correctement les mesures rend cette diversité visible et permet de formuler des pistes cliniques ; les données disponibles ne permettent pas de conclure directement sur la sévérité.

Le langage est professionnel et concis. Les termes médicaux usuels sont conservés ; les termes statistiques sont expliqués dans leur usage : « PCA — une carte simplifiée des profils », « clustering — regrouper les profils qui se ressemblent ». L’application est un outil d’exploration de cohorte, sans diagnostic ni décision médicale individuelle.

La priorité reste la **datavisualisation**. Le clustering répond à la nécessité de regarder 91 mesures ensemble ; il ne constitue pas la finalité du projet. La refonte conserve les données préparées, les analyses, les graphiques et les interactions, en réorganisant leur rôle dans le récit.

## Parcours et budget visuel

Le parcours obligatoire comporte **six chapitres**, signalés par le composant « Notre progression ». Le glossaire et le laboratoire sont des accès complémentaires. Le bouton de fin de chapitre formule le besoin de l’étape suivante ; Groupes mène directement à Conclusion.

| Étape | Question du professionnel | Représentation et contribution |
|---|---|---|
| **01 Complexité** | Les patients ont-ils des profils très différents ? | L’histogramme révèle la dispersion des détections, au-delà d’un indicateur binaire. |
| **02 Comparabilité** | Comparons-nous réellement les mêmes mesures ? | La matrice de couverture justifie les 91 allergènes communs ; les données manquantes délimitent la clinique exploitable. |
| **03 Profils IgE** | Quels signaux dominent et comment se combinent-ils ? | Le classement situe les fréquences ; la distribution et la heatmap montrent la diversité individuelle. |
| **04 Clinique** | Certaines détections diffèrent-elles selon la clinique disponible ? | Les barres divergentes montrent le sens et l’amplitude des écarts ; Ara h 2 rend leur lecture concrète. |
| **05 Groupes** | Que voyons-nous en considérant les 91 mesures ensemble ? | Les scores expliquent K ; la PCA situe les patients ; les empreintes décrivent les groupes ; la composition par puce interroge l’effet de mesure. |
| **06 Conclusion** | Qu’est-ce qui est établi, suggéré ou non démontré ? | Trois niveaux de conclusion répondent à la question sans ajouter de graphique décoratif. |

Le parcours oral dure dix minutes. Le laboratoire A/B est un prolongement facultatif, après le récit. Les graphiques secondaires sont placés dans des sections d’approfondissement pour préserver la lecture principale. Le changement d’organisation ne justifie pas d’ajouter de nouvelles analyses.

## Hiérarchie narrative et visuelle

Chaque chapitre suit le même raisonnement : **question → obstacle → décision → visualisation → interprétation → nouvelle question**.

La question et le message important précèdent les détails techniques. Autour d’un graphique important, quatre éléments courts suffisent :

- **Question :** ce que le graphique aide à comprendre.
- **Lecture :** le sens des axes, des couleurs ou du contraste.
- **À retenir :** un constat calculé pour la population affichée, ou une clé de lecture quand un constat n’est pas possible.
- **Prudence :** la limite utile à l’interprétation, avec les détails secondaires repliables.

Les composants narratifs partagent une identité cohérente. Les décisions du panel commun et du traitement des inconnus sont visibles avant les résultats qui en dépendent. Une case sans mesure, un zéro et une donnée clinique inconnue ne doivent pas paraître équivalents.

L’identité conserve un fond papier légèrement teinté, des surfaces blanches, le bleu nuit pour le texte et la structure, le turquoise pour les actions et accents. L’orange signale des limites contextuelles. Les couleurs des puces et des groupes restent stables, accompagnées de libellés ; aucune palette vert/rouge ne doit transformer automatiquement les patients en « sains » ou « malades ».

Les unités et dénominateurs restent accessibles. Pas de 3D, jauges ou animations nécessaires à la compréhension. L’espace disponible sert d’abord aux questions et aux graphiques.

## Deux modes, des états préservés

**Story** est le mode par défaut. Il utilise la cohorte source entière et le modèle de référence : standardisation par technologie et K retenu par la silhouette. Les réglages Explore conservés ne modifient pas le récit. Le filtrage croisé graphique est réservé à Explore. Les contrôles secondaires ne dominent pas l’écran.

**Explore** donne accès aux filtres, sélections, lasso, choix de K et standardisation. Les textes de résultat suivent la sélection ; les diagnostics globaux du modèle gardent leur périmètre source explicite. Les filtres ne réapprennent pas le modèle.

Le passage en Story conserve les filtres, réglages, sélections Explore et cohortes A/B. Revenir en Explore permet de retrouver cette exploration. Le laboratoire ouvre Explore ; revenir au récit depuis ce laboratoire conduit à la première étape.

## Contrat d’interaction

- Les transitions animent le changement de chapitre, avec fondu, léger glissement et repère mobile dans la navigation. Une modification de filtre ne rejoue pas cette transition. La préférence système de réduction des animations désactive ces effets.
- En Explore, les filtres globaux persistent entre chapitres. L’effectif retenu, les critères actifs et une action de remise à zéro gardent la sélection compréhensible.
- Un clic sur une puce, une classe d’âge, un allergène ou un groupe correspond à un contrôle explicite. Pour un allergène, le clic retient les patients dont la mesure est détectée, c’est-à-dire supérieure à zéro.
- Le lasso ou le rectangle de la PCA retient des identifiants précis. Une sélection vide reste vide ; elle ne doit jamais être remplacée silencieusement par toute la cohorte. L’utilisateur peut effacer la sélection.
- Enregistrer A ou B fige les patients retenus et le contexte du modèle. Ces instantanés ne changent pas avec les filtres ultérieurs. Le chevauchement est indiqué ; deux cohortes libres ne sont pas nécessairement indépendantes.
- Les cohortes A/B persistent localement dans le navigateur ; elles ne constituent pas un compte utilisateur partagé.
- Les quatre exemples du laboratoire remplacent A et B à partir de la **source entière**, indépendamment des filtres et de la sélection graphique : enfants / adultes, hommes / femmes, symptômes cutanés Oui / Non, groupes 1 / 2. Les âges inconnus et statuts cutanés inconnus sont exclus des contrastes correspondants. Le contraste des groupes utilise le modèle courant ; avec K supérieur à 2, seuls les groupes 1 et 2 sont comparés.
- Le sens des écarts est annoncé : **Oui − Non** pour la clinique, **B − A** pour les cohortes.
- Sur petit écran, les filtres Explore deviennent un tiroir refermable. Les commandes et sections repliables restent utilisables au clavier, avec libellés et focus visibles. Le récit n’exige aucun geste graphique exclusif.
- Une sélection vide ou un dénominateur nul produit un état explicite, jamais un zéro inventé pour une statistique indéfinie.

## Contrat scientifique

- Les **241 mesures** désignent les colonnes IgE du fichier ; elles ne sont pas toutes disponibles chez chaque patient. La comparaison transversale et les groupes reposent sur les **91 allergènes communs**.
- `Sensitization` est une variable source distincte du compte calculé. Une détection signifie une mesure valide strictement supérieure à zéro, sans seuil diagnostique universel revendiqué.
- Les valeurs IgE négatives non documentées sont invalides. Elles restent traçables dans la source et sont masquées dans les calculs. Une absence de mesure n’est pas remplacée par zéro.
- Les comptes sur 91 mesures, KMeans et PCA nécessitent un panel complet. Les patients incomplets restent présents dans les autres analyses et dans les effectifs appropriés.
- Les fréquences IgE utilisent les mesures observées par allergène. Les fréquences cliniques utilisent les patients renseignés. Les effectifs des groupes cliniques et les dénominateurs IgE peuvent donc différer.
- Les traitements décrivent un traitement déclaré, pas la présence certaine ni la gravité d’une maladie. Le code 9 reste inconnu ; pour les symptômes cutanés, il est documenté comme sans objet ou non pertinent.
- KMeans utilise uniquement les 91 mesures IgE préparées. La PCA utilise les mêmes mesures pour une projection ; elle n’est pas l’entrée de KMeans. La clinique décrit les groupes après leur construction.
- Les scores K = 2 à 8 justifient le choix par défaut. La silhouette n’est pas une validation clinique. Les groupes et leur numérotation ne sont pas des diagnostics ou des degrés de gravité.
- Un panel commun et la standardisation par technologie ne garantissent pas une harmonisation parfaite. Le V de Cramér et la composition par puce sont des diagnostics limités de l’effet de plateforme.
- Les comparaisons restent descriptives et non ajustées. Âge, recrutement, technologie ou disponibilité des données peuvent participer aux écarts. Aucune causalité, prédiction individuelle ou représentativité générale n’est déduite.
- `Severe_Allergy` est mentionnée dans le dictionnaire général, mais absente du CSV. Aucune cible artificielle de sévérité n’est créée.

## Choix technique et vérification

Dash coordonne les états et callbacks ; Plotly fournit les interactions graphiques ; pandas et NumPy partagent les calculs entre vues. scikit-learn prépare les mesures et calcule les modèles ; SciPy fournit le diagnostic d’association. CSS et JavaScript adaptent la lecture et les transitions. Les tests pytest vérifient les invariants et comportements utiles.

La vérification porte sur les effectifs source, le sens des contrastes, les dénominateurs manquants, le modèle de référence Story, la conservation de l’état Explore, les filtres combinés, le lasso, les cohortes et les exemples rapides. Contrôler aussi les cas vides, la navigation, les callbacks, le clavier, les sections repliables, le mobile et la réduction des animations.

Une revue visuelle complète les tests : questions lisibles, axes et légendes visibles, graphiques cohérents avec leur texte, absence de débordement ou de commande masquée. Les captures du dossier `docs/images` documentent l’interface ; elles ne remplacent pas les contrôles fonctionnels.

La [présentation](presentation.md) explique le pourquoi et le comment. Le [guide oral](oral-guide.md) fixe le parcours de dix minutes. Le [README](../README.md) décrit le lancement et l’architecture. Les [consignes du module](brief/Projets.pdf) restent la référence pour les attendus d’évaluation.
