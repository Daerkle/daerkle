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

# Warnungen (z. B. von yfinance) unterdrücken
warnings.filterwarnings('ignore', category=FutureWarning)

# Seitentitel und Layout setzen
st.set_page_config(
    page_title="Daerkle",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded"  # Sidebar standardmäßig eingeblendet
)

# CSS für ein modernes Layout, kompakte Watchlist, Sidebar & Tabellen-Styling
st.markdown("""
    <style>
        /* Header */
        .app-header {
            font-family: 'Helvetica Neue', sans-serif;
            text-align: center;
            padding: 20px 0;
            background: linear-gradient(90deg, #1f2937, #4b5563);
            color: white;
            font-size: 2em;
            margin-bottom: 20px;
        }
        /* Pivot- und Setup-Tabellen */
        .pivot-table {
            width: 100%;
            font-size: 0.9em;
            border-collapse: collapse;
        }
        .pivot-table th,
        .pivot-table td {
            padding: 4px 8px;
            text-align: right;
        }
        .pivot-table th:first-child,
        .pivot-table td:first-child {
            text-align: left;
        }
        .pivot-table tr:hover {
            background-color: rgba(255,255,255,0.05);
        }
        .setup-table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
            font-size: 0.9em;
        }
        .setup-table th {
            background-color: rgba(255,255,255,0.05);
            padding: 8px 12px;
            text-align: left;
        }
        .setup-table td {
            padding: 8px 12px;
            border-bottom: 1px solid rgba(255,255,255,0.1);
        }
        .setup-table tr:hover {
            background-color: rgba(255,255,255,0.02);
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
        /* Kompakte Watchlist-Buttons: Die Symbol-Buttons sind ganz normal klickbar ... */
        div.stButton > button {
            background-color: transparent;
            border: none;
            padding: 4px 8px;
            margin: 0;
            width: 100%;
            text-align: left;
            font-size: 0.9rem;
            cursor: pointer;
        }
        div.stButton > button:hover {
            background-color: rgba(255,255,255,0.1);
        }
        /* Wir fassen jede Zeile in einen Container */
        .watchlist-row {
            margin-bottom: 1px;
        }
        /* Den Lösch-Button (mit Schlüssel "del_") verstecken – er soll nur bei Hover erscheinen */
        button[data-key^="del_"] {
            opacity: 0;
            transition: opacity 0.2s;
        }
        .watchlist-row:hover button[data-key^="del_"] {
            opacity: 1;
        }
    </style>
""", unsafe_allow_html=True)

# ---------------------------
# Funktion zum Rerun (sicherer Fallback)
# ---------------------------
def safe_rerun():
    if hasattr(st, "experimental_rerun"):
        st.experimental_rerun()
    else:
        st._rerun()

# ---------------------------
# Integration der Navigationsleiste in der Sidebar
# ---------------------------
with st.sidebar:
    # Lies HTML und CSS aus dem Ordner "components"
    nav_html_path = os.path.join("components", "nav_bar.html")
    with open(nav_html_path, "r", encoding="utf-8") as f:
        nav_html = f.read()
    nav_css_path = os.path.join("components", "nav_bar.css")
    with open(nav_css_path, "r", encoding="utf-8") as f:
        nav_css = f.read()
    nav_component = f"<style>{nav_css}</style>{nav_html}"
    components.html(nav_component, height=800, scrolling=False)

# ---------------------------
# Datenbankpfad festlegen
# ---------------------------
if os.getenv('STREAMLIT_CLOUD'):
    DB_PATH = os.path.join(tempfile.gettempdir(), 'pivot_plotter.db')
else:
    DB_PATH = os.path.join('data', 'pivot_plotter.db')
    os.makedirs('data', exist_ok=True)

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
# Header anzeigen im Hauptbereich
# ---------------------------
# ---------------------------
# Layout: Hauptinhalt (links) und Watchlist (rechts)
# ---------------------------
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
                <h4>DeMark Trading Setups</h4>
                <p 
                </p>
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
                        <td><span class="timeframe-badge">{label}</span></td>
                        <td><span class="setup-badge long">🔼 Long Setup</span></td>
                        <td>R1 ({setups['long']['trigger']:.2f})</td>
                        <td>R2 ({setups['long']['target']:.2f})</td>
                        <td><span style="color: #10B981">● Aktiv</span></td>
                        <td><span class="setup-distance {distance_class}">{setups['long']['distance']}</span></td>
                    </tr>
                    """, unsafe_allow_html=True)
                if setups['short']['active']:
                    active_setups_found = True
                    distance_value = float(setups['short']['distance'].rstrip('%'))
                    distance_class = 'positive' if distance_value > 0 else 'negative'
                    st.markdown(f"""
                    <tr class="setup-active short">
                        <td><span class="timeframe-badge">{label}</span></td>
                        <td><span class="setup-badge short">🔽 Short Setup</span></td>
                        <td>S1 ({setups['short']['trigger']:.2f})</td>
                        <td>S2 ({setups['short']['target']:.2f})</td>
                        <td><span style="color: #EF4444">● Aktiv</span></td>
                        <td><span class="setup-distance {distance_class}">{setups['short']['distance']}</span></td>
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
                                <strong>Standard Pivot Status:</strong>
                                <span style="color: {pivot_status['color']}">
                                    {pivot_status['status']} ({pivot_status['distance']})
                                </span>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            # Pivot-Tabelle
                            level_order = [
                                ('R5', None), ('R4', None), ('R3', None), ('R2', 'R2'),
                                ('R1', 'R1'), ('P', 'P'), ('S1', 'S1'), ('S2', 'S2'),
                                ('S3', None), ('S4', None), ('S5', None)
                            ]
                            st.markdown("""
                            <table class="pivot-table">
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
                                        row.append(
                                            f'<td style="{level_style}"><span style="color: #10B981">{std_value:.2f}</span> <small>({std_date})</small></td>'
                                        )
                                    else:
                                        # Farbkodierung für nicht getestete Levels
                                        if std_status.endswith('↑'):
                                            # Widerstand wartet auf Test
                                            status_color = '#EC4899'  # Pink
                                        elif std_status.endswith('↓'):
                                            # Unterstützung wartet auf Test
                                            status_color = '#F59E0B'  # Orange
                                        else:
                                            status_color = ''
                                            
                                        if std_status:
                                            row.append(f'<td style="{level_style}">{std_value:.2f} <small style="color: {status_color}">{std_status}</small></td>')
                                        else:
                                            row.append(f'<td style="{level_style}">{std_value:.2f}</td>')
                                else:
                                    row.append(f'<td style="{level_style}">-</td>')
                                if dm_level and dm_level in analysis['demark']['levels']:
                                    dm_value = analysis['demark']['levels'][dm_level]
                                    dm_reached, dm_date, dm_status = analysis['demark']['history'][dm_level]
                                    if dm_reached:
                                        row.append(
                                            f'<td style="{level_style}"><span style="color: #10B981">{dm_value:.2f}</span> <small>({dm_date})</small></td>'
                                        )
                                    else:
                                        # Farbkodierung für nicht getestete Levels
                                        if dm_status.endswith('↑'):
                                            # Widerstand wartet auf Test
                                            status_color = '#EC4899'  # Pink
                                        elif dm_status.endswith('↓'):
                                            # Unterstützung wartet auf Test
                                            status_color = '#F59E0B'  # Orange
                                        else:
                                            status_color = ''
                                            
                                        if dm_status:
                                            row.append(f'<td style="{level_style}">{dm_value:.2f} <small style="color: {status_color}">{dm_status}</small></td>')
                                        else:
                                            row.append(f'<td style="{level_style}">{dm_value:.2f}</td>')
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
