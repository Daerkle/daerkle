# Daerkle

Eine Streamlit-App zur Analyse von Pivot-Punkten mit TradingView Integration und historischer Überprüfung.

## Features

- TradingView Charts Integration
- Automatische Berechnung von Standard und Demark Pivot-Punkten
- Live-Kursdaten und Handelsvolumen in der Watchlist
- Unterstützung für verschiedene Zeiteinheiten (Tag bis Jahr)
- Historische Überprüfung von erreichten Levels
- Persistente Datenbank für Watchlist und Level-Historie

## Installation & Start

### Lokale Installation

1. Repository klonen:
```bash
git clone https://github.com/yourusername/pivot-plotter-pro.git
cd pivot-plotter-pro
```

2. Dependencies installieren:
```bash
pip install -r requirements.txt
```

3. App starten:
```bash
streamlit run app.py
```

### Docker Installation

1. Container bauen und starten:
```bash
docker-compose up --build
```

2. App im Browser öffnen:
```
http://localhost:8501
```

## Streamlit Cloud Deployment

1. Fork dieses Repository auf GitHub

2. Auf [share.streamlit.io](https://share.streamlit.io) gehen:
   - Mit GitHub anmelden
   - "New app" klicken
   - Repository auswählen
   - Branch auswählen (main)
   - Haupt-Python-Datei auswählen (app.py)
   - "Deploy!" klicken

Die App wird automatisch deployed und ist über eine öffentliche URL erreichbar.

## Lokale Entwicklung

### Projektstruktur

```
pivot-plotter-pro/
├── app.py                  # Hauptanwendung
├── requirements.txt        # Python Dependencies
├── .streamlit/
│   └── config.toml        # Streamlit Konfiguration
└── src/
    └── pivot_plotter_pro/
        ├── core/          # Core Funktionalität
        │   └── pivot_calculator.py
        ├── data/          # Datenhandling
        │   ├── database.py
        │   └── yahoo_client.py
        └── utils/         # Hilfsfunktionen
            └── helpers.py
```

### Entwicklungsumgebung

1. Virtual Environment erstellen:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

2. Dependencies installieren:
```bash
pip install -r requirements.txt
```

3. App im Debug-Modus starten:
```bash
streamlit run app.py --server.runOnSave=true
```

## Benutzung

1. Symbole zur Watchlist hinzufügen (z.B. AAPL, MSFT, GOOGL)
2. Symbol aus der Watchlist auswählen
3. TradingView Chart und Pivot-Punkte werden automatisch angezeigt
4. Verschiedene Zeiteinheiten über die Tabs auswählen
5. Erreichte Pivot-Punkte werden grün markiert

## Datenbank

Die App nutzt SQLite für die persistente Speicherung:
- Watchlist
- Berechnete Pivot-Punkte
- Historie der erreichten Levels

Die Datenbank wird automatisch erstellt.

## Updates & Wartung

1. Code aktualisieren:
```bash
git pull origin main
```

2. Dependencies aktualisieren:
```bash
pip install -r requirements.txt --upgrade
```

## Support

Bei Fragen oder Problemen:
1. GitHub Issues erstellen
2. Pull Requests sind willkommen

## Lizenz

MIT License