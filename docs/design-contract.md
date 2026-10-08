# Contrat de conception — Allergy Atlas

## Décision et public

**Question :** comment les profils de sensibilisation IgE se structurent-ils dans ACC, et quelles différences observe-t-on selon les manifestations cliniques disponibles ?

Le public visé est un étudiant, analyste ou chercheur qui veut explorer une cohorte, comprendre ses limites de mesure et comparer des sous-populations. L'application accompagne aussi une démonstration orale de dix minutes. Elle ne fournit ni diagnostic ni prédiction de sévérité.

**Choix technique :** Dash relie les filtres, sélections Plotly et cohortes sans imposer de rechargement complet. Plotly fournit survol, zoom et sélection dans un langage graphique cohérent. Python permet de partager les mêmes règles de calcul entre figures et indicateurs. Le supplément de complexité est justifié par le filtrage croisé, la sélection PCA et les cohortes sauvegardées.

## Parcours et budget visuel

Une navigation persistante donne accès à un glossaire « Repères » et à sept chapitres. Un seul chapitre est actif et rendu à la fois ; viser deux à cinq graphiques Plotly simultanés, complétés par de courts textes et indicateurs. Les graphiques répondent chacun à une question explicite.

| Chapitre | Question | Encodage principal et justification |
|---|---|---|
| 01 Vue d'ensemble | Qui est étudié, combien de signaux observe-t-on ? | Histogramme : forme d'une distribution ; barres : effectifs des puces. |
| 02 Mesures | Les patients sont-ils comparables ? | Matrice : couverture structurelle ; barres horizontales : données non renseignées. |
| 03 Sensibilisation | Quels signaux dominent et comment coexistent-ils ? | Barres classées : classement ; histogramme : nombre de détections ; courbe par âge ; heatmap `log1p(IgE)` : motifs. |
| 04 Clinique | Les signatures diffèrent-elles entre groupes observés ? | Barres divergentes : différence de fréquences en points ; barres empilées : composition clinique. |
| 05 Profils | Quels regroupements exploratoires émergent ? | Nuage PCA : proximité projetée ; heatmap : signatures ; barres : surreprésentations et composition par puce. |
| 06 Cohortes | Que change une définition de population ? | Tableau A/B : indicateurs lisibles ; barres divergentes : différences de fréquences. |
| 07 Conclusions | Quelles conclusions les données autorisent-elles ? | Constats chiffrés, limites et provenance ; éviter les graphiques décoratifs. |

## Hiérarchie et identité visuelle

Fond papier légèrement teinté, surfaces blanches, bleu nuit pour structure et texte, turquoise pour actions et accent. Réserver l'orange aux avertissements contextuels ; ne pas coder automatiquement les patients comme « sains » ou « malades » par vert/rouge. Palette qualitative stable pour les trois puces et pour les groupes, avec libellés explicites.

Le titre formule une idée ; le sous-titre explicite le périmètre ; les axes donnent unité et dénominateur. L'interface laisse de l'espace aux graphiques. Pas de 3D, de jauge, de multiplication de camemberts ni d'animation indispensable à la compréhension. Respecter la préférence de réduction des animations.

## Contrat d'interaction

- Le changement d’onglet anime seulement le contenu du chapitre : fondu et léger glissement dans le sens du parcours, avec un soulignement mobile dans le menu. Une modification de filtre ne rejoue pas cette transition. La préférence système de réduction des animations désactive ces effets.

- L'effectif retenu et son pourcentage de la cohorte source restent visibles. Les filtres globaux persistent entre chapitres ; un bouton réinitialise leur état.
- Clic sur une puce, une classe d'âge, un allergène ou un cluster : même action que le contrôle explicite correspondant. Les filtres actifs sont affichés sous forme de pastilles lisibles.
- Sur la PCA, la sélection au lasso ou par rectangle définit un sous-ensemble identifiable ; l'utilisateur doit pouvoir effacer cette sélection.
- Les filtres ont un état de session (`dcc.Store` ou persistance des contrôles). Les cohortes A/B sont conservées localement dans le navigateur via `dcc.Store(storage_type="local")` ; ce stockage n'est pas un compte utilisateur partagé.
- Sauvegarder A ou B fige les patients de la sélection. Signaler leur éventuel chevauchement : deux cohortes construites librement ne sont pas forcément indépendantes.
- Sélectionner un allergène applique explicitement une exigence de détection (> 0) chez les patients ; ce comportement est annoncé près du classement et dans le panneau de filtres.
- Sur petit écran, le panneau de filtres devient un tiroir refermable. Les commandes restent utilisables au clavier, disposent de libellés et d'un focus visible ; aucune étape de l'histoire n'exige exclusivement un clic sur une marque graphique.
- Une sélection vide produit un état explicite et une action de remise à zéro, sans inventer zéro pour une statistique indéfinie.

## Contrat scientifique

- `Sensitization` est une variable fournie. Une IgE « détectée » signifie une valeur valide strictement supérieure à zéro, sans prétendre appliquer un seuil diagnostique.
- Les comparaisons transversales et les profils utilisent les 91 allergènes communs. Couverture d'une puce et valeur valide d'un patient sont deux notions distinctes.
- Les IgE négatives non documentées sont invalides. Un résultat manquant n'est pas remplacé par zéro ; les dénominateurs suivent les mesures disponibles.
- Les traitements décrivent un traitement déclaré, pas la présence certaine ni la gravité d'une maladie. Le code 9 reste non renseigné ; pour les symptômes cutanés il est décrit comme « sans objet/non pertinent » dans le dictionnaire.
- Une fréquence clinique est calculée parmi les patients renseignés, avec effectif observé et taux non renseigné affichés.
- Les comparaisons sont descriptives. Les écarts peuvent refléter âge, recrutement, technologie, disponibilité des informations ou autres facteurs ; ils ne démontrent ni causalité ni valeur prédictive.
- PCA et KMeans n'utilisent que des IgE. Le choix de K, la transformation, l'exclusion des cas incomplets et le contrôle de l'effet puce doivent être expliqués près des résultats.
- `Severe_Allergy` figure dans le dictionnaire général mais pas dans le CSV fourni. Aucune cible de sévérité synthétique n'est créée.

## Vérification et dossier d'évaluation

Vérifier les effectifs sur les fichiers source, le sens des contrastes A/B, la cohérence des dénominateurs, les filtres combinés, la remise à zéro, une cohorte vide, la navigation et l'absence d'erreurs de callbacks. Vérifier visuellement un écran large et un écran mobile : textes, axes, légendes, survols et tiroir ne doivent pas se masquer.

Les [consignes du module](brief/Projets.pdf) demandent de présenter le parcours de conception et d'argumenter l'outil choisi. Elles prévoient également un dépôt intermédiaire après trois jours, un quiz théorique et une co-évaluation commentée. La capacité à critiquer ses choix fait donc partie de la démonstration : expliquer ce qui a été conservé, pourquoi le périmètre commun est nécessaire et ce qui ne peut pas être déduit du jeu ouvert.
