# 🎬 Audio Level Analyzer

Analyseur de niveau sonore pour fichiers vidéo/audio avec génération de rapports HTML et correction automatique du volume.

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![FFmpeg](https://img.shields.io/badge/FFmpeg-required-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

## ✨ Fonctionnalités

- 📊 **Analyse du niveau sonore** (moyenne et pic en dB)
- 📁 **Traitement par lot** de dossiers entiers
- 📄 **Rapport HTML** avec visualisations
- 📈 **Export CSV/JSON** des résultats
- 🔧 **Normalisation audio** vers un niveau cible
- ⬆️ **Boost audio** avec gain fixe
- ⚡ **Traitement parallèle** pour plus de rapidité

## 📋 Prérequis

- Python 3.8+
- FFmpeg

### Installation de FFmpeg

```bash
# Ubuntu/Debian
sudo apt install ffmpeg

# macOS
brew install ffmpeg

# Windows (avec Chocolatey)
choco install ffmpeg
```

## 🚀 Installation

```bash
git clone https://github.com/votre-username/audio-level-analyzer.git
cd audio-level-analyzer
```

Aucune dépendance Python externe requise ! Le script utilise uniquement la bibliothèque standard.

## 📖 Utilisation

### Analyse d'un fichier unique

```bash
python audio_level_analyzer.py video.mp4
```

Sortie :
```
✅ video.mp4
   Niveau moyen: -32.5 dB
   Niveau max:   -8.2 dB
   🔊 MOYEN
```

### Analyse d'un dossier

```bash
python audio_level_analyzer.py ./videos/
```

Génère automatiquement un rapport `audio_report.html` dans le dossier.

### Options d'export

```bash
# Avec export CSV
python audio_level_analyzer.py ./videos/ --csv

# Avec export JSON
python audio_level_analyzer.py ./videos/ --json

# Sans rapport HTML
python audio_level_analyzer.py ./videos/ --no-html
```

### Correction audio

#### Normalisation (recommandé)

Ajuste chaque fichier pour atteindre un niveau cible :

```bash
# Normaliser vers -24 dB (standard broadcast/YouTube)
python audio_level_analyzer.py ./videos/ --normalize -24

# Normaliser vers -30 dB (plus conservateur)
python audio_level_analyzer.py ./videos/ --normalize -30
```

#### Boost fixe

Applique le même gain à tous les fichiers :

```bash
# Augmenter de +10 dB
python audio_level_analyzer.py ./videos/ --boost 10

# Augmenter de +15 dB
python audio_level_analyzer.py ./videos/ --boost 15
```

Les fichiers corrigés sont créés dans un sous-dossier (`normalized_24dB/` ou `boosted_+10dB/`).

## 📊 Échelle de classification

| Niveau | Plage (dB) | Description | Couleur |
|--------|------------|-------------|---------|
| 🔇 TRÈS BAS | < -50 | Quasi inaudible, problème | 🔴 Rouge |
| 🔈 BAS | -50 à -42 | Faible, à normaliser | 🟠 Orange |
| 🔉 MOYEN- | -42 à -36 | Acceptable mais faible | 🟡 Jaune |
| 🔊 MOYEN | -36 à -30 | Correct pour de la voix | 🟢 Vert |
| 🔊 MOYEN+ | -30 à -24 | Bon niveau | 🟢 Vert foncé |
| 📢 ÉLEVÉ | > -24 | Fort, niveau broadcast | 🔵 Bleu |

> 💡 Cette échelle est optimisée pour du contenu voix/conférence. Pour de la musique, les niveaux sont généralement plus élevés.

## 📄 Rapport HTML

Le rapport HTML inclut :

- 📈 Statistiques globales (moyenne, min, max)
- 📊 Graphique de répartition par niveau
- 📋 Tableau détaillé de chaque fichier
- 🎨 Barres de visualisation colorées
- ⚠️ Liste des erreurs éventuelles

![Exemple de rapport](docs/report-example.png)

## 🎯 Cas d'usage

### Préparation de vidéos pour YouTube

```bash
# Analyser et normaliser vers -24 dB (standard YouTube)
python audio_level_analyzer.py ./exports/ --normalize -24 --csv
```

### Contrôle qualité de rushes

```bash
# Générer un rapport pour identifier les fichiers problématiques
python audio_level_analyzer.py ./rushes/
```

### Uniformisation d'enregistrements de conférence

```bash
# Normaliser vers -30 dB pour éviter l'écrêtage
python audio_level_analyzer.py ./conferences/ --normalize -30
```

## 🔧 Formats supportés

**Vidéo** : MP4, MKV, AVI, MOV, WEBM

**Audio** : MP3, WAV, M4A

## 📝 Exemples de sortie

### Terminal

```
🔍 56 fichier(s) trouvé(s)
📂 ./videos/

  ⏳ [██████████████████████████████████████████████████] 56/56 (100%)

✅ Analyse terminée!
   • 56 fichier(s) analysé(s)
📄 Rapport HTML: ./videos/audio_report.html
```

### CSV

```csv
Fichier,Niveau Moyen (dB),Niveau Max (dB),Classification
video_01.mp4,-32.5,-8.2,MOYEN
video_02.mp4,-45.1,-12.3,BAS
video_03.mp4,-28.7,-5.1,MOYEN+
```

## 🤝 Contribution

Les contributions sont les bienvenues ! N'hésitez pas à :

1. Fork le projet
2. Créer une branche (`git checkout -b feature/amelioration`)
3. Commit (`git commit -m 'Ajout de fonctionnalité'`)
4. Push (`git push origin feature/amelioration`)
5. Ouvrir une Pull Request

## 📜 Licence

Ce projet est sous licence MIT. Voir le fichier [LICENSE](LICENSE) pour plus de détails.

## 🙏 Remerciements

- [FFmpeg](https://ffmpeg.org/) pour le traitement audio/vidéo
- Développé avec l'aide de Claude (Anthropic)
