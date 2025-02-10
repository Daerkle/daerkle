# Pivot Plotter Pro - Implementierungsplan

## 1. Projektsetup (Tag 1)
- [ ] Python-Projekt mit Poetry initialisieren
- [ ] Abhängigkeiten installieren:
  - streamlit
  - yfinance
  - pandas
  - numpy
  - streamlit-tradingview-components
  - plotly (optional für zusätzliche Visualisierungen)

## 2. Datenmodell & Berechnungen (Tag 2)
- [ ] Klasse für Pivot-Punkt Berechnungen
  - Standard Pivot-Punkte (P, R1-R5, S1-S5)
  - Demark Pivot-Punkte (P, R1, S1)
- [ ] Yahoo Finance Integration
  - Abrufen historischer Daten
  - Unterstützung verschiedener Timeframes
  - Caching-Mechanismus

## 3. Basis-UI (Tag 3)
- [ ] Streamlit App-Layout
- [ ] Watchlist-Komponente
  - CSV/TXT Import/Export
  - Manuelle Eingabe
  - Persistenz (SQLite/JSON)
- [ ] TradingView Chart Integration
  - Symbol-Übergabe
  - Timeframe-Steuerung

## 4. Pivot-Analyse (Tag 4)
- [ ] Implementierung der Analyse-Logik
  - Prüfung auf erreichte Pivot-Punkte
  - Zeiteinheiten-übergreifende Analyse
- [ ] Tabellarische Darstellung
  - Conditional Formatting
  - Farbkodierung für Status
  - Sortier- und Filterfunktionen

## 5. Erweiterte Features (Tag 5)
- [ ] Benachrichtigungen bei Pivot-Punkt Erreichen
- [ ] Export-Funktionen (CSV, Excel)
- [ ] Backtest-Funktionalität
- [ ] Performance-Optimierungen
- [ ] Benutzereinstellungen

## Technische Spezifikationen

### Pivot-Punkt Formeln

```python
def calculate_standard_pivots(high, low, close):
    pivot = (high + low + close) / 3
    
    r1 = (2 * pivot) - low
    r2 = pivot + (high - low)
    r3 = high + 2 * (pivot - low)
    r4 = r3 + (r3 - r2)
    r5 = r4 + (r4 - r3)
    
    s1 = (2 * pivot) - high
    s2 = pivot - (high - low)
    s3 = low - 2 * (high - pivot)
    s4 = s3 - (s2 - s3)
    s5 = s4 - (s3 - s4)
    
    return {
        'P': pivot,
        'R1': r1, 'R2': r2, 'R3': r3, 'R4': r4, 'R5': r5,
        'S1': s1, 'S2': s2, 'S3': s3, 'S4': s4, 'S5': s5
    }

def calculate_demark_pivots(high, low, close, open):
    if close < open:
        x = high + (2 * low) + close
    elif close > open:
        x = (2 * high) + low + close
    else:  # close == open
        x = high + low + (2 * close)
    
    pivot = x / 4
    r1 = (x / 2) - low
    s1 = (x / 2) - high
    
    return {
        'P': pivot,
        'R1': r1,
        'S1': s1
    }
```

### Datenstruktur Watchlist

```python
class WatchlistItem:
    symbol: str
    timeframes: List[str]  # e.g. ["1d", "1w", "1m"]
    last_update: datetime
    pivot_points: Dict[str, Dict]  # timeframe -> pivot calculations
    alerts: List[PivotAlert]
```

### Benutzeroberfläche

#### Hauptlayout
```
+-------------------+
|     Watchlist     |
+-------------------+
|   TradingView     |
|      Chart        |
+-------------------+
|   Pivot-Tabelle   |
+-------------------+
```

#### Pivot-Tabelle
```
| Zeiteinheit | P | R1 | R2 | R3 | R4 | R5 | S1 | S2 | S3 | S4 | S5 |
|-------------|---|----|----|----|----|----|----|----|----|----|----|
| Täglich     | ✓ | ✗  | ✗  | -  | -  | -  | ✓  | ✓  | -  | -  | -  |
| Wöchentlich | ✓ | ✓  | -  | -  | -  | -  | ✗  | ✗  | -  | -  | -  |
| Monatlich   | - | -  | -  | -  | -  | -  | -  | -  | -  | -  | -  |
```
Legende:
- ✓ : Erreicht
- ✗ : Nicht erreicht
- - : Weit entfernt

## Roadmap & Priorisierung

1. **MVP (Minimum Viable Product)**
   - Basis Watchlist
   - TradingView Chart
   - Standard Pivot-Berechnungen
   - Einfache tabellarische Darstellung

2. **Version 1.0**
   - Demark Pivots
   - Erweiterte Watchlist-Funktionen
   - Verbessertes UI/UX
   - Basic Alerting

3. **Version 2.0**
   - Backtest-Funktionalität
   - Erweiterte Analysen
   - Multi-Timeframe-Scanning
   - Export-Funktionen