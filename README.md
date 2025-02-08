# Pivot Plotter Pro

Eine Streamlit-App zur Analyse von Pivot-Punkten mit TradingView Integration und historischer Überprüfung.

## Features

- TradingView Charts Integration
- Automatische Berechnung von Standard und Demark Pivot-Punkten
- Unterstützung für verschiedene Zeiteinheiten (Tag bis Jahr)
- Historische Überprüfung von erreichten Levels
- Persistente Datenbank für Watchlist und Level-Historie
- Dockerisierte Deployment-Option

## Lokale Installation

1. Repository klonen:
```bash
git clone https://github.com/yourusername/pivot-plotter-pro.git
cd pivot-plotter-pro
```

2. Python-Abhängigkeiten installieren:
```bash
pip install -r requirements.txt
pip install -e .
```

3. App starten:
```bash
streamlit run app.py
```

## Docker Installation

1. Container bauen und starten:
```bash
docker-compose up --build
```

2. App im Browser öffnen:
```
http://localhost:8501
```

## Cloud Deployment

### Render

1. Neues Web Service auf render.com erstellen
2. GitHub Repository verbinden
3. Build Command: `pip install -r requirements.txt`
4. Start Command: `streamlit run app.py`

### Heroku

1. Heroku CLI installieren
2. Im Projekt-Verzeichnis:
```bash
heroku create pivot-plotter-pro
git push heroku main
```

### DigitalOcean App Platform

1. Neues App erstellen
2. GitHub Repository verbinden
3. Build Command: `pip install -r requirements.txt`
4. Run Command: `streamlit run app.py`

## Umgebungsvariablen

Die App unterstützt folgende Umgebungsvariablen:

```env
STREAMLIT_SERVER_PORT=8501
STREAMLIT_SERVER_ADDRESS=0.0.0.0
DATABASE_PATH=/app/data/pivot_plotter.db
```

## Datenbank

Die App verwendet SQLite für die persistente Speicherung:

- Watchlist
- Berechnete Pivot-Punkte
- Historie der erreichten Levels

Die Datenbank wird automatisch im Verzeichnis `/app/data` erstellt.

## Updates & Wartung

1. Code aktualisieren:
```bash
git pull origin main
```

2. Dependencies aktualisieren:
```bash
pip install -r requirements.txt --upgrade
```

3. Datenbank-Migration (falls nötig):
```bash
python scripts/migrate_db.py
```

## Support

Bei Fragen oder Problemen:
1. GitHub Issues erstellen
2. Pull Requests sind willkommen