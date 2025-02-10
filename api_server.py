from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from yahoo_client import YahooClient
from pivot_calculator import PivotCalculator
from core.setup_analyzer import analyze_timeframes_setups
from setup_analyzer import SetupAnalyzer, Setup
import uvicorn
from typing import Dict, List, Optional, Any
import pandas as pd
import logging
import sys
import os
from pydantic import BaseModel

# Logging konfigurieren
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('api_server.log')
    ]
)
logger = logging.getLogger(__name__)

app = FastAPI()

# CORS Middleware konfigurieren
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Singleton Instanzen
yahoo_client = YahooClient()

class WatchlistItem(BaseModel):
    symbol: str

@app.get("/api/stock-data")
async def get_stock_data(symbol: str, timeframe: str = "1d"):
    """Holt OHLC-Daten für ein Symbol"""
    logger.debug(f"GET /api/stock-data - symbol: {symbol}, timeframe: {timeframe}")
    
    try:
        df = yahoo_client.get_data(symbol, timeframe)
        logger.debug(f"Dataframe nach get_data für Symbol {symbol}:")
        logger.debug(df)  # Logge das DataFrame Objekt
        
        if df is None or df.empty:
            logger.error(f"Keine Daten gefunden für {symbol}")
            raise HTTPException(status_code=404, detail=f"Keine Daten gefunden für {symbol}")
        
        # DataFrame in das erwartete Format konvertieren
        result = []
        for index, row in df.iterrows():
            try:
                result.append({
                    "time": index.strftime("%Y-%m-%d"),
                    "open": float(row["Open"]),
                    "high": float(row["High"]),
                    "low": float(row["Low"]),
                    "close": float(row["Close"]),
                    "volume": int(row["Volume"])
                })
            except Exception as e:
                logger.error(f"Fehler beim Verarbeiten der Zeile: {row}")
                logger.error(f"Fehlerdetails: {e}")
                continue  # Überspringe diese Zeile und fahre fort
        
        if not result:
            logger.error(f"Keine gültigen Daten für {symbol}")
            raise HTTPException(status_code=404, detail=f"Keine gültigen Daten für {symbol}")
        
        logger.debug(f"Returning {len(result)} datenpunkte für {symbol}")
        return result
        
    except Exception as e:
        logger.error(f"Fehler beim Abrufen der Daten für {symbol}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/pivot-analysis")
async def get_pivot_analysis(symbol: str) -> Dict[str, Any]:
    """Analysiert ein Symbol auf Trading-Setups"""
    logger.debug(f"GET /api/pivot-analysis - symbol: {symbol}")
    
    try:
        # Hole Daten für verschiedene Zeitrahmen
        timeframes = ["1d", "1w", "1m"]
        setups: List[Setup] = []
        
        for timeframe in timeframes:
            df = yahoo_client.get_data(symbol, timeframe)
            if df is not None and not df.empty:
                analyzer = SetupAnalyzer(df, timeframe)
                timeframe_setups = analyzer.analyze_setups()
                setups.extend(timeframe_setups)
        
        # Konvertiere Setups in JSON-serialisierbares Format
        setup_dicts = []
        for setup in setups:
            setup_dict = {
                "type": setup.type.value,
                "subType": setup.sub_type.value,
                "quality": setup.quality.value,
                "entry": setup.entry,
                "stopLoss": setup.stop_loss,
                "target": setup.target,
                "probability": setup.probability,
                "rr": setup.rr,
                "volumeBuzz": setup.volume_buzz,
                "timeframe": setup.timeframe,
                "trendDirection": setup.trend_direction,
                "cluster": setup.cluster,
                "divergence": setup.divergence,
                "repeatedTests": setup.repeated_tests,
                "trailingStop": setup.trailing_stop,
                "additionalTargets": setup.additional_targets,
                "confirmations": setup.confirmations,
                "bestTime": setup.best_time
            }
            setup_dicts.append(setup_dict)
        
        return {
            "symbol": symbol,
            "setups": setup_dicts
        }
        
    except Exception as e:
        logger.error(f"Fehler bei der Setup-Analyse für {symbol}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/pivot-analysis-old")
async def get_pivot_analysis_old(symbol: str):
    """Liefert Pivot-Analyse und Setups für alle Timeframes"""
    logger.debug(f"GET /api/pivot-analysis - symbol: {symbol}")
    timeframes_data = yahoo_client.get_all_timeframes(symbol)
    if not timeframes_data:
        logger.error(f"Keine Daten gefunden für {symbol}")
        raise HTTPException(status_code=404, detail="Keine Daten gefunden")
    
    # Setup-Analyse durchführen
    setups = analyze_timeframes_setups(timeframes_data)
    logger.debug(f"Setup-Analyse für {symbol}: {setups}")
    
    # Pivot-Analyse für jeden Timeframe
    analysis = {}
    for timeframe, df in timeframes_data.items():
        if df is not None and not df.empty:
            timeframe_analysis = PivotCalculator.analyze_timeframe(df)
            logger.debug(f"Pivot-Analyse für {symbol} ({timeframe}): {timeframe_analysis}")
            
            # Format für Frontend anpassen
            analysis[timeframe] = {
                "standard": {
                    "levels": timeframe_analysis["standard"]["levels"],
                    "history": timeframe_analysis["standard"]["history"],
                    "status": timeframe_analysis["standard"]["status"]
                },
                "demark": {
                    "levels": timeframe_analysis["demark"]["levels"],
                    "history": timeframe_analysis["demark"]["history"]
                }
            }
    
    return {
        "setups": setups,
        "pivots": analysis
    }

@app.get("/api/period-info/{timeframe}")
async def get_period_info(timeframe: str):
    """Liefert Informationen zur aktuellen Handelsperiode"""
    logger.debug(f"GET /api/period-info/{timeframe}")
    info = yahoo_client.get_period_info(timeframe)
    logger.debug(f"Period info für {timeframe}: {info}")
    return {"info": info}

def read_watchlist():
    """Liest die Watchlist-Datei"""
    try:
        import json
        with open('watchlist.json', 'r') as f:
            data = json.load(f)
            
        # Stelle sicher, dass wir ein Dict mit symbols key zurückgeben
        if isinstance(data, list):
            watchlist = {"symbols": data}
        elif isinstance(data, dict) and "symbols" in data:
            watchlist = data
        else:
            watchlist = {"symbols": []}
            
        logger.debug(f"Watchlist gelesen: {watchlist}")
        return watchlist
    except FileNotFoundError:
        logger.warning("Watchlist-Datei nicht gefunden, erstelle neue")
        return {"symbols": []}
    except Exception as e:
        logger.error(f"Fehler beim Lesen der Watchlist: {e}")
        raise

def write_watchlist(watchlist):
    """Schreibt die Watchlist-Datei"""
    try:
        import json
        with open('watchlist.json', 'w') as f:
            json.dump(watchlist, f)
        logger.debug(f"Watchlist geschrieben: {watchlist}")
    except Exception as e:
        logger.error(f"Fehler beim Schreiben der Watchlist: {e}")
        raise

@app.get("/api/watchlist")
async def get_watchlist():
    """Gibt die aktuelle Watchlist zurück"""
    logger.debug("GET /api/watchlist")
    try:
        watchlist = read_watchlist()
        return watchlist
    except Exception as e:
        logger.error(f"Fehler in get_watchlist: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/watchlist")
async def add_to_watchlist(item: WatchlistItem):
    """Fügt ein Symbol zur Watchlist hinzu"""
    logger.debug(f"POST /api/watchlist - body: {item}")
    try:
        symbol = item.symbol.upper()
        logger.debug(f"Versuche {symbol} zu validieren")
        
        # Prüfen ob das Symbol bei Yahoo Finance existiert
        df = yahoo_client.get_data(symbol, "1d")
        if df is None:
            logger.error(f"Symbol {symbol} nicht gefunden")
            raise HTTPException(status_code=404, detail=f"Symbol {symbol} nicht gefunden")
    
        logger.debug(f"Dataframe nach get_data für Symbol {symbol}:")
        logger.debug(df)  # Logge das DataFrame Objekt

        watchlist = read_watchlist()
        if symbol not in watchlist["symbols"]:
            watchlist["symbols"].append(symbol)
            write_watchlist(watchlist)
            logger.info(f"Symbol {symbol} zur Watchlist hinzugefügt")
        else:
            logger.debug(f"Symbol {symbol} bereits in Watchlist")
        
        return watchlist
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Fehler in add_to_watchlist: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/watchlist")
async def remove_from_watchlist(item: WatchlistItem):
    """Entfernt ein Symbol aus der Watchlist"""
    logger.debug(f"DELETE /api/watchlist - body: {item}")
    try:
        symbol = item.symbol.upper()
        watchlist = read_watchlist()
        
        if symbol in watchlist["symbols"]:
            watchlist["symbols"].remove(symbol)
            write_watchlist(watchlist)
            logger.info(f"Symbol {symbol} aus Watchlist entfernt")
        else:
            logger.debug(f"Symbol {symbol} nicht in Watchlist gefunden")
        
        return watchlist
    except Exception as e:
        logger.error(f"Fehler in remove_from_watchlist: {e}")
        raise HTTPException(status_code=500, detail=str(e))

def init_watchlist():
    """Initialisiert die Watchlist-Datei wenn sie nicht existiert"""
    try:
        # Stelle sicher, dass das Verzeichnis existiert
        data_dir = os.path.dirname('watchlist.json')
        if data_dir and not os.path.exists(data_dir):
            os.makedirs(data_dir)
            logger.info(f"Verzeichnis erstellt: {data_dir}")
        
        # Erstelle watchlist.json wenn sie nicht existiert
        if not os.path.exists('watchlist.json'):
            write_watchlist({"symbols": []})
            logger.info("Neue Watchlist-Datei initialisiert")
        else:
            logger.debug("Watchlist-Datei existiert bereits")
        
    except Exception as e:
        logger.error(f"Fehler beim Initialisieren der Watchlist: {e}")
        raise

if __name__ == "__main__":
    init_watchlist()
    logger.info("API-Server startet...")
    uvicorn.run(app, host="0.0.0.0", port=8000)