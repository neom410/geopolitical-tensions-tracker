import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import os
import sys

# Aggiungi il path per importare i moduli
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

def load_data():
    """Carica i dati processati"""
    try:
        articles = pd.read_csv('data/processed/articles_latest.csv')
        countries = pd.read_csv('data/processed/country_summary_latest.csv')
        timeline = pd.read_csv('data/processed/timeline_latest.csv')
        
        # Converti le date
        articles['published'] = pd.to_datetime(articles['published'])
        timeline['date'] = pd.to_datetime(timeline['date'])
        
        return articles, countries, timeline
    except FileNotFoundError:
        st.error("No processed data found. Please run the data collector and processor first.")
        return None, None, None

def create_tension_gauge(avg_tension):
    """Crea un gauge per il livello di tensione globale"""
    fig = go.Figure(go.Indicator(
        mode = "gauge+number+delta",
        value = avg_tension,
        domain = {'x': [0, 1], 'y': [0, 1]},
        title = {'text': "Global Tension Level"},
        delta = {'reference': 5},
        gauge = {
            'axis': {'range': [None, 10]},
            'bar': {'color': "darkblue"},
            'steps': [
                {'range': [0, 3], 'color': "lightgreen"},
                {'range': [3, 6], 'color': "yellow"},
                {'range': [6, 10], 'color': "red"}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': 7
            }
        }
    ))
    
    fig.update_layout(height=300)
    return fig

def create_country_chart(countries):
    """Crea un grafico a barre per i paesi"""
    fig = px.bar(
        countries.head(10), 
        x='country', 
        y='avg_tension',
        color='avg_tension',
        color_continuous_scale='RdYlBu_r',
        title='Top 10 Countries by Average Tension Level'
    )
    
    fig.update_layout(
        xaxis_title="Country",
        yaxis_title="Average Tension Score",
        xaxis={'categoryorder': 'total descending'}
    )
    
    return fig

def create_timeline_chart(timeline):
    """Crea un grafico temporale"""
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=timeline['date'],
        y=timeline['avg_tension'],
        mode='lines+markers',
        name='Average Tension',
        line=dict(color='blue', width=2)
    ))
    
    fig.add_trace(go.Scatter(
        x=timeline['date'],
        y=timeline['max_tension'],
        mode='lines+markers',
        name='Max Tension',
        line=dict(color='red', width=2)
    ))
    
    fig.update_layout(
        title='Tension Levels Over Time',
        xaxis_title='Date',
        yaxis_title='Tension Score',
        hovermode='x unified'
    )
    
    return fig

def create_source_distribution(articles):
    """Crea un grafico della distribuzione delle fonti"""
    source_counts = articles['source'].value_counts()
    
    fig = px.pie(
        values=source_counts.values,
        names=source_counts.index,
        title='News Sources Distribution'
    )
    
    return fig

def main():
    st.set_page_config(
        page_title="Geopolitical Tensions Tracker",
        page_icon="🌍",
        layout="wide"
    )
    
    st.title("🌍 Geopolitical Tensions Tracker")
    st.markdown("Real-time monitoring of global geopolitical tensions using open data sources")
    
    # Carica i dati
    articles, countries, timeline = load_data()
    
    if articles is None:
        st.stop()
    
    # Metriche principali
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Total Articles",
            len(articles),
            delta=f"Last 24h"
        )
    
    with col2:
        avg_tension = articles['enhanced_tension_score'].mean()
        st.metric(
            "Average Tension",
            f"{avg_tension:.2f}",
            delta=f"{avg_tension - 5:.2f}"
        )
    
    with col3:
        max_tension = articles['enhanced_tension_score'].max()
        st.metric(
            "Peak Tension",
            f"{max_tension:.2f}",
            delta="Critical" if max_tension > 7 else "Normal"
        )
    
    with col4:
        countries_count = len(countries)
        st.metric(
            "Countries Monitored",
            countries_count,
            delta=f"Active"
        )
    
    # Gauge di tensione globale
    st.subheader("Global Tension Level")
    fig_gauge = create_tension_gauge(avg_tension)
    st.plotly_chart(fig_gauge, use_container_width=True)
    
    # Layout a due colonne
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Countries by Tension Level")
        if not countries.empty:
            fig_countries = create_country_chart(countries)
            st.plotly_chart(fig_countries, use_container_width=True)
            
            # Tabella dei paesi
            st.subheader("Detailed Country Data")
            st.dataframe(
                countries[['country', 'avg_tension', 'max_tension', 'article_count']],
                use_container_width=True
            )
    
    with col2:
        st.subheader("Timeline Analysis")
        if not timeline.empty:
            fig_timeline = create_timeline_chart(timeline)
            st.plotly_chart(fig_timeline, use_container_width=True)
            
            # Distribuzione delle fonti
            st.subheader("News Sources")
            fig_sources = create_source_distribution(articles)
            st.plotly_chart(fig_sources, use_container_width=True)
    
    # Articoli recenti con alta tensione
    st.subheader("Recent High-Tension Articles")
    high_tension_articles = articles[articles['enhanced_tension_score'] >= 5].head(10)
    
    if not high_tension_articles.empty:
        for _, article in high_tension_articles.iterrows():
            with st.expander(f"[{article['enhanced_tension_score']:.1f}] {article['title'][:100]}..."):
                st.write(f"**Source:** {article['source']}")
                st.write(f"**Published:** {article['published'].strftime('%Y-%m-%d %H:%M')}")
                st.write(f"**Countries:** {', '.join(eval(article['countries']) if isinstance(article['countries'], str) else article['countries'])}")
                st.write(f"**Description:** {article['description'][:300]}...")
                st.write(f"**Link:** {article['link']}")
    else:
        st.info("No high-tension articles found in recent data.")
    
    # Informazioni aggiuntive
    st.sidebar.header("About")
    st.sidebar.info(
        "This dashboard monitors geopolitical tensions using:\n"
        "- RSS feeds from major news sources\n"
        "- Keyword-based tension scoring\n"
        "- Country-specific analysis\n"
        "- Real-time updates"
    )
    
    st.sidebar.header("Data Sources")
    st.sidebar.markdown(
        "- Reuters World News\n"
        "- BBC World News\n"
        "- AP World News\n"
        "- Deutsche Welle\n"
        "- France24\n"
        "- Al Jazeera"
    )
    
    # Footer
    st.sidebar.markdown("---")
    st.sidebar.markdown("Last updated: " + datetime.now().strftime('%Y-%m-%d %H:%M'))

if __name__ == "__main__":
    main()
