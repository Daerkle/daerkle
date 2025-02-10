# Daerkle Trading Analysis

Eine Handelsanalyse-Plattform, die Pivot-Punkte, DeMark-Setups und technische Analysen kombiniert.

## Installation

### Backend (Python)

1. Python-Abhängigkeiten installieren:
```bash
pip install -r requirements.txt
```

2. FastAPI-Server starten:
```bash
python api_server.py
```
Der Server läuft dann auf http://localhost:8000

### Frontend (Next.js)

1. In das Frontend-Verzeichnis wechseln:
```bash
cd daerkle-next
```

2. NPM-Abhängigkeiten installieren:
```bash
npm install
```

3. Frontend-Server starten:
```bash
npm run dev
```
Die Anwendung ist dann unter http://localhost:3000 erreichbar.

## Features

- Echtzeit Kurs-Charts mit TradingView-Integration
- Pivot-Level Analyse:
  - Standard Pivot-Punkte (R1-R5, PP, S1-S5)
  - DeMark Pivot-Punkte
  - Historische Level-Tests
- Setup-Analyse:
  - Long/Short Setups für verschiedene Zeitrahmen
  - DeMark Setup-Status
  - Automatische Setup-Erkennung
- Watchlist:
  - Symbol-Verwaltung
  - Echtzeit-Kurse und Indikatoren
  - Schnelle Navigation

## Komponenten

### Python-Backend

- `api_server.py`: FastAPI-Server für Datenanalyse
- `yahoo_client.py`: Yahoo Finance Integration
- `pivot_calculator.py`: Pivot-Berechnungen
- `core/setup_analyzer.py`: Setup-Analysen
- `core/pivot_base.py`: Basis-Pivot-Funktionen

### Next.js Frontend

- `app/page.tsx`: Hauptseite mit Layout
- `contexts/SymbolContext.tsx`: Symbol-State Management
- `components/`:
  - `Chart.tsx`: TradingView Chart Integration
  - `PivotLevels.tsx`: Pivot-Level Anzeige
  - `SetupList.tsx`: Setup-Übersicht
  - `Watchlist.tsx`: Symbol-Verwaltung

## API-Endpunkte

- `/api/stock-data`: OHLC-Daten
- `/api/pivot-analysis`: Pivot- und Setup-Analyse
- `/api/watchlist`: Watchlist-Verwaltung

## Entwicklung

### Backend erweitern

1. Neue Analysen in `core/` implementieren
2. FastAPI-Endpunkt in `api_server.py` hinzufügen
3. Tests schreiben und ausführen

### Frontend erweitern

1. Neue Komponente in `components/` erstellen
2. Route in `app/` hinzufügen falls nötig
3. API-Integration implementieren
4. TypeScript-Typen definieren

## Known Issues

- Watchlist wird nur beim Start synchronisiert
- Setup-Analyse benötigt mehr historische Daten für präzisere Ergebnisse