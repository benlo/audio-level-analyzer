#!/usr/bin/env python3
"""
Analyseur de niveau sonore pour fichiers MP4
Analyse un fichier unique ou tous les fichiers d'un dossier
Génère un rapport HTML
"""

import subprocess
import sys
import json
import re
import csv
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed


def apply_audio_correction(file_path: str, gain_db: float, output_path: str) -> bool:
    """Applique un gain audio à un fichier."""
    
    cmd = [
        "ffmpeg",
        "-y",  # Overwrite
        "-i", str(file_path),
        "-af", f"volume={gain_db}dB",
        "-c:v", "copy",  # Copie vidéo sans réencodage
        "-c:a", "aac",   # Réencode audio en AAC
        "-b:a", "192k",
        str(output_path)
    ]
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=600
        )
        return result.returncode == 0
    except Exception:
        return False


def analyze_audio_level(file_path: str) -> dict:
    """Analyse le niveau sonore d'un fichier vidéo/audio."""
    
    path = Path(file_path)
    if not path.exists():
        return {"fichier": path.name, "error": "Fichier non trouvé"}
    
    cmd = [
        "ffmpeg",
        "-i", str(file_path),
        "-af", "volumedetect",
        "-vn", "-sn", "-dn",
        "-f", "null", "-"
    ]
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300
        )
        
        stderr = result.stderr
        
        mean_match = re.search(r"mean_volume:\s*([-\d.]+)\s*dB", stderr)
        max_match = re.search(r"max_volume:\s*([-\d.]+)\s*dB", stderr)
        
        if not mean_match or not max_match:
            return {"fichier": path.name, "error": "Pas de piste audio"}
        
        mean_db = float(mean_match.group(1))
        max_db = float(max_match.group(1))
        level = classify_level(mean_db)
        
        return {
            "fichier": path.name,
            "chemin": str(path),
            "niveau_moyen_db": mean_db,
            "niveau_max_db": max_db,
            "classification": level["label"],
            "color": level["color"],
            "emoji": level["emoji"]
        }
        
    except subprocess.TimeoutExpired:
        return {"fichier": path.name, "error": "Timeout"}
    except Exception as e:
        return {"fichier": path.name, "error": str(e)}


def classify_level(mean_db: float) -> dict:
    """
    Classifie le niveau sonore basé sur la moyenne en dB.
    
    Échelle adaptée pour du contenu voix/conférence:
    - Très bas:  < -50 dB (quasi inaudible, problème d'enregistrement)
    - Bas:       -50 à -42 dB (faible, à normaliser)
    - Moyen-:    -42 à -36 dB (acceptable mais faible)
    - Moyen:     -36 à -30 dB (niveau correct pour de la voix)
    - Moyen+:    -30 à -24 dB (bon niveau)
    - Élevé:     > -24 dB (fort, proche broadcast)
    """
    
    if mean_db < -50:
        return {"label": "TRÈS BAS", "color": "#ef4444", "emoji": "🔇"}  # Rouge = problème
    elif mean_db < -42:
        return {"label": "BAS", "color": "#f97316", "emoji": "🔈"}  # Orange
    elif mean_db < -36:
        return {"label": "MOYEN-", "color": "#eab308", "emoji": "🔉"}  # Jaune
    elif mean_db < -30:
        return {"label": "MOYEN", "color": "#22c55e", "emoji": "🔊"}  # Vert = OK
    elif mean_db < -24:
        return {"label": "MOYEN+", "color": "#10b981", "emoji": "🔊"}  # Vert foncé = bien
    else:
        return {"label": "ÉLEVÉ", "color": "#3b82f6", "emoji": "📢"}  # Bleu = fort


def print_progress_bar(current, total, width=50):
    """Affiche une barre de progression."""
    percent = current / total
    filled = int(width * percent)
    bar = "█" * filled + "░" * (width - filled)
    sys.stdout.write(f"\r  ⏳ [{bar}] {current}/{total} ({percent*100:.0f}%)")
    sys.stdout.flush()


def analyze_folder(folder_path: str, extensions: list = None, workers: int = 4) -> list:
    """Analyse tous les fichiers vidéo/audio d'un dossier."""
    
    if extensions is None:
        extensions = [".mp4", ".mkv", ".avi", ".mov", ".webm", ".mp3", ".wav", ".m4a"]
    
    folder = Path(folder_path)
    if not folder.is_dir():
        return [{"error": f"Dossier non trouvé: {folder_path}"}]
    
    # Trouve tous les fichiers
    files = []
    for ext in extensions:
        files.extend(folder.glob(f"*{ext}"))
        files.extend(folder.glob(f"*{ext.upper()}"))
    
    files = sorted(set(files))
    
    if not files:
        return [{"error": f"Aucun fichier trouvé dans {folder_path}"}]
    
    print(f"\n🔍 {len(files)} fichier(s) trouvé(s)")
    print(f"📂 {folder_path}\n")
    
    results = []
    completed = 0
    
    # Analyse parallèle avec barre de progression
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {executor.submit(analyze_audio_level, str(f)): f for f in files}
        
        for future in as_completed(futures):
            result = future.result()
            results.append(result)
            completed += 1
            print_progress_bar(completed, len(files))
    
    print("\n")  # Nouvelle ligne après la barre
    
    # Trie par nom de fichier
    results.sort(key=lambda x: x.get('fichier', ''))
    
    return results


def generate_html_report(results: list, folder_path: str, output_path: str):
    """Génère un rapport HTML."""
    
    valid_results = [r for r in results if 'error' not in r]
    errors = [r for r in results if 'error' in r]
    
    # Statistiques
    if valid_results:
        means = [r['niveau_moyen_db'] for r in valid_results]
        avg_mean = sum(means) / len(means)
        min_mean = min(means)
        max_mean = max(means)
        
        # Répartition
        levels_count = {}
        for r in valid_results:
            lvl = r['classification']
            levels_count[lvl] = levels_count.get(lvl, 0) + 1
    else:
        avg_mean = min_mean = max_mean = 0
        levels_count = {}
    
    # Génération HTML
    html = f'''<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Rapport Audio - {Path(folder_path).name}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            min-height: 100vh;
            color: #e4e4e7;
            padding: 2rem;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
        }}
        h1 {{
            font-size: 2rem;
            margin-bottom: 0.5rem;
            color: #fff;
        }}
        .subtitle {{
            color: #a1a1aa;
            margin-bottom: 2rem;
        }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1rem;
            margin-bottom: 2rem;
        }}
        .stat-card {{
            background: rgba(255,255,255,0.05);
            border-radius: 12px;
            padding: 1.5rem;
            border: 1px solid rgba(255,255,255,0.1);
        }}
        .stat-value {{
            font-size: 2rem;
            font-weight: bold;
            color: #fff;
        }}
        .stat-label {{
            color: #a1a1aa;
            font-size: 0.875rem;
            margin-top: 0.25rem;
        }}
        .section {{
            background: rgba(255,255,255,0.03);
            border-radius: 12px;
            padding: 1.5rem;
            margin-bottom: 1.5rem;
            border: 1px solid rgba(255,255,255,0.1);
        }}
        .section-title {{
            font-size: 1.25rem;
            margin-bottom: 1rem;
            color: #fff;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
        }}
        th, td {{
            padding: 0.75rem 1rem;
            text-align: left;
            border-bottom: 1px solid rgba(255,255,255,0.1);
        }}
        th {{
            color: #a1a1aa;
            font-weight: 500;
            font-size: 0.875rem;
            text-transform: uppercase;
        }}
        tr:hover {{
            background: rgba(255,255,255,0.03);
        }}
        .level-badge {{
            display: inline-block;
            padding: 0.25rem 0.75rem;
            border-radius: 9999px;
            font-size: 0.75rem;
            font-weight: 600;
        }}
        .db-value {{
            font-family: 'SF Mono', Monaco, monospace;
            color: #a1a1aa;
        }}
        .db-bar {{
            width: 100px;
            height: 8px;
            background: rgba(255,255,255,0.1);
            border-radius: 4px;
            overflow: hidden;
            display: inline-block;
            vertical-align: middle;
            margin-left: 0.5rem;
        }}
        .db-bar-fill {{
            height: 100%;
            border-radius: 4px;
            transition: width 0.3s;
        }}
        .distribution {{
            display: flex;
            gap: 1rem;
            flex-wrap: wrap;
        }}
        .dist-item {{
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }}
        .dist-bar {{
            height: 24px;
            border-radius: 4px;
            min-width: 30px;
            display: flex;
            align-items: center;
            justify-content: center;
            color: #fff;
            font-weight: 600;
            font-size: 0.875rem;
        }}
        .error-list {{
            color: #f87171;
            font-size: 0.875rem;
            list-style: none;
        }}
        .error-list li {{
            margin: 0.25rem 0;
        }}
        .footer {{
            text-align: center;
            color: #71717a;
            font-size: 0.75rem;
            margin-top: 2rem;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🎬 Rapport d'analyse audio</h1>
        <p class="subtitle">📂 {folder_path}<br>🕐 {datetime.now().strftime("%d/%m/%Y à %H:%M")}</p>
        
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-value">{len(valid_results)}</div>
                <div class="stat-label">Fichiers analysés</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{avg_mean:.1f} dB</div>
                <div class="stat-label">Niveau moyen global</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{min_mean:.1f} dB</div>
                <div class="stat-label">Le plus bas</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{max_mean:.1f} dB</div>
                <div class="stat-label">Le plus fort</div>
            </div>
        </div>
        
        <div class="section">
            <h2 class="section-title">📊 Répartition par niveau</h2>
            <div class="distribution">
'''
    
    level_colors = {
        "TRÈS BAS": "#ef4444",  # Rouge = problème
        "BAS": "#f97316",       # Orange
        "MOYEN-": "#eab308",    # Jaune
        "MOYEN": "#22c55e",     # Vert = OK
        "MOYEN+": "#10b981",    # Vert foncé = bien
        "ÉLEVÉ": "#3b82f6"      # Bleu = fort
    }
    
    for level in ["TRÈS BAS", "BAS", "MOYEN-", "MOYEN", "MOYEN+", "ÉLEVÉ"]:
        count = levels_count.get(level, 0)
        if count > 0:
            width = max(30, count * 20)
            html += f'''
                <div class="dist-item">
                    <span>{level}</span>
                    <div class="dist-bar" style="background: {level_colors[level]}; width: {width}px;">{count}</div>
                </div>
'''
    
    html += '''
            </div>
        </div>
        
        <div class="section">
            <h2 class="section-title">📋 Détail des fichiers</h2>
            <table>
                <thead>
                    <tr>
                        <th>Fichier</th>
                        <th>Niveau moyen</th>
                        <th>Niveau max</th>
                        <th>Classification</th>
                    </tr>
                </thead>
                <tbody>
'''
    
    for r in valid_results:
        # Calcul pourcentage pour la barre (de -50dB à 0dB)
        percent = min(max((r['niveau_moyen_db'] + 50) / 50 * 100, 0), 100)
        
        html += f'''
                    <tr>
                        <td>{r['fichier']}</td>
                        <td>
                            <span class="db-value">{r['niveau_moyen_db']:.1f} dB</span>
                            <div class="db-bar">
                                <div class="db-bar-fill" style="width: {percent}%; background: {r['color']};"></div>
                            </div>
                        </td>
                        <td><span class="db-value">{r['niveau_max_db']:.1f} dB</span></td>
                        <td><span class="level-badge" style="background: {r['color']}20; color: {r['color']};">{r['emoji']} {r['classification']}</span></td>
                    </tr>
'''
    
    html += '''
                </tbody>
            </table>
        </div>
'''
    
    if errors:
        html += '''
        <div class="section">
            <h2 class="section-title">⚠️ Erreurs</h2>
            <ul class="error-list">
'''
        for e in errors:
            html += f'                <li>{e["fichier"]}: {e["error"]}</li>\n'
        
        html += '''
            </ul>
        </div>
'''
    
    html += '''
        <div class="footer">
            Généré par Audio Level Analyzer
        </div>
    </div>
</body>
</html>
'''
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"📄 Rapport HTML: {output_path}")


def export_csv(results: list, output_path: str):
    """Exporte les résultats en CSV."""
    
    valid_results = [r for r in results if 'error' not in r]
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['Fichier', 'Niveau Moyen (dB)', 'Niveau Max (dB)', 'Classification'])
        
        for r in valid_results:
            writer.writerow([
                r['fichier'],
                r['niveau_moyen_db'],
                r['niveau_max_db'],
                r['classification']
            ])
    
    print(f"📊 Export CSV: {output_path}")


def print_summary(results: list):
    """Affiche un résumé court dans le terminal."""
    
    valid_results = [r for r in results if 'error' not in r]
    errors = [r for r in results if 'error' in r]
    
    print("✅ Analyse terminée!")
    print(f"   • {len(valid_results)} fichier(s) analysé(s)")
    if errors:
        print(f"   • {len(errors)} erreur(s)")


def process_corrections(results: list, folder_path: str, mode: str, value: float):
    """Applique les corrections audio (normalize ou boost)."""
    
    valid_results = [r for r in results if 'error' not in r]
    if not valid_results:
        print("❌ Aucun fichier à corriger")
        return
    
    # Crée le dossier de sortie
    folder = Path(folder_path)
    if mode == "normalize":
        output_dir = folder / f"normalized_{int(abs(value))}dB"
    else:
        output_dir = folder / f"boosted_+{int(value)}dB"
    
    output_dir.mkdir(exist_ok=True)
    
    print(f"\n🔧 Correction audio en cours...")
    print(f"   Mode: {'Normalisation vers ' + str(value) + ' dB' if mode == 'normalize' else 'Boost de +' + str(value) + ' dB'}")
    print(f"   Sortie: {output_dir}\n")
    
    success = 0
    errors = 0
    
    for i, r in enumerate(valid_results, 1):
        # Calcul du gain
        if mode == "normalize":
            gain = value - r['niveau_moyen_db']  # Gain pour atteindre la cible
        else:
            gain = value  # Boost fixe
        
        input_path = r['chemin']
        output_path = output_dir / r['fichier']
        
        print_progress_bar(i, len(valid_results))
        
        if apply_audio_correction(input_path, gain, str(output_path)):
            success += 1
        else:
            errors += 1
    
    print(f"\n\n✅ Correction terminée!")
    print(f"   • {success} fichier(s) corrigé(s)")
    if errors:
        print(f"   • {errors} erreur(s)")
    print(f"   📂 {output_dir}")


def main():
    if len(sys.argv) < 2:
        print("""
🎬 Analyseur de niveau sonore

Usage:
  python audio_level_analyzer.py <fichier.mp4>     Analyse un fichier
  python audio_level_analyzer.py <dossier>         Analyse un dossier (génère HTML)
  
Options d'export:
  --csv          Exporte aussi en CSV
  --json         Exporte aussi en JSON
  --no-html      Ne génère pas de rapport HTML

Options de correction audio:
  --normalize TARGET   Normalise vers le niveau cible (ex: --normalize -24)
  --boost GAIN         Applique un boost fixe (ex: --boost 10)

Exemples:
  python audio_level_analyzer.py ./videos/
  python audio_level_analyzer.py ./videos/ --normalize -24
  python audio_level_analyzer.py ./videos/ --boost 15
  python audio_level_analyzer.py ./videos/ --csv --normalize -30
        """)
        sys.exit(1)
    
    target = sys.argv[1]
    path = Path(target)
    
    # Parse des options de correction
    normalize_target = None
    boost_value = None
    
    if "--normalize" in sys.argv:
        idx = sys.argv.index("--normalize")
        if idx + 1 < len(sys.argv):
            try:
                normalize_target = float(sys.argv[idx + 1])
            except ValueError:
                print("❌ Valeur invalide pour --normalize (ex: --normalize -24)")
                sys.exit(1)
    
    if "--boost" in sys.argv:
        idx = sys.argv.index("--boost")
        if idx + 1 < len(sys.argv):
            try:
                boost_value = float(sys.argv[idx + 1])
            except ValueError:
                print("❌ Valeur invalide pour --boost (ex: --boost 10)")
                sys.exit(1)
    
    if path.is_file():
        # Analyse d'un seul fichier
        print(f"\n⏳ Analyse de {path.name}...")
        result = analyze_audio_level(target)
        if 'error' in result:
            print(f"\n❌ Erreur: {result['error']}")
        else:
            print(f"\n✅ {result['fichier']}")
            print(f"   Niveau moyen: {result['niveau_moyen_db']:.1f} dB")
            print(f"   Niveau max:   {result['niveau_max_db']:.1f} dB")
            print(f"   {result['emoji']} {result['classification']}")
            
            # Correction si demandée
            if normalize_target is not None:
                gain = normalize_target - result['niveau_moyen_db']
                output_path = path.parent / f"{path.stem}_normalized{path.suffix}"
                print(f"\n🔧 Normalisation: +{gain:.1f} dB → {normalize_target} dB")
                if apply_audio_correction(target, gain, str(output_path)):
                    print(f"✅ Fichier créé: {output_path}")
                else:
                    print("❌ Erreur lors de la correction")
            
            elif boost_value is not None:
                output_path = path.parent / f"{path.stem}_boosted{path.suffix}"
                print(f"\n🔧 Boost: +{boost_value:.1f} dB")
                if apply_audio_correction(target, boost_value, str(output_path)):
                    print(f"✅ Fichier créé: {output_path}")
                else:
                    print("❌ Erreur lors de la correction")
    
    elif path.is_dir():
        # Analyse d'un dossier
        results = analyze_folder(target)
        print_summary(results)
        
        # Rapport HTML (par défaut)
        if "--no-html" not in sys.argv:
            html_path = path / "audio_report.html"
            generate_html_report(results, str(path), str(html_path))
        
        # Export CSV
        if "--csv" in sys.argv:
            csv_path = path / "audio_levels.csv"
            export_csv(results, str(csv_path))
        
        # Export JSON
        if "--json" in sys.argv:
            json_path = path / "audio_levels.json"
            valid_results = [r for r in results if 'error' not in r]
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(valid_results, f, indent=2, ensure_ascii=False)
            print(f"📋 Export JSON: {json_path}")
        
        # Correction audio
        if normalize_target is not None:
            process_corrections(results, str(path), "normalize", normalize_target)
        elif boost_value is not None:
            process_corrections(results, str(path), "boost", boost_value)
    
    else:
        print(f"❌ Chemin non trouvé: {target}")
        sys.exit(1)


if __name__ == "__main__":
    main()
