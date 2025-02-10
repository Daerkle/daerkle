# Scanner Integration Plan

## Übersicht
Die Scanner-Funktionalität ist als statische HTML-Website im `eodstockscans` Verzeichnis implementiert. Um diese mit der Hauptanwendung zu verbinden, benötigen wir folgende Komponenten:

## Komponenten

### 1. HTTP-Server für Scanner
- Python's eingebauten HTTP-Server nutzen
- Scanner-Website unter Port 8080 servieren
- Server als Hintergrundprozess laufen lassen

### 2. Navigation
- Navbar-Links zur Scanner-URL (http://localhost:8080) aktualisieren
- Responsives Design beibehalten

### 3. Start-Skript
```bash
#!/bin/bash
# Start Scanner HTTP Server im Hintergrund
cd eodstockscans/site && python -m http.server 8080 &
# Start Streamlit App
streamlit run app.py
```

## Implementation
1. Zum Code-Modus wechseln
2. Start-Skript erstellen
3. Navbar aktualisieren mit korrektem Link zum Scanner
4. Test und Validierung der Integration

## Vorteile dieser Lösung
- Einfache Integration der bestehenden Scanner-Website
- Keine Änderungen am Scanner-Code notwendig
- Schnelle Navigation zwischen den Komponenten
- Lokale Entwicklung und Tests möglich