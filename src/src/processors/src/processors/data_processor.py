import pandas as pd
import json
import os
from datetime import datetime, timedelta
from typing import List, Dict
import glob

class DataProcessor:
    def __init__(self):
        self.country_keywords = {
            'Russia': ['russia', 'moscow', 'putin', 'kremlin', 'russian'],
            'Ukraine': ['ukraine', 'kyiv', 'kiev', 'zelensky', 'ukrainian'],
            'China': ['china', 'beijing', 'chinese', 'xi jinping', 'taiwan'],
            'USA': ['united states', 'america', 'washington', 'biden', 'american'],
            'Iran': ['iran', 'tehran', 'iranian', 'persian'],
            'Israel': ['israel', 'israeli', 'jerusalem', 'netanyahu'],
            'Palestine': ['palestine', 'palestinian', 'gaza', 'west bank'],
            'North Korea': ['north korea', 'pyongyang', 'kim jong'],
            'Syria': ['syria', 'syrian', 'damascus', 'assad'],
            'Afghanistan': ['afghanistan', 'kabul', 'afghan', 'taliban']
        }
        
        self.severity_weights = {
            'war': 5.0,
            'invasion': 4.5,
            'military': 3.0,
            'sanctions': 3.5,
            'nuclear': 4.0,
            'missile': 3.5,
            'attack': 4.0,
            'crisis': 2.5,
            'tension': 2.0,
            'threat': 2.5,
            'conflict': 3.0,
            'protest': 1.5,
            'diplomacy': 1.0
        }
    
    def load_latest_data(self) -> pd.DataFrame:
        """Carica i dati più recenti da tutti i file JSON"""
        json_files = glob.glob('data/raw/news_*.json')
        
        if not json_files:
            print("No data files found!")
            return pd.DataFrame()
        
        all_articles = []
        for file in json_files:
            with open(file, 'r', encoding='utf-8') as f:
                articles = json.load(f)
                all_articles.extend(articles)
        
        df = pd.DataFrame(all_articles)
        if not df.empty:
            df['published'] = pd.to_datetime(df['published'])
            df = df.sort_values('published', ascending=False)
            # Rimuovi duplicati basati su titolo e source
            df = df.drop_duplicates(subset=['title', 'source'])
        
        return df
    
    def identify_countries(self, text: str) -> List[str]:
        """Identifica i paesi menzionati nel testo"""
        text_lower = text.lower()
        mentioned_countries = []
        
        for country, keywords in self.country_keywords.items():
            for keyword in keywords:
                if keyword in text_lower:
                    mentioned_countries.append(country)
                    break
        
        return list(set(mentioned_countries))  # Rimuovi duplicati
    
    def enhanced_tension_score(self, text: str) -> float:
        """Calcola un punteggio di tensione più sofisticato"""
        text_lower = text.lower()
        score = 0
        
        # Punteggio basato su parole chiave ponderate
        for keyword, weight in self.severity_weights.items():
            if keyword in text_lower:
                score += weight
        
        # Bonus per combinazioni di parole critiche
        critical_combinations = [
            ('military', 'action'),
            ('nuclear', 'threat'),
            ('border', 'conflict'),
            ('economic', 'sanctions'),
            ('diplomatic', 'crisis')
        ]
        
        for combo in critical_combinations:
            if all(word in text_lower for word in combo):
                score += 2.0
        
        # Normalizza il punteggio (0-10)
        return min(10.0, round(score, 2))
    
    def process_articles(self, df: pd.DataFrame) -> pd.DataFrame:
        """Processa gli articoli per l'analisi"""
        if df.empty:
            return df
        
        # Aggiungi colonne per analisi
        df['countries'] = df.apply(
            lambda row: self.identify_countries(row['title'] + ' ' + row['description']), 
            axis=1
        )
        
        df['enhanced_tension_score'] = df.apply(
            lambda row: self.enhanced_tension_score(row['title'] + ' ' + row['description']),
            axis=1
        )
        
        # Aggiungi informazioni temporali
        df['hour'] = df['published'].dt.hour
        df['day_of_week'] = df['published'].dt.dayofweek
        df['date'] = df['published'].dt.date
        
        return df
    
    def create_country_summary(self, df: pd.DataFrame) -> pd.DataFrame:
        """Crea un riassunto per paese"""
        if df.empty:
            return pd.DataFrame()
        
        # Espandi le righe per paese (un articolo può menzionare più paesi)
        country_rows = []
        for _, row in df.iterrows():
            for country in row['countries']:
                country_row = row.copy()
                country_row['country'] = country
                country_rows.append(country_row)
        
        if not country_rows:
            return pd.DataFrame()
        
        country_df = pd.DataFrame(country_rows)
        
        # Raggruppa per paese
        country_summary = country_df.groupby('country').agg({
            'enhanced_tension_score': ['mean', 'max', 'count'],
            'published': 'max'
        }).round(2)
        
        # Flatten column names
        country_summary.columns = ['avg_tension', 'max_tension', 'article_count', 'last_update']
        country_summary = country_summary.reset_index()
        country_summary = country_summary.sort_values('avg_tension', ascending=False)
        
        return country_summary
    
    def create_timeline(self, df: pd.DataFrame) -> pd.DataFrame:
        """Crea una timeline delle tensioni"""
        if df.empty:
            return pd.DataFrame()
        
        # Raggruppa per data
        timeline = df.groupby('date').agg({
            'enhanced_tension_score': ['mean', 'max', 'count'],
            'countries': lambda x: len(set([country for sublist in x for country in sublist]))
        }).round(2)
        
        timeline.columns = ['avg_tension', 'max_tension', 'article_count', 'countries_mentioned']
        timeline = timeline.reset_index()
        timeline = timeline.sort_values('date')
        
        return timeline
    
    def save_processed_data(self, df: pd.DataFrame, country_summary: pd.DataFrame, timeline: pd.DataFrame):
        """Salva i dati processati"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Salva i dati processati
        df.to_csv(f'data/processed/articles_{timestamp}.csv', index=False)
        country_summary.to_csv(f'data/processed/country_summary_{timestamp}.csv', index=False)
        timeline.to_csv(f'data/processed/timeline_{timestamp}.csv', index=False)
        
        # Salva anche la versione "latest" per facile accesso
        df.to_csv('data/processed/articles_latest.csv', index=False)
        country_summary.to_csv('data/processed/country_summary_latest.csv', index=False)
        timeline.to_csv('data/processed/timeline_latest.csv', index=False)
        
        print(f"Processed data saved:")
        print(f"- Articles: {len(df)}")
        print(f"- Countries: {len(country_summary)}")
        print(f"- Timeline entries: {len(timeline)}")

def main():
    processor = DataProcessor()
    
    # Carica i dati
    df = processor.load_latest_data()
    
    if df.empty:
        print("No data to process!")
        return
    
    # Processa i dati
    df_processed = processor.process_articles(df)
    country_summary = processor.create_country_summary(df_processed)
    timeline = processor.create_timeline(df_processed)
    
    # Salva i risultati
    processor.save_processed_data(df_processed, country_summary, timeline)
    
    # Mostra statistiche
    print(f"\nProcessing complete!")
    print(f"Total articles: {len(df_processed)}")
    print(f"Average tension score: {df_processed['enhanced_tension_score'].mean():.2f}")
    
    if not country_summary.empty:
        print(f"\nTop 5 countries by tension:")
        print(country_summary.head()[['country', 'avg_tension', 'article_count']])

if __name__ == "__main__":
    main()
