import feedparser
import requests
from datetime import datetime, timedelta
import pandas as pd
import json
import os
from typing import List, Dict

class NewsCollector:
    def __init__(self):
        # RSS feed gratuiti di fonti affidabili
        self.rss_feeds = {
            'reuters_world': 'https://feeds.reuters.com/reuters/worldNews',
            'bbc_world': 'http://feeds.bbci.co.uk/news/world/rss.xml',
            'ap_world': 'https://rsshub.app/ap/topics/world-news',
            'dw_world': 'https://rss.dw.com/xml/rss-en-world',
            'france24': 'https://www.france24.com/en/rss',
            'aljazeera': 'https://www.aljazeera.com/xml/rss/all.xml'
        }
        
        # Parole chiave per tensioni geopolitiche
        self.tension_keywords = [
            'war', 'conflict', 'military', 'sanctions', 'diplomacy',
            'tension', 'crisis', 'attack', 'threat', 'invasion',
            'protest', 'revolution', 'coup', 'border', 'dispute',
            'missile', 'nuclear', 'terror', 'violence', 'strike'
        ]
        
        # Paesi e regioni da monitorare
        self.regions = [
            'ukraine', 'russia', 'china', 'taiwan', 'israel',
            'palestine', 'iran', 'north korea', 'syria', 'afghanistan',
            'myanmar', 'belarus', 'georgia', 'armenia', 'azerbaijan'
        ]
    
    def collect_news(self, hours_back: int = 24) -> List[Dict]:
        """Raccoglie notizie dalle ultime ore specificate"""
        all_articles = []
        cutoff_time = datetime.now() - timedelta(hours=hours_back)
        
        for source, url in self.rss_feeds.items():
            try:
                print(f"Collecting from {source}...")
                feed = feedparser.parse(url)
                
                for entry in feed.entries:
                    # Parsing della data
                    try:
                        if hasattr(entry, 'published_parsed'):
                            article_time = datetime(*entry.published_parsed[:6])
                        elif hasattr(entry, 'updated_parsed'):
                            article_time = datetime(*entry.updated_parsed[:6])
                        else:
                            article_time = datetime.now()
                    except:
                        article_time = datetime.now()
                    
                    # Filtra solo articoli recenti
                    if article_time >= cutoff_time:
                        article = {
                            'source': source,
                            'title': entry.get('title', ''),
                            'description': entry.get('summary', ''),
                            'link': entry.get('link', ''),
                            'published': article_time.isoformat(),
                            'tension_score': self._calculate_tension_score(
                                entry.get('title', '') + ' ' + entry.get('summary', '')
                            )
                        }
                        all_articles.append(article)
                        
            except Exception as e:
                print(f"Error collecting from {source}: {e}")
                continue
        
        return all_articles
    
    def _calculate_tension_score(self, text: str) -> float:
        """Calcola un punteggio di tensione basato su parole chiave"""
        text_lower = text.lower()
        
        # Punteggio base per parole chiave di tensione
        tension_score = 0
        for keyword in self.tension_keywords:
            if keyword in text_lower:
                tension_score += 1
        
        # Punteggio aggiuntivo per regioni sensibili
        region_score = 0
        for region in self.regions:
            if region in text_lower:
                region_score += 2
        
        # Normalizza il punteggio (0-10)
        total_score = min(10, (tension_score + region_score) / 2)
        return round(total_score, 2)
    
    def save_to_json(self, articles: List[Dict], filename: str = None):
        """Salva gli articoli in un file JSON"""
        if filename is None:
            filename = f"data/raw/news_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(articles, f, ensure_ascii=False, indent=2)
        
        print(f"Saved {len(articles)} articles to {filename}")
        return filename

def main():
    collector = NewsCollector()
    articles = collector.collect_news(hours_back=24)
    filename = collector.save_to_json(articles)
    
    # Mostra statistiche
    if articles:
        df = pd.DataFrame(articles)
        print(f"\nCollected {len(articles)} articles")
        print(f"Average tension score: {df['tension_score'].mean():.2f}")
        print(f"Max tension score: {df['tension_score'].max():.2f}")
        print(f"Sources: {df['source'].nunique()}")

if __name__ == "__main__":
    main()
