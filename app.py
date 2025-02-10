import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
from pathlib import Path
import json
from datetime import datetime
from pivot_calculator import PivotCalculator, OHLC
from yahoo_client import YahooClient
from database import Database
import os
import tempfile
import warnings
from core.pivot_base import check_pivot_status
from core.setup_analyzer import analyze_timeframes_setups
from fastapi import FastAPI, HTTPException
import logging

# Warnungen (z. B. von yfinance) unterdrücken
warnings.filterwarnings('ignore', category=FutureWarning)

# FastAPI App erstellen
app = FastAPI()

# Logger einrichten
logger = logging.getLogger(__name__)

# Seitentitel und Layout setzen
st.set_page_config(
    page_title="Daerkle",
    page_icon="",
    layout="wide"
)

# CSS für ein responsives Layout
st.markdown("""
    <style>
        /* Responsive Base Styles */
        * {
            box-sizing: border-box;
        }
        
        /* Header */
        .app-header {
            font-family: 'Helvetica Neue', sans-serif;
            text-align: center;
            padding: clamp(10px, 3vw, 20px) 0;
            background: linear-gradient(90deg, #1f2937, #4b5563);
            color: white;
            font-size: clamp(1.5em, 4vw, 2em);
            margin-bottom: clamp(10px, 3vw, 20px);
        }

        /* Responsive Grid Settings */
        .stApp {
            max-width: 100% !important;
            padding: 1rem !important;
        }
        /* Responsive Tabellen */
        .pivot-table,
        .setup-table {
            width: 100%;
            font-size: clamp(0.75em, 2vw, 0.9em);
            border-collapse: collapse;
            overflow-x: auto;
            display: block;
        }
        
        @media (max-width: 768px) {
            .pivot-table,
            .setup-table {
                font-size: 0.75em;
            }
            
            .pivot-table th,
            .pivot-table td,
            .setup-table th,
            .setup-table td {
                padding: 4px;
                white-space: nowrap;
            }
            
            /* Horizontales Scrollen für Tabellen auf mobilen Geräten */
            .setup-table,
            .pivot-table {
                max-width: 100vw;
                -webkit-overflow-scrolling: touch;
            }
            
            /* Sticky erste Spalte für bessere Übersicht */
            .pivot-table th:first-child,
            .pivot-table td:first-child,
            .setup-table th:first-child,
            .setup-table td:first-child {
                position: sticky;
                left: 0;
                background: var(--background-color);
                z-index: 1;
            }
        }
        
        .pivot-table {
            line-height: 1.2;
        }
        
        .pivot-table th,
        .pivot-table td {
            padding: 4px 6px;
            text-align: right;
            font-size: 0.9em;
        }
        
        /* Datumsanzeige in Pivot-Tabellen */
        .pivot-date {
            color: #6B7280;
            font-size: 0.7em;
            margin-left: 4px;
            font-feature-settings: "tnum";
        }
        
        .pivot-table th:first-child,
        .pivot-table td:first-child {
            text-align: left;
            font-weight: 500;
        }
        
        /* Pivot-Status Icons */
        .pivot-icon {
            display: inline-block;
            min-width: 16px;
            text-align: center;
            margin-left: 4px;
        }
        
        /* Info-Button Styling */
        .info-button {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 16px;
            height: 16px;
            border-radius: 50%;
            background-color: rgba(99,102,241,0.1);
            color: #6366F1;
            font-size: 12px;
            cursor: help;
            margin-left: 6px;
            border: none;
        }
        
        .info-button:hover {
            background-color: rgba(99,102,241,0.2);
        }
        
        /* Überschriften mit Info-Buttons */
        .header-with-info {
            display: flex;
            align-items: center;
            gap: 6px;
        }
        
        /* Tooltip-Styling */
        .tooltip {
            position: relative;
            display: inline-block;
        }
        
        .tooltip .tooltip-text {
            visibility: hidden;
            background-color: rgba(17, 24, 39, 0.95);
            color: #fff;
            text-align: left;
            padding: 8px 12px;
            border-radius: 6px;
            font-size: 0.8em;
            line-height: 1.4;
            width: 280px;
            position: absolute;
            z-index: 1;
            bottom: 125%;
            left: 50%;
            transform: translateX(-50%);
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
        }
        
        .tooltip:hover .tooltip-text {
            visibility: visible;
        }

        /* Kompakte Darstellung der Pivot-Level */
        .pivot-table tr {
            height: 24px;
        }
        
        .pivot-table tr:hover,
        .setup-table tr:hover {
            background-color: rgba(255,255,255,0.05);
        }
        
        .setup-table th {
            background-color: rgba(255,255,255,0.05);
            padding: clamp(4px, 1vw, 12px);
            text-align: left;
        }
        
        .setup-table td {
            padding: clamp(4px, 1vw, 12px);
            border-bottom: 1px solid rgba(255,255,255,0.1);
        }
        .timeframe-badge {
            display: inline-block;
            padding: 2px 6px;
            border-radius: 4px;
            background-color: rgba(99,102,241,0.1);
            color: #6366F1;
            font-weight: 500;
            font-size: 0.8em;
        }
        /* Responsive Watchlist Buttons */
        div.stButton > button {
            background-color: transparent;
            border: none;
            padding: clamp(4px, 1vw, 8px);
            margin: 0;
            width: 100%;
            text-align: left;
            font-size: clamp(0.8rem, 2vw, 0.9rem);
            cursor: pointer;
            min-height: 44px; /* Touch-freundliche Größe */
        }

        div.stButton > button:hover {
            background-color: rgba(255,255,255,0.1);
        }

        /* Responsiver Watchlist Container */
        .watchlist-row {
            margin-bottom: 1px;
            display: flex;
            align-items: center;
        }

        /* Mobile Anpassungen */
        @media (max-width: 768px) {
            /* Watchlist Styling */
            .watchlist-row {
                flex-direction: row;
                justify-content: space-between;
                padding: 4px;
                background-color: rgba(255,255,255,0.02);
                border-radius: 4px;
            }

            /* Lösch-Button immer sichtbar auf Mobilgeräten */
            button[data-key^="del_"] {
                opacity: 1 !important;
                padding: 8px !important;
                min-width: 44px;
                border-radius: 4px;
            }

            /* Chart Anpassungen */
            .tradingview-widget-container {
                height: 60vh !important;
                min-height: 300px;
            }

            /* Spalten auf volle Breite */
            .stTabs [data-testid="stHorizontalBlock"] {
                flex-direction: column !important;
            }
            .stTabs [data-testid="stHorizontalBlock"] > div {
                width: 100% !important;
            }
        }

        /* Desktop Styling */
        @media (min-width: 769px) {
            button[data-key^="del_"] {
                opacity: 0;
                transition: opacity 0.2s;
            }

            .watchlist-row:hover button[data-key^="del_"] {
                opacity: 1;
            }
        }
    </style>
""", unsafe_allow_html=True)

# ---------------------------
# Funktion zum Rerun (sicherer Fallback)
# ---------------------------
def safe_rerun():
    st.rerun()

# ---------------------------
# Datenbankpfad festlegen
# ---------------------------
if os.getenv('VERCEL_ENV') or os.getenv('STREAMLIT_CLOUD'):
    # Verwende temporäres Verzeichnis für Vercel/Cloud-Deployment
    DB_PATH = os.path.join(tempfile.gettempdir(), 'watchlist.db')
else:
    # Lokaler Entwicklungspfad
    DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'watchlist.db')

# Initialisiere die Datenbank
db = Database(DB_PATH)

# ---------------------------
# Funktionen zur Speicherung des zuletzt geöffneten Symbols
# ---------------------------
LAST_SYMBOL_PATH = os.path.join('data', 'last_symbol.json')
def save_last_symbol(symbol):
    with open(LAST_SYMBOL_PATH, 'w') as f:
        json.dump({"symbol": symbol}, f)
def load_last_symbol():
    if os.path.exists(LAST_SYMBOL_PATH):
        with open(LAST_SYMBOL_PATH, 'r') as f:
            data = json.load(f)
        return data.get("symbol")
    return None

# ---------------------------
# Session State Initialisierung
# ---------------------------
if 'yahoo_client' not in st.session_state:
    st.session_state.yahoo_client = YahooClient()
if 'db' not in st.session_state:
    st.session_state.db = Database(DB_PATH)
if 'selected_symbol' not in st.session_state or st.session_state.selected_symbol is None:
    st.session_state.selected_symbol = load_last_symbol()
if 'active_page' not in st.session_state:
    st.session_state.active_page = 'pivot'

# Navigation CSS und HTML laden
with open('components/nav_bar.css') as f:
    nav_css = f.read()
with open('components/nav_bar.html') as f:
    nav_html = f.read()

# CSS für die Navigation einbinden
st.markdown(f"<style>{nav_css}</style>", unsafe_allow_html=True)

# Navigation anzeigen
st.markdown(nav_html, unsafe_allow_html=True)

def handle_symbol_submit():
    """Behandelt die Symbol-Eingabe."""
    if 'new_symbol' in st.session_state and st.session_state.new_symbol:
        symbol = st.session_state.new_symbol.upper()
        watchlist = st.session_state.db.load_watchlist()
        if symbol and symbol not in watchlist:
            watchlist.append(symbol)
            st.session_state.db.save_watchlist(watchlist)
            st.session_state.new_symbol = ""
            safe_rerun()

TIMEFRAME_LABELS = {
    "1d": "Tag",
    "1w": "Woche",
    "1m": "Monat"
}

# ---------------------------
# Hilfsfunktion zur Erkennung mobiler Geräte
# ---------------------------
def is_mobile():
    # Streamlit bietet keine direkte Möglichkeit zur Geräteerkennung
    # Wir nutzen einen Parameter in der URL als Workaround
    return st.query_params.get("view", "") == "mobile"

# ---------------------------
# Header anzeigen im Hauptbereich
# ---------------------------
# ---------------------------
# Responsives Layout basierend auf Bildschirmbreite
# ---------------------------
# Mobile Layout: Watchlist oben, Hauptinhalt darunter
if is_mobile():
    col_watchlist = st.container()
    col_main = st.container()
else:
    col_main, col_watchlist = st.columns([3, 1])
    if is_mobile():
        col_watchlist = st.container()
        col_main = st.container()
    # Desktop Layout: Hauptinhalt links, Watchlist rechts
    else:
        col_main, col_watchlist = st.columns([3, 1])

# --- RECHTE SPALTE: WATCHLIST ---
with col_watchlist:
    st.markdown("### Watchlist")
    col1, col2 = st.columns([3, 1])
    new_symbol = col1.text_input(
        "Symbol",
        key="new_symbol",
        placeholder="z.B. AAPL",
        label_visibility="collapsed",
        on_change=handle_symbol_submit
    )
    if col2.button("➕", help="Symbol hinzufügen"):
        handle_symbol_submit()
    st.divider()
    watchlist = st.session_state.db.load_watchlist()
    if not watchlist:
        st.info("Keine Symbole in der Watchlist")
    else:
        # Für jeden Eintrag in der Watchlist: Wir umschließen die Zeile in einen Container mit der Klasse "watchlist-row"
        for symbol in watchlist:
            try:
                df = st.session_state.yahoo_client.get_data(symbol, "1d")
                if df is not None and not df.empty:
                    last_price = df['Close'].iloc[-1]
                    price_change = (last_price - df['Open'].iloc[0]) / df['Open'].iloc[0] * 100
                    volume = df['Volume'].iloc[-1]
                    with st.container():
                        st.markdown(f'<div class="watchlist-row">', unsafe_allow_html=True)
                        c1, c2 = st.columns([4, 1])
                        with c1:
                            # Gesamter Eintrag als Button (Symbol, Preis, % und Volumen)
                            if st.button(f"{symbol}\n{last_price:.2f} ({price_change:+.1f}%) Vol: {volume}", key=f"select_{symbol}", help=symbol):
                                st.session_state.selected_symbol = symbol
                                save_last_symbol(symbol)
                                safe_rerun()
                        with c2:
                            # Lösch-Button – wird per CSS nur bei Hover sichtbar
                            if st.button("🗑️", key=f"del_{symbol}"):
                                watchlist.remove(symbol)
                                st.session_state.db.save_watchlist(watchlist)
                                if symbol == st.session_state.selected_symbol:
                                    st.session_state.selected_symbol = None
                                    save_last_symbol(None)
                                safe_rerun()
                        st.markdown("</div>", unsafe_allow_html=True)
            except Exception as e:
                st.error(f"Fehler beim Laden von {symbol}: {str(e)}")

# --- LINKE SPALTE: HAUPTINHALT ---
with col_main:
    if st.session_state.selected_symbol:
        chart_col, pivot_col = st.columns([2.5, 1])
        # Linke Spalte: Chart & Setup-Übersicht
        with chart_col:
            # TradingView-Chart einbetten
            tradingview_config = {
                "symbol": st.session_state.selected_symbol,
                "interval": "D",
                "timezone": "Europe/Berlin",
                "theme": "dark",
                "style": "1",
                "locale": "de_DE",
                "enable_publishing": False,
                "allow_symbol_change": True,
                "hide_side_toolbar": True,
                "container_id": "tradingview_chart",
                "height": "400"
            }
            html = f"""
            <div class="tradingview-widget-container" style="height:400px;">
                <div id="tradingview_chart" style="height:100%;"></div>
                <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
                <script type="text/javascript">
                new TradingView.widget({json.dumps(tradingview_config)});
                </script>
            </div>
            """
            st.components.v1.html(html, height=400)
            
            # DeMark Setup Übersicht
            st.markdown("""
            <div style="margin: 20px 0;">
                <div class="header-with-info">
                    <h4>DeMark Trading Setups</h4>
                    <div class="tooltip">
                        <span class="info-button">?</span>
                        <span class="tooltip-text">
                            <strong>DeMark Trading Setups:</strong><br>
                            • Setup wird aktiv wenn R1/S1 berührt wurde oder der Preis 0.1% darüber/darunter liegt<br>
                            • R2/S2 dienen als Kursziele<br>
                            • ⚑/⚐ markiert wichtige DeMark S1 Levels<br>
                            • ○↑/○↓ zeigt offene, noch nicht getestete Pivot-Punkte<br>
                            • Pivot-Punkte bleiben oft „offen" und werden später getestet
                        </span>
                    </div>
                </div>
                <style>
                    .setup-badge {
                        display: inline-block;
                        padding: 4px 8px;
                        border-radius: 4px;
                        font-weight: 500;
                    }
                    .setup-badge.long {
                        background-color: rgba(16,185,129,0.1);
                        color: #10B981;
                        border: 1px solid rgba(16,185,129,0.2);
                    }
                    .setup-badge.short {
                        background-color: rgba(239,68,68,0.1);
                        color: #EF4444;
                        border: 1px solid rgba(239,68,68,0.2);
                    }
                    .setup-distance {
                        font-weight: bold;
                        padding: 2px 6px;
                        border-radius: 3px;
                    }
                    .setup-distance.positive {
                        background-color: rgba(16,185,129,0.1);
                        color: #10B981;
                    }
                    .setup-distance.negative {
                        background-color: rgba(239,68,68,0.1);
                        color: #EF4444;
                    }
                    .setup-active {
                        position: relative;
                    }
                    .setup-active::before {
                        content: '';
                        position: absolute;
                        left: 0;
                        top: 0;
                        bottom: 0;
                        width: 3px;
                    }
                    .setup-active.long::before {
                        background-color: #10B981;
                    }
                    .setup-active.short::before {
                        background-color: #EF4444;
                    }
                </style>
                <style>
                    .setup-table {
                        width: 100%;
                        table-layout: fixed;
                        border-collapse: collapse;
                    }
                    .setup-table th,
                    .setup-table td {
                        padding: 8px;
                        text-align: center;
                        white-space: nowrap;
                        overflow: hidden;
                        text-overflow: ellipsis;
                        vertical-align: middle;
                        border-bottom: 1px solid rgba(255,255,255,0.1);
                    }
                    /* Zeiteinheit Spalte */
                    .setup-table th:first-child,
                    .setup-table td:first-child {
                        width: 80px;
                        text-align: left;
                        padding-left: 8px;
                    }
                    /* Setup Spalte */
                    .setup-table th:nth-child(2),
                    .setup-table td:nth-child(2) {
                        width: 100px;
                        text-align: left;
                        padding-left: 8px;
                    }
                    /* Trigger und Target Spalten */
                    .setup-table th:nth-child(3),
                    .setup-table td:nth-child(3),
                    .setup-table th:nth-child(4),
                    .setup-table td:nth-child(4) {
                        width: 120px;
                    }
                    /* Status Spalte */
                    .setup-table th:nth-child(5),
                    .setup-table td:nth-child(5) {
                        width: 80px;
                    }
                    /* Distanz Spalte */
                    .setup-table th:nth-child(6),
                    .setup-table td:nth-child(6) {
                        width: 90px;
                    }
                    /* Header Styling */
                    .setup-table th {
                        background-color: rgba(255,255,255,0.05);
                        font-weight: 500;
                        padding: 8px;
                        font-size: 0.9em;
                    }
                    /* Hover Effekt */
                    .setup-table tr:hover {
                        background-color: rgba(255,255,255,0.02);
                    }
                </style>
                <table class="setup-table">
                    <tr>
                        <th>Zeiteinheit</th>
                        <th>Setup</th>
                        <th>Trigger (DeMark)</th>
                        <th>Target (Standard)</th>
                        <th>Status</th>
                        <th>Distanz zum Target</th>
                    </tr>
            """, unsafe_allow_html=True)
            
            # Hole die Daten für alle Zeitrahmen (z. B. Tag, Woche, Monat)
            timeframes_data = st.session_state.yahoo_client.get_all_timeframes(st.session_state.selected_symbol)
            setups_by_timeframe = analyze_timeframes_setups(timeframes_data)
            
            active_setups_found = False
            for timeframe, setups in setups_by_timeframe.items():
                label = TIMEFRAME_LABELS.get(timeframe, timeframe)
                if setups['long']['active']:
                    active_setups_found = True
                    distance_value = float(setups['long']['distance'].rstrip('%'))
                    distance_class = 'positive' if distance_value > 0 else 'negative'
                    st.markdown(f"""
                    <tr class="setup-active long">
                        <td style="text-align: left;"><span class="timeframe-badge">{label}</span></td>
                        <td style="text-align: left;"><span class="setup-badge long">🔼 Long Setup</span></td>
                        <td style="text-align: center;">R1 ({setups['long']['trigger']:.2f})</td>
                        <td style="text-align: center;">R2 ({setups['long']['target']:.2f})</td>
                        <td style="text-align: center;"><span style="color: #10B981">● Aktiv</span></td>
                        <td style="text-align: center;"><span class="setup-distance {distance_class}">{setups['long']['distance']}</span></td>
                    </tr>
                    """, unsafe_allow_html=True)
                if setups['short']['active']:
                    active_setups_found = True
                    distance_value = float(setups['short']['distance'].rstrip('%'))
                    distance_class = 'positive' if distance_value > 0 else 'negative'
                    st.markdown(f"""
                    <tr class="setup-active short">
                        <td style="text-align: left;"><span class="timeframe-badge">{label}</span></td>
                        <td style="text-align: left;"><span class="setup-badge short">🔽 Short Setup</span></td>
                        <td style="text-align: center;">S1 ({setups['short']['trigger']:.2f})</td>
                        <td style="text-align: center;">S2 ({setups['short']['target']:.2f})</td>
                        <td style="text-align: center;"><span style="color: #EF4444">● Aktiv</span></td>
                        <td style="text-align: center;"><span class="setup-distance {distance_class}">{setups['short']['distance']}</span></td>
                    </tr>
                    """, unsafe_allow_html=True)
            if not active_setups_found:
                st.markdown("""
                    <tr>
                        <td colspan="6" style="text-align: center; color: #6B7280; padding: 20px;">
                            Keine aktiven Setups gefunden
                        </td>
                    </tr>
                """, unsafe_allow_html=True)
            st.markdown("</table></div>", unsafe_allow_html=True)
            
        # Pivot-Tabellen und detaillierte Analysen pro Zeitrahmen in der rechten Spalte
        with pivot_col:
            tabs = st.tabs(list(TIMEFRAME_LABELS.values()))
            for (timeframe, df), tab in zip(timeframes_data.items(), tabs):
                with tab:
                    st.markdown(f"#### {st.session_state.yahoo_client.get_period_info(timeframe)}")
                    if df is not None and not df.empty:
                        try:
                            analysis = PivotCalculator.analyze_timeframe(df)
                            current_price = df['Close'].iloc[-1]
                            pivot_status = analysis['standard']['status']
                            # Für den jeweiligen Zeitraum holen wir das Setup (aus unserem Analyzer)
                            setups = setups_by_timeframe.get(timeframe, {
                                'long': {'active': False, 'trigger': 0, 'target': 0, 'distance': ''},
                                'short': {'active': False, 'trigger': 0, 'target': 0, 'distance': ''}
                            })
                            
                            # Anzeige des Standard Pivot Status
                            st.markdown(f"""
                            <div style="padding: 10px; border-radius: 5px; background-color: rgba(255,255,255,0.05); margin-bottom: 10px;">
                                <div class="header-with-info" style="align-items: center;">
                                    <strong>Standard Pivot Status:</strong>
                                    <div class="tooltip">
                                        <span class="info-button">?</span>
                                        <span class="tooltip-text">
                                            <strong>Pivot Status:</strong><br>
                                            • Zeigt die Position zum Standard Pivot-Punkt P<br>
                                            • Grüner Status: Preis über Pivot<br>
                                            • Roter Status: Preis unter Pivot<br>
                                            • Prozent: Abstand zum Pivot-Punkt<br>
                                            • Wichtig für Trendbestimmung
                                        </span>
                                    </div>
                                    <span style="color: {pivot_status['color']}; margin-left: 8px;">
                                        {pivot_status['status']} ({pivot_status['distance']})
                                    </span>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            # Pivot-Tabelle
                            level_order = [
                                ('R5', None), ('R4', None), ('R3', None), ('R2', None),
                                ('R1', 'R1'), ('P', 'P'), ('S1', 'S1'), ('S2', None),
                                ('S3', None), ('S4', None), ('S5', None)
                            ]
                            st.markdown("""
                            <table class="pivot-table">
                                <tr>
                                    <th colspan="3">
                                        <div class="header-with-info" style="justify-content: center; margin-bottom: 8px;">
                                            <span>Pivot-Levels</span>
                                            <div class="tooltip">
                                                <span class="info-button">?</span>
                                                <span class="tooltip-text">
                                                    <strong>Pivot-Levels:</strong><br>
                                                    • Standard: Klassische Pivot-Punkte für Support/Resistance<br>
                                                    • DeMark: Präzisere Berechnung basierend auf Open/Close<br>
                                                    • Graues Datum: Level wurde bereits getestet<br>
                                                    • ○ mit Pfeil: Level wartet auf Test<br>
                                                    • Farbige Markierung: Wichtige Trigger- und Target-Levels
                                                </span>
                                            </div>
                                        </div>
                                    </th>
                                </tr>
                                <tr>
                                    <th>Level</th>
                                    <th>Standard</th>
                                    <th>DeMark</th>
                                </tr>
                            """, unsafe_allow_html=True)
                            rows = []
                            for std_level, dm_level in level_order:
                                row = ['<tr>']
                                is_dm_trigger = ((dm_level == 'R1' and setups['short']['active']) or
                                                 (dm_level == 'S1' and setups['long']['active']))
                                is_std_target = ((std_level == 'R2' and setups['short']['active']) or
                                                 (std_level == 'S2' and setups['long']['active']))
                                level_style = ""
                                # Zeitrahmen-spezifische Farben
                                colors = {
                                    "1d": {"trigger": "#6366F1", "target": "#10B981"},  # Blau/Grün
                                    "1w": {"trigger": "#F59E0B", "target": "#D97706"},  # Orange/Dunkelorange
                                    "1m": {"trigger": "#EC4899", "target": "#BE185D"}   # Pink/Dunkelpink
                                }
                                if is_dm_trigger:
                                    color = colors[timeframe]["trigger"]
                                    level_style = f'background-color: {color}25; border-left: 3px solid {color};'
                                elif is_std_target:
                                    color = colors[timeframe]["target"]
                                    level_style = f'background-color: {color}25; border-right: 3px solid {color};'
                                row.append(f'<td style="{level_style}"><strong>{std_level}</strong></td>')
                                if std_level in analysis['standard']['levels']:
                                    std_value = analysis['standard']['levels'][std_level]
                                    std_reached, std_date, std_status = analysis['standard']['history'][std_level]
                                    if std_reached:
                                        # Level wurde getroffen - zeige Datum klein und in grauer Farbe
                                        row.append(
                                            f'<td style="{level_style}">{std_value:.2f} <span class="pivot-date">{std_date}</span></td>'
                                        )
                                    else:
                                        # Status-Icons für nicht getestete Levels
                                        if '⚑' in std_status or '⚐' in std_status:
                                            # DMS1 Markierung
                                            status_color = '#EC4899'  # Pink für wichtige Marke
                                        elif '○' in std_status:
                                            # Offene wichtige Levels
                                            status_color = '#F59E0B'  # Orange für offene Levels
                                        else:
                                            # Standard Richtungspfeile
                                            status_color = '#6B7280'  # Grau für normale Levels
                                        
                                        icon = f'<span class="pivot-icon" style="color: {status_color}">{std_status}</span>'
                                        row.append(f'<td style="{level_style}">{std_value:.2f} {icon}</td>')
                                else:
                                    row.append(f'<td style="{level_style}">-</td>')
                                if dm_level and dm_level in analysis['demark']['levels']:
                                    dm_value = analysis['demark']['levels'][dm_level]
                                    dm_reached, dm_date, dm_status = analysis['demark']['history'][dm_level]
                                    if dm_reached:
                                        # Level wurde getroffen - zeige Datum klein und in grauer Farbe
                                        row.append(
                                            f'<td style="{level_style}">{dm_value:.2f} <span class="pivot-date">{dm_date}</span></td>'
                                        )
                                    else:
                                        # Status-Icons für DeMark Levels
                                        if '⚑' in dm_status or '⚐' in dm_status:
                                            status_color = '#EC4899'  # Pink für DMS1
                                        elif '○' in dm_status:
                                            status_color = '#F59E0B'  # Orange für offene wichtige Levels
                                        else:
                                            status_color = '#6B7280'  # Grau für normale Richtungspfeile
                                        
                                        icon = f'<span class="pivot-icon" style="color: {status_color}">{dm_status}</span>'
                                        row.append(f'<td style="{level_style}">{dm_value:.2f} {icon}</td>')
                                else:
                                    row.append(f'<td style="{level_style}">-</td>')
                                row.append('</tr>')
                                rows.append(''.join(row))
                            st.markdown(''.join(rows) + '</table>', unsafe_allow_html=True)
                        except Exception as e:
                            st.error(f"Fehler bei der Pivot-Berechnung: {str(e)}")
                    else:
                        st.info("Keine Daten verfügbar für diesen Zeitraum.")
    else:
        st.info("Bitte wähle ein Symbol aus der Watchlist aus.")

@app.get("/api/stock-data")
async def get_stock_data(symbol: str, timeframe: str = "1d"):
    """Gibt die Kursdaten für ein Symbol zurück"""
    logger.debug(f"GET /api/stock-data - symbol: {symbol}, timeframe: {timeframe}")
    try:
        df = st.session_state.yahoo_client.get_data(symbol, timeframe)
        if df is None:
            logger.error(f"Symbol {symbol} nicht gefunden")
            raise HTTPException(status_code=404, detail=f"Symbol {symbol} nicht gefunden")
        
        # DataFrame in eine Liste von Dictionaries umwandeln
        data = []
        for index, row in df.iterrows():
            data.append({
                "date": index.isoformat(),
                "open": float(row["Open"]),
                "high": float(row["High"]),
                "low": float(row["Low"]),
                "close": float(row["Close"]),
                "volume": int(row["Volume"])
            })
        
        return data
    except Exception as e:
        logger.error(f"Fehler in get_stock_data: {e}")
        raise HTTPException(status_code=500, detail=str(e))
