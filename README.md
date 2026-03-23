# 🌍 VoxOrbis · Atlas Interactif des Langues du Monde

**VoxOrbis** est une application web qui cartographie plus de 200 langues et dialectes à travers le globe, en croisant linguistique, data science et visualisation de données.

L'idée est née d'un constat simple : mes études en traduction me donnaient la matière (les langues, les familles linguistiques, les statuts de vitalité), et mes compétences en informatique me donnaient les outils pour les modéliser. VoxOrbis est le pont entre les deux · un projet d'Humanités Numériques.

> Toutes les analyses statistiques (K-Means, OLS, Shannon, Pearson, Haversine, Kamada-Kawai) sont implémentées **from scratch**, sans `scikit-learn`, `scipy` ni `networkx`. Uniquement le module `math` de Python.

---

## Ce que fait l'application

### Carte mondiale interactive
Une carte Plotly affiche les 200+ langues sous forme de bulles, dimensionnées par nombre de locuteurs et colorées par famille linguistique. Le hover affiche la fiche complète de chaque langue : famille, script, statut UNESCO, pays, notes historiques.

### Fiches Langues
Chaque entrée du dataset est consultable individuellement avec toutes ses métadonnées : nom, famille, type (langue/dialecte), locuteurs estimés, système d'écriture, coordonnées géographiques, statut de vitalité et une note descriptive.

### Module Statistiques
C'est la partie la plus technique. Le module intègre du clustering K-Means sur les familles linguistiques (implémenté from scratch), une régression linéaire OLS pour modéliser la relation latitude / nombre de locuteurs, l'entropie de Shannon appliquée à la diversité des systèmes d'écriture, des statistiques descriptives complètes (variance, skewness, kurtosis, distributions) et la corrélation de Pearson entre variables numériques.

### Réseau de Similarités
Un graphe force-directed (algorithme Kamada-Kawai, codé à la main) qui visualise les clusters linguistiques et les proximités entre langues. Limité à 120 nœuds pour des raisons de performance · l'algorithme est en O(n³).

### Place-moi ! (Mini-jeu géographique)
10 manches. Une langue s'affiche, il faut cliquer sur la carte pour deviner où elle se parle. Le score est calculé via la formule de Haversine (distance réelle en km). Système de record persistant.

### Timeline
Une frise interactive couvrant 5 000 ans d'histoire linguistique, filtrable par région et par famille.

### Comparateur
Met 2 ou 3 langues côte à côte pour comparer tous leurs attributs : locuteurs, famille, script, statut, géographie.

### Quiz Script
10 questions à choix multiples : un extrait d'écriture s'affiche, il faut deviner la langue correspondante.

### Focus Occitanie
Une section dédiée aux langues du territoire montpelliérain · de l'occitan languedocien au darija, en passant par le catalan nord et le nissard.

---

## Stack technique

| Couche | Outils |
|---|---|
| **Langage** | Python 3 |
| **Data** | Pandas, module `math` (standard library) |
| **Interface** | Streamlit |
| **Visualisation** | Plotly (cartes géospatiales, graphes réseau) |
| **Frontend custom** | HTML5 / CSS3 / JavaScript injectés dans Streamlit |
| **Design** | Glassmorphism dark, animations CSS, curseur custom, effets sonores interactifs |

---

## Architecture

L'application repose sur un fichier unique (`voxorbis.py`) qui gère à la fois le pipeline de données, la logique métier et le rendu visuel.

**Backend / Logique :** routage multi-pages natif via `st.session_state`, persistance des données de session (historique, scores, état des mini-jeux), et tous les algorithmes statistiques et de graphe implémentés sans bibliothèques de haut niveau.

**Frontend :** injection massive de HTML/CSS custom pour dépasser les limitations visuelles de Streamlit, glassmorphism, animations `@keyframes`, composants interactifs dynamiques, et effets sonores (hover/click) via JavaScript injecté dans un `st.components.v1.html`.

---

## Dataset

Les données ont été compilées manuellement à partir de Glottolog 4.8 (Max Planck Institute) pour la classification des familles, Ethnologue 26e édition (SIL International) pour les estimations de locuteurs, l'UNESCO Atlas of the World's Languages in Danger pour les statuts de vitalité, et Wikipedia / littérature académique pour les notes descriptives.

Chaque langue est caractérisée par : nom, famille linguistique, type, nombre de locuteurs (M), coordonnées GPS, pays, région, statut de vitalité, officialité, système d'écriture, et une note.

---

## Limites connues

Les estimations de locuteurs sont approximatives et varient selon les sources (L1 vs L1+L2, comptages officiels vs estimations linguistiques). La classification langue/dialecte est souvent politique autant que linguistique. Le réseau Kamada-Kawai peut freezer sur les machines avec moins de 4 Go de RAM. Les coordonnées géographiques représentent un point central approximatif, pas l'aire réelle de diffusion.

---

## Auteur

**Amar C.C** · Data Science & Visualisation, 2025

---

*VoxOrbis · Glottolog 4.8 · Ethnologue 26e · UNESCO Atlas · SIL International*
