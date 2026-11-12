# Trajectory Analyzer

Outil d'analyse et de visualisation de trajectoires d'aéronefs à partir de fichiers KML.

## Description

Cet outil permet de :
- Charger et parser des fichiers KML contenant des trajectoires avec altitudes
- Comparer deux trajectoires provenant de sources différentes
- Calculer les écarts latéraux (2D) et verticaux (altitude)
- Visualiser les trajectoires en 2D et 3D
- Exporter les résultats d'analyse

## Prérequis

- Python 3.7+
- pip

## Installation

```bash
# Cloner le dépôt
git clone https://github.com/tbouttier/trajetory_analyzer.git
cd trajetory_analyzer

# Installer les dépendances
pip install -r requirements.txt
```

## Utilisation

### Commande de base

```bash
python main.py fichier1.kml fichier2.kml
```

### Options disponibles

```bash
# Afficher les visualisations
python main.py fichier1.kml fichier2.kml --show

# Sauvegarder les résultats dans un dossier
python main.py fichier1.kml fichier2.kml --output mon_dossier

# Sauvegarder tous les graphiques
python main.py fichier1.kml fichier2.kml --save

# Afficher uniquement la visualisation 3D
python main.py fichier1.kml fichier2.kml --3d --show

# Afficher uniquement la visualisation 2D
python main.py fichier1.kml fichier2.kml --2d --show

# Afficher les graphiques d'écarts
python main.py fichier1.kml fichier2.kml --deviations --show

# Exporter les résultats en CSV
python main.py fichier1.kml fichier2.kml --csv

# Tout sauvegarder et afficher
python main.py fichier1.kml fichier2.kml --save --show --csv
```

### Exemple complet

```bash
# Analyser et sauvegarder tous les résultats
python main.py trajectoire_source1.kml trajectoire_source2.kml \
    --output analyse_trajectoire \
    --save \
    --csv \
    --show
```

## Structure du projet

```
trajetory_analyzer/
├── main.py              # Interface en ligne de commande
├── kml_parser.py        # Parsing des fichiers KML
├── analysis.py          # Calcul des écarts entre trajectoires
├── visualization.py     # Visualisation 2D et 3D
├── requirements.txt     # Dépendances Python
└── README.md            # Documentation
```

## Format des fichiers KML

Les fichiers KML doivent contenir des trajectoires avec :
- Coordonnées géographiques (latitude, longitude)
- Altitudes (optionnelles, mais recommandées pour l'analyse complète)
- Noms de trajectoire (optionnels)

L'outil prend en charge :
- `LineString` pour les trajectoires
- `Point` pour les points individuels
- `MultiGeometry` pour les géométries complexes
- `Placemark` avec noms et timestamps

## Sorties

### Fichiers générés

Dans le dossier de sortie (`output/` par défaut) :
- `2d_trajectories.png` - Visualisation 2D des trajectoires
- `3d_trajectories.png` - Visualisation 3D des trajectoires
- `deviations.png` - Graphiques des écarts latéraux et verticaux
- `3d_with_deviations.png` - Visualisation 3D avec lignes de déviation
- `summary.png` - Résumé des métriques de déviation
- `comparison_results.csv` - Résultats numériques (si `--csv`)

### Métriques calculées

- **Écarts latéraux** : Distance horizontale entre points correspondants
- **Écarts verticaux** : Différence d'altitude entre points correspondants
- **Moyenne, Maximum, Minimum, Écart-type** pour chaque type de déviation

## Visualisations

### Visualisation 2D
Affiche les trajectoires superposées sur un plan latitude/longitude.

### Visualisation 3D
Affiche les trajectoires en 3D avec l'altitude comme troisième dimension.
- Chaque trajectoire a sa propre échelle de couleurs basée sur l'altitude
- Permet une comparaison visuelle immédiate

### Visualisation 3D avec déviations
Affiche les deux trajectoires avec des lignes reliant les points correspondants, permettant de voir directement les écarts.

### Graphiques d'écarts
- Courbe des écarts latéraux point par point
- Courbe des écarts verticaux point par point
- Lignes indiquant la moyenne

### Résumé
Barres graphiques montrant les métriques clés de déviation.

## Exemple de fichier KML

```xml
<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
  <Placemark>
    <name>Trajectoire Aéronef 1</name>
    <LineString>
      <coordinates>
        -1.234,45.678,1000
        -1.235,45.679,1050
        -1.236,45.680,1100
      </coordinates>
    </LineString>
  </Placemark>
</kml>
```

## Dépendances

- `fastkml` - Parsing des fichiers KML
- `numpy` - Calculs numériques
- `matplotlib` - Visualisation
- `pandas` - Manipulation des données
- `lxml` - Parsing XML (dépendance de fastkml)
- `scipy` - Fonctions scientifiques (optionnel, pour l'interpolation)

## Contribution

Les contributions sont les bienvenues ! Ouvrez une issue ou une pull request sur GitHub.

## Licence

Ce projet est sous licence MIT.
