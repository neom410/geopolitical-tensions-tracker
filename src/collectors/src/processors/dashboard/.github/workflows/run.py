#!/usr/bin/env python3
"""
Script di avvio rapido per il Geopolitical Tensions Tracker
Uso: python run.py [collect|process|dashboard|all]
"""

import sys
import os
import subprocess
import argparse
from datetime import datetime

def run_command(command, description):
    """Esegue un comando e gestisce gli errori"""
    print(f"\n{'='*50}")
    print(f"🔄 {description}")
    print(f"{'='*50}")
    
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(result.stdout)
        if result.stderr:
            print(f"Warning: {result.stderr}")
        print(f"✅ {description} completato con successo!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Errore in {description}:")
        print(f"Return code: {e.returncode}")
        print(f"Output: {e.stdout}")
        print(f"Error: {e.stderr}")
        return False

def setup_environment():
    """Configura l'ambiente iniziale"""
    print("🚀 Configurazione ambiente...")
    
    # Crea le directory necessarie
    directories = [
        'data/raw',
        'data/processed',
        'data/sources',
        'logs'
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"📁 Directory creata: {directory}")
    
    print("✅ Ambiente configurato!")

def collect_data():
    """Raccoglie i dati dalle fonti"""
    return run_command(
        "cd src/collectors && python news_collector.py",
        "Raccolta dati dalle fonti RSS"
    )

def process_data():
    """Processa i dati raccolti"""
    return run_command(
        "cd src/processors && python data_processor.py",
        "Elaborazione e analisi dei dati"
    )

def run_dashboard():
    """Avvia la dashboard"""
    print("\n🌐 Avvio dashboard...")
    print("La dashboard si aprirà su: http://localhost:8501")
    print("Premi Ctrl+C per fermare la dashboard")
    
    try:
        subprocess.run("cd dashboard && streamlit run app.py", shell=True, check=True)
    except KeyboardInterrupt:
        print("\n👋 Dashboard fermata dall'utente")
    except subprocess.CalledProcessError as e:
        print(f"❌ Errore nell'avvio della dashboard: {e}")

def generate_report():
    """Genera un report testuale"""
    try:
        import pandas as pd
        
        print("\n📊 Generazione report...")
        
        # Carica i dati
        articles = pd.read_csv('data/processed/articles_latest.csv')
        countries = pd.read_csv('data/processed/country_summary_latest.csv')
        timeline = pd.read_csv('data/processed/timeline_latest.csv')
        
        # Genera report
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        report = f"""
GEOPOLITICAL TENSIONS REPORT
Generated: {timestamp}
{'='*60}

📊 SUMMARY STATISTICS
- Total articles analyzed: {len(articles)}
- Countries monitored: {len(countries)}
- Average global tension: {articles['enhanced_tension_score'].mean():.2f}/10
- Peak tension score: {articles['enhanced_tension_score'].max():.2f}/10
- Latest data: {pd.to_datetime(articles['published']).max()}

🌍 TOP 10 COUNTRIES BY TENSION LEVEL
"""
        
        for i, (_, row) in enumerate(countries.head(10).iterrows(), 1):
            status = "🔴" if row['avg_tension'] > 6 else "🟡" if row['avg_tension'] > 3 else "🟢"
            report += f"{i:2d}. {status} {row['country']:<15} {row['avg_tension']:>5.2f}/10 ({row['article_count']} articles)\n"
        
        report += f"""
📈 RECENT TRENDS (Last 7 days)
- Days analyzed: {len(timeline)}
- Trend direction: {'↗️ Rising' if timeline['avg_tension'].iloc[-1] > timeline['avg_tension'].iloc[0] else '↘️ Falling' if len(timeline) > 1 else '➡️ Stable'}
- Peak day: {timeline.loc[timeline['max_tension'].idxmax(), 'date']} ({timeline['max_tension'].max():.2f}/10)

🔥 HIGH-TENSION ARTICLES (Score > 6.0)
"""
        
        high_tension = articles[articles['enhanced_tension_score'] > 6.0].head(5)
        for _, article in high_tension.iterrows():
            countries_str = ', '.join(eval(article['countries']) if isinstance(article['countries'], str) else article['countries'])
            report += f"- [{article['enhanced_tension_score']:.1f}] {article['title'][:80]}...\n"
            report += f"  Countries: {countries_str}\n"
            report += f"  Source: {article['source']} | {pd.to_datetime(article['published']).strftime('%Y-%m-%d %H:%M')}\n\n"
        
        report += f"""
📡 DATA SOURCES
- Reuters World News, BBC World, AP News
- Deutsche Welle, France24, Al Jazeera
- Update frequency: Every 6 hours
- Next update: Automated via GitHub Actions

⚠️  DISCLAIMER
This tool provides automated analysis for monitoring purposes only.
Tension scores are algorithmic estimates, not expert assessments.
"""
        
        # Salva il report
        with open(f'logs/report_{datetime.now().strftime("%Y%m%d_%H%M")}.txt', 'w', encoding='utf-8') as f:
            f.write(report)
        
        print(report)
        print(f"📝 Report salvato in logs/")
        
    except FileNotFoundError:
        print("❌ Nessun dato trovato. Esegui prima la raccolta e l'elaborazione dei dati.")
    except Exception as e:
        print(f"❌ Errore nella generazione del report: {e}")

def main():
    parser = argparse.ArgumentParser(description='Geopolitical Tensions Tracker')
    parser.add_argument(
        'action', 
        choices=['collect', 'process', 'dashboard', 'report', 'all', 'setup'],
        help='Azione da eseguire'
    )
    parser.add_argument(
        '--hours', 
        type=int, 
        default=24, 
        help='Ore di dati da raccogliere (default: 24)'
    )
    
    args = parser.parse_args()
    
    print("🌍 GEOPOLITICAL TENSIONS TRACKER")
    print("=" * 50)
    
    if args.action == 'setup':
        setup_environment()
        
    elif args.action == 'collect':
        setup_environment()
        collect_data()
        
    elif args.action == 'process':
        if not os.path.exists('data/raw'):
            print("❌ Nessun dato grezzo trovato. Esegui prima 'collect'.")
            return
        process_data()
        
    elif args.action == 'dashboard':
        if not os.path.exists('data/processed/articles_latest.csv'):
            print("❌ Nessun dato processato trovato. Esegui prima 'collect' e 'process'.")
            return
        run_dashboard()
        
    elif args.action == 'report':
        if not os.path.exists('data/processed/articles_latest.csv'):
            print("❌ Nessun dato processato trovato. Esegui prima 'collect' e 'process'.")
            return
        generate_report()
        
    elif args.action == 'all':
        setup_environment()
        
        if collect_data():
            if process_data():
                generate_report()
                print(f"\n🎉 Pipeline completa eseguita con successo!")
                print(f"💡 Esegui 'python run.py dashboard' per visualizzare i risultati")
            else:
                print("❌ Errore nell'elaborazione dei dati")
        else:
            print("❌ Errore nella raccolta dei dati")

if __name__ == "__main__":
    if len(sys.argv) == 1:
        print("Uso: python run.py [collect|process|dashboard|report|all|setup]")
        print("\nEsempi:")
        print("  python run.py setup      # Configura l'ambiente")
        print("  python run.py collect    # Raccoglie i dati")
        print("  python run.py process    # Elabora i dati")
        print("  python run.py dashboard  # Avvia la dashboard")
        print("  python run.py report     # Genera report testuale")
        print("  python run.py all        # Esegue tutto il pipeline")
    else:
        main()
