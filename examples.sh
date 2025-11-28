#!/bin/bash
# Exemple d'utilisation du script

# Analyse simple d'un dossier
python audio_level_analyzer.py ./videos/

# Analyse avec export CSV et JSON
python audio_level_analyzer.py ./videos/ --csv --json

# Normalisation vers -24 dB (standard YouTube/broadcast)
python audio_level_analyzer.py ./videos/ --normalize -24

# Boost fixe de +12 dB
python audio_level_analyzer.py ./videos/ --boost 12

# Analyse d'un fichier unique
python audio_level_analyzer.py video.mp4

# Normalisation d'un fichier unique
python audio_level_analyzer.py video.mp4 --normalize -24
