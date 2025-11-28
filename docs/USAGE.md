# Documentation

## Structure du rapport HTML

Le rapport HTML généré contient :

1. **En-tête** : Nom du dossier analysé et date/heure
2. **Statistiques** : 4 cartes avec les métriques clés
3. **Répartition** : Barres de distribution par niveau
4. **Tableau** : Liste détaillée de tous les fichiers
5. **Erreurs** : Liste des fichiers non analysés (si applicable)

## Niveaux de référence

### Pour du contenu voix/podcast/conférence

| Niveau cible | Usage |
|--------------|-------|
| -24 dB | Standard broadcast, YouTube |
| -30 dB | Conservateur, évite l'écrêtage |
| -19 dB | Spotify (loudness normalization) |

### Pour de la musique

| Niveau cible | Usage |
|--------------|-------|
| -14 dB | Spotify, Apple Music |
| -16 dB | Amazon Music |
| -24 dB | YouTube Music |

## Algorithme de détection

Le script utilise le filtre `volumedetect` de FFmpeg qui analyse :
- **mean_volume** : Niveau RMS moyen sur toute la durée
- **max_volume** : Pic le plus élevé détecté

## Correction audio

### Normalisation
Calcul : `gain = cible - niveau_moyen_actuel`

Exemple : Fichier à -40 dB, cible -24 dB → gain de +16 dB

### Boost
Applique un gain fixe identique à tous les fichiers.

⚠️ Attention à l'écrêtage si le niveau max + boost > 0 dB
