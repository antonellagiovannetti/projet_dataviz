# Démonstration de dix minutes

## Préparer la démonstration

Lancer `python app.py` dans l'environnement installé, attendre la préparation des modèles, ouvrir l'application à `http://127.0.0.1:8050`, puis réinitialiser les filtres. Garder une fenêtre assez large pour montrer les graphiques ensemble. Les effectifs ci-dessous décrivent la cohorte complète ; ils changent dès qu'un filtre est appliqué.

Le fil directeur : **comprendre les mesures avant de comparer les patients, puis utiliser l'interaction pour explorer des différences sans leur donner une portée médicale indue.**

## 0:00–1:00 — Question et choix de conception

« Nous disposons de centaines de mesures IgE par patient. Comment transformer cette complexité en profils compréhensibles et les rapprocher des informations cliniques disponibles ? »

Montrer le titre et les indicateurs : **4 271 patients, 241 mesures IgE, trois technologies**. La variable fournie `Sensitization` vaut 1 pour **3 579 patients, soit 83,8 %**. L'âge médian est **16 ans parmi 4 210 âges connus**.

Expliquer en une phrase le choix de Dash/Plotly : la même population sélectionnée alimente plusieurs graphiques ; la PCA permet une sélection spatiale ; les cohortes A/B sont mémorisées pour une comparaison dynamique. La valeur ajoutée vient du parcours et des interactions.

Ouvrir brièvement **Repères** : distinguer « détection », « sensibilisation source » et « allergie clinique », puis revenir à la vue d’ensemble. Cette page sert de glossaire pendant toute la présentation ; sa recherche retrouve aussi les sigles (IgE, PCA, KMeans) et les notions statistiques. Les exemples de calcul y sont fictifs.

## 1:00–2:00 — La mesure précède l'interprétation

Passer à **Mesures**. Montrer les **2 351 ISAC V1, 781 ISAC V2 et 1 139 ALEX**. La matrice révèle **112 mesures par version ISAC contre 223 pour ALEX**. Un compte brut de détections n'est donc pas comparable entre puces.

« Nous retenons les **91 allergènes communs** pour les comparaisons transversales. Commun ne veut toutefois pas dire que les technologies sont parfaitement interchangeables. »

Pointer les informations cliniques non renseignées : **57,2 %** pour les symptômes cutanés, **64,9 %** pour le traitement de l'asthme et **69,3 %** pour le traitement de la rhinite. Mentionner les **52 valeurs IgE à −1**, sans code documenté : elles sont écartées des mesures valides ; aucune n'est transformée en zéro.

## 2:00–4:00 — Lire la diversité des signatures

Passer à **Sensibilisation**. Montrer que **Phl p 1 est détecté chez environ 50,0 %** de la cohorte. Sur les 91 allergènes communs, la médiane est de **11 détections** parmi **4 241 patients ayant toutes ces mesures valides**.

« Ici, détecté signifie simplement une valeur du fichier strictement supérieure à zéro. Ce n'est pas un diagnostic d'allergie. L'indicateur `Sensitization` fourni est conservé séparément. »

Montrer le classement, la distribution et la variation selon l'âge. Appliquer une classe d'âge ou une puce, faire constater le nouvel effectif, puis réinitialiser. La heatmap montre des combinaisons individuelles : sa transformation `log1p` rend les amplitudes lisibles ; elle ne change pas la règle de détection.

Ne pas comparer directement des moyennes d'IgE entre plateformes comme si leur calibration était identique. Préférer les fréquences de détection et le périmètre commun pour la démonstration transversale.

## 4:00–6:00 — Relier biologie et informations cliniques

Passer à **Clinique** et choisir **Symptômes cutanés**. Sur la cohorte complète : **1 140 « oui »**, **686 « non »**, **2 445 non renseignés / non pertinents**. La comparaison porte donc sur **1 826 patients**.

Exemple vérifié : **Ara h 2 est détecté chez 27,7 % des patients avec symptômes cutanés contre 8,5 % sans symptômes, soit +19,3 points de pourcentage**. Pour cette mesure, les dénominateurs sont respectivement 1 140 et 686.

« C'est une différence descriptive dans la population observée, pas la preuve d'un mécanisme causal. L'âge, la technologie, le recrutement ou la disponibilité des données peuvent participer à l'écart. »

Changer brièvement de variable clinique pour montrer que l'effectif observé change. Pour un traitement, dire « traitement déclaré », jamais « maladie sévère ». Souligner que le sens des barres correspond aux groupes indiqués sur le graphique.

## 6:00–8:00 — Des groupes exploratoires, sans cible clinique

Passer à **Profils**. Expliquer que seules les **91 mesures IgE communes** construisent les groupes ; les variables cliniques servent ensuite à les décrire. Les **30 patients incomplets** sur ce périmètre sont exclus de cette analyse ; les **4 241 autres** entrent dans la PCA et le clustering, sans imputation.

Présenter la transformation `log1p`, la standardisation **par puce** puis KMeans **dans les 91 dimensions**. Le K proposé est **2**, avec une silhouette de **0,440** calculée sur un même échantillon fixe de 1 500 patients pour tous les K. Les deux groupes rassemblent **3 433 et 808 patients**. Une silhouette est une aide au choix, pas une validation clinique.

PC1 et PC2 expliquent **22,54 %** de la variance au total : le plan n'est qu'une projection partielle. Les modèles sont appris sur la cohorte complète admissible ; filtrer change l'affichage, pas l'apprentissage. Les numéros des groupes ordonnent le nombre moyen de détections, pas la gravité.

Sélectionner un cluster avec le contrôle ou une région au lasso, puis montrer sa signature et la composition par technologie. Pour la solution par défaut, le **V de Cramér puce × cluster vaut 0,010** : faible association globale, sans preuve d'absence de tout effet de plateforme. Le mode de standardisation globale permet de tester la sensibilité à ce choix. La standardisation par technologie peut atténuer aussi de vraies différences de population ; elle ne garantit pas leur harmonisation.

« Ces groupes résument la diversité des IgE. Ils ne sont ni des diagnostics ni une prédiction de la sévérité. »

## 8:00–9:00 — Une comparaison impossible sur une diapositive statique

Passer à **Cohortes**. Réinitialiser. Exclure les âges inconnus pour cette démonstration, choisir **0–17 ans**, enregistrer **A** ; choisir ensuite **18–102 ans**, enregistrer **B**. Comparer effectifs, âge médian, sensibilisation et détections communes.

Montrer la différence de signatures. Une valeur en points de pourcentage est une différence absolue de fréquence, pas un pourcentage d'augmentation. Vérifier le sens A/B dans la légende. Ces deux plages d'âge sont disjointes ; d'autres cohortes peuvent se chevaucher, et l'application doit le signaler.

## 9:00–10:00 — Conclusion et recul critique

« Le parcours transforme une matrice complexe en une exploration reproductible : comprendre les technologies, comparer un périmètre commun, voir les différences cliniques observées, puis construire ses propres cohortes. »

Terminer avec quatre limites :

- Une IgE détectée n'est pas automatiquement une allergie clinique.
- Les informations cliniques manquent pour une part importante de la cohorte.
- Les plateformes gardent des différences de mesure malgré leurs allergènes communs.
- **`Severe_Allergy` est documentée mais absente du CSV** : aucune conclusion directe de sévérité n'est possible avec ce fichier.

## Réponses courtes aux questions probables

**Pourquoi ne pas utiliser les 241 mesures pour tous les patients ?** Parce que les manques sont largement structurels : une puce ne mesure pas tous les allergènes. Les remplir par zéro créerait de faux profils de non-détection.

**Pourquoi le seuil zéro ?** Il définit exactement ce que le fichier permet de compter. Il est présenté comme une détection descriptive et non comme un seuil diagnostique universel.

**Pourquoi ne pas prédire la sévérité ?** La cible n'est pas disponible dans le fichier fourni. Utiliser un traitement ou une somme d'IgE à sa place changerait le sens clinique sans validation.

**Quel est le principal risque d'interprétation ?** Confondre une structure statistique avec une entité clinique, surtout lorsque les patients renseignés diffèrent des autres ou que l'effet de plateforme persiste.

**Comment le projet répond-il aux consignes ?** Il livre un dashboard interactif, une question métier explicite, un parcours de conception argumenté et une critique des limites. Les [consignes du module](brief/Projets.pdf) prévoient aussi un dépôt intermédiaire après trois jours, un quiz théorique et une co-évaluation commentée.
