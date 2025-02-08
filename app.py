import streamlit as st
import pandas as pd
from pathlib import Path
import json
from datetime import datetime
from pivot_plotter_pro.core.pivot_calculator import PivotCalculator, OHLC
from pivot_plotter_pro.data.yahoo_client import YahooClient
from pivot_plotter_pro.data.database import Database
import os

# Konfiguration
st.set_page_config(
    page_title="Pivot Plotter Pro",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS für kompaktes Layout
st.markdown("""
<style>
    .main > div {
        padding-top: 1rem;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        padding: 4px 8px;
    }
    div[data-testid="stVerticalBlock"] > div:has(div.element-container) {
        padding: 0.1rem;
    }
    div[data-testid="stMetric"] {
        padding: 0.1rem;
    }
</style>
""", unsafe_allow_html=True)

# Datenbankpfad aus Umgebungsvariable oder Standard
DB_PATH = os.getenv('DATABASE_PATH', 'data/pivot_plotter.db')
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

# Session State Initialisierung
if 'yahoo_client' not in st.session_state:
    st.session_state.yahoo_client = YahooClient()
if 'db' not in st.session_state:
    st.session_state.db = Database(DB_PATH)

TIMEFRAME_LABELS = {
    "1d": "Tag",
    "1w": "Woche",
    "1m": "Monat",
    "3m": "Quartal",
    "6m": "Halbjahr",
    "1y": "Jahr"
}

# Sidebar für Watchlist
with st.sidebar:
    st.header("Watchlist")
    
    # Symbol Input
    col1, col2 = st.columns([3, 1])
    new_symbol = col1.text_input(
        "Symbol",
        placeholder="z.B. AAPL",
        label_visibility="collapsed"
    ).upper()
    
    if col2.button("➕", help="Symbol hinzufügen"):
        watchlist = st.session_state.db.load_watchlist()
        if new_symbol and new_symbol not in watchlist:
            watchlist.append(new_symbol)
            st.session_state.db.save_watchlist(watchlist)
            st.rerun()
    
    # Watchlist Anzeige mit aktuellen Kursen
    st.divider()
    watchlist = st.session_state.db.load_watchlist()
    
    if not watchlist:
        st.info("Keine Symbole in der Watchlist")
    else:
        # Aktuelle Kursdaten für alle Symbole holen
        for symbol in watchlist:
            df = st.session_state.yahoo_client.get_data(symbol, "1d")
            if df is not None and not df.empty:
                last_price = df['Close'].iloc[-1]
                volume = df['Volume'].iloc[-1]
                price_change = (last_price - df['Open'].iloc[0]) / df['Open'].iloc[0] * 100
                
                col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
                
                # Symbol mit Preis
                col1.markdown(f"**{symbol}**")
                
                # Aktueller Kurs mit Änderung
                color = "green" if price_change >= 0 else "red"
                col2.markdown(
                    f"<span style='color: {color}'>{last_price:.2f}</span>",
                    unsafe_allow_html=True
                )
                col3.markdown(
                    f"<span style='color: {color}'>{price_change:+.1f}%</span>",
                    unsafe_allow_html=True
                )
                
                # Löschen Button
                if col4.button("🗑️", key=f"del_{symbol}", help="Symbol entfernen"):
                    watchlist.remove(symbol)
                    st.session_state.db.save_watchlist(watchlist)
                    st.rerun()
                
                # Volumen
                st.caption(f"Vol: {volume:,.0f}")
                st.divider()

# Hauptbereich
if watchlist:
    # Symbol Auswahl in der Sidebar
    with st.sidebar:
        st.divider()
        selected_symbol = st.selectbox(
            "Symbol auswählen",
            watchlist,
            label_visibility="collapsed"
        )
    
    # Hauptbereich in zwei Spalten aufteilen
    col1, col2 = st.columns([1.2, 0.8])
    
    with col1:
        # TradingView Chart
        tradingview_config = {
            "symbol": selected_symbol,
            "interval": "D",
            "timezone": "Europe/Berlin",
            "theme": "dark",
            "style": "1",
            "locale": "de_DE",
            "enable_publishing": False,
            "allow_symbol_change": True,
            "hide_side_toolbar": True,
            "container_id": "tradingview_chart"
        }
        
        html = f"""
        <div class="tradingview-widget-container">
            <div id="tradingview_chart"></div>
            <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
            <script type="text/javascript">
            new TradingView.widget({json.dumps(tradingview_config)});
            </script>
        </div>
        """
        st.components.v1.html(html, height=800)
    
    with col2:
        # Pivot-Punkte für alle Zeiteinheiten
        tabs = st.tabs(list(TIMEFRAME_LABELS.values()))
        
        # Für jede Zeiteinheit
        for (timeframe, df), tab in zip(
            st.session_state.yahoo_client.get_all_timeframes(selected_symbol).items(),
            tabs
        ):
            with tab:
                if df is not None and not df.empty:
                    # Pivot-Analyse durchführen
                    analysis = PivotCalculator.analyze_timeframe(df)
                    current_price = df['Close'].iloc[-1]
                    
                    # Pivot-Punkte in der Datenbank speichern
                    st.session_state.db.save_pivot_points(
                        selected_symbol,
                        timeframe,
                        analysis['standard']['levels'],
                        analysis['demark']['levels']
                    )
                    
                    # Level-Historie speichern
                    for level_type in ['standard', 'demark']:
                        for level_name, (reached, date) in analysis[level_type]['history'].items():
                            if reached:
                                st.session_state.db.save_level_hit(
                                    selected_symbol,
                                    timeframe,
                                    level_type,
                                    level_name,
                                    analysis[level_type]['levels'][level_name],
                                    date
                                )
                    
                    # Level-Hierarchie definieren
                    level_order = [
                        ('R5', None), ('R4', None), ('R3', None), ('R2', None),
                        ('R1', 'R1'), ('P', 'P'), ('S1', 'S1'),
                        ('S2', None), ('S3', None), ('S4', None), ('S5', None)
                    ]
                    
                    # Kompakte Darstellung der Pivot-Punkte
                    for std_level, dm_level in level_order:
                        cols = st.columns([1, 1.5, 1.5])
                        
                        # Level-Name
                        cols[0].markdown(f"**{std_level}**")
                        
                        # Standard Pivot
                        if std_level in analysis['standard']['levels']:
                            std_value = analysis['standard']['levels'][std_level]
                            std_reached, std_date = analysis['standard']['history'][std_level]
                            
                            if std_reached:
                                cols[1].markdown(
                                    f"<span style='color: #10B981'>{std_value:.2f}</span> "
                                    f"({std_date})",
                                    unsafe_allow_html=True
                                )
                            else:
                                cols[1].markdown(f"{std_value:.2f}")
                        else:
                            cols[1].markdown("-")
                        
                        # Demark Pivot
                        if dm_level and dm_level in analysis['demark']['levels']:
                            dm_value = analysis['demark']['levels'][dm_level]
                            dm_reached, dm_date = analysis['demark']['history'][dm_level]
                            
                            if dm_reached:
                                cols[2].markdown(
                                    f"<span style='color: #10B981'>{dm_value:.2f}</span> "
                                    f"({dm_date})",
                                    unsafe_allow_html=True
                                )
                            else:
                                cols[2].markdown(f"{dm_value:.2f}")
                        else:
                            cols[2].markdown("-")
                        
                else:
                    st.error(f"Keine Daten verfügbar für {selected_symbol} ({TIMEFRAME_LABELS[timeframe]})")
    
else:
    st.info("Füge Symbole zur Watchlist hinzu, um zu beginnen.")