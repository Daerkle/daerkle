from typing import Dict, List, Optional, Union
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import pytz

class YahooClient:
    """Client für Yahoo Finance API Integration."""
    
    TIMEFRAME_PERIODS = {
        "1d": "1d",     # Tägliche Daten
        "1w": "1wk",    # Wöchentliche Daten
        "1m": "1mo",    # Monatliche Daten
    }
    
    def __init__(self):
        self._cache: Dict[str, Dict[str, pd.DataFrame]] = {}
        self._cache_expiry: Dict[str, Dict[str, datetime]] = {}
        self._cache_duration = {
            "1d": timedelta(minutes=5),    # 5 Minuten Cache für Tagesdaten
            "1w": timedelta(minutes=15),   # 15 Minuten Cache für Wochendaten
            "1m": timedelta(minutes=30),   # 30 Minuten Cache für Monatsdaten
        }
        self.timezone = pytz.timezone('Europe/Berlin')

    def get_last_trading_day(self) -> datetime:
        """Ermittelt den letzten Handelstag."""
        now = datetime.now(self.timezone)
        
        # Wenn heute Sonntag (6) oder Samstag (5)
        if now.weekday() == 6:  # Sonntag
            return (now - timedelta(days=2)).replace(
                hour=0, minute=0, second=0, microsecond=0
            )
        elif now.weekday() == 5:  # Samstag
            return (now - timedelta(days=1)).replace(
                hour=0, minute=0, second=0, microsecond=0
            )
        else:
            # Wenn vor Marktöffnung (15:30 DE Zeit), dann vorheriger Tag
            if now.hour < 15 or (now.hour == 15 and now.minute < 30):
                return (now - timedelta(days=1)).replace(
                    hour=0, minute=0, second=0, microsecond=0
                )
            return now.replace(hour=0, minute=0, second=0, microsecond=0)

    def get_period_info(self, timeframe: str) -> str:
        """Gibt Informationen über die aktuelle Periode zurück."""
        now = datetime.now(self.timezone)
        
        if timeframe == "1d":
            return f"Tag: {now.strftime('%d.%m.%Y')}"
        
        elif timeframe == "1w":
            week_start = (now - timedelta(days=now.weekday()))
            week_end = week_start + timedelta(days=6)
            week_number = now.isocalendar()[1]
            return f"KW {week_number}: {week_start.strftime('%d.%m')} - {week_end.strftime('%d.%m.%Y')}"
        
        else:  # "1m"
            return f"Monat: {now.strftime('%B %Y')}"

    def get_current_period_start(self, timeframe: str) -> datetime:
        """Ermittelt den Start der aktuellen Periode."""
        last_trading_day = self.get_last_trading_day()
        
        if timeframe == "1d":
            # Letzter Handelstag
            return last_trading_day
        
        elif timeframe == "1w":
            # Aktuelle oder letzte vollständige Handelswoche
            week_start = last_trading_day - timedelta(days=last_trading_day.weekday())
            return week_start
        
        else:  # "1m"
            # Aktueller oder letzter vollständiger Handelsmonat
            return last_trading_day.replace(day=1)

    def get_lookback_period(self, timeframe: str) -> str:
        """Bestimmt den Lookback-Zeitraum basierend auf der Zeiteinheit."""
        if timeframe == "1d":
            return "60d"  # Mehr Tage für bessere historische Analyse
        elif timeframe == "1w":
            return "6mo"
        else:  # "1m"
            return "12mo"

    def get_data(
        self, 
        symbol: str, 
        timeframe: str = "1d"
    ) -> Optional[pd.DataFrame]:
        """
        Holt OHLC-Daten von Yahoo Finance mit Caching.
        
        Args:
            symbol: Trading Symbol (z.B. 'AAPL')
            timeframe: Zeiteinheit ('1d', '1w', '1m')
            
        Returns:
            DataFrame mit OHLC-Daten oder None bei Fehler
        """
        # Cache-Check
        if self._is_cache_valid(symbol, timeframe):
            return self._cache[symbol][timeframe]

        try:
            print(f"\nHole Daten für {symbol} ({timeframe})...")
            
            # Yahoo Finance Ticker erstellen
            ticker = yf.Ticker(symbol)
            
            # Startdatum der aktuellen Periode
            period_start = self.get_current_period_start(timeframe)
            lookback = self.get_lookback_period(timeframe)
            
            print(f"Periode start: {period_start}")
            print(f"Lookback: {lookback}")
            
            # Daten abrufen
            df = ticker.history(
                period=lookback,
                interval=self.TIMEFRAME_PERIODS[timeframe]
            )
            
            print(f"Rohdaten Shape: {df.shape}")
            
            # DataFrame aufbereiten
            if not df.empty:
                df = df[['Open', 'High', 'Low', 'Close', 'Volume']]
                # Stelle explizit die Datentypen sicher
                df['Open'] = df['Open'].astype(float)
                df['High'] = df['High'].astype(float)
                df['Low'] = df['Low'].astype(float)
                df['Close'] = df['Close'].astype(float)
                df['Volume'] = df['Volume'].astype(int)
                
                # Berechne die tägliche prozentuale Änderung korrekt
                df['PctChange'] = df['Close'].pct_change() * 100
                
                # Timezone konvertieren
                if df.index.tz is not None:
                    df.index = df.index.tz_convert(self.timezone)
                else:
                    df.index = df.index.tz_localize('UTC').tz_convert(self.timezone)
                
                print(f"Verfügbare Daten Shape: {df.shape}")
                
                if not df.empty:
                    # Debug-Ausgabe der OHLC-Werte
                    print("\nOHLC für Periode:")
                    print(f"Open: {df['Open'].iloc[0]:.2f}")
                    print(f"High: {df['High'].max():.2f}")
                    print(f"Low: {df['Low'].min():.2f}")
                    print(f"Close: {df['Close'].iloc[-1]:.2f}")
                    
                    self._update_cache(symbol, timeframe, df)
                    return df
                else:
                    print("Keine Daten für die aktuelle Periode gefunden")
                    
        except Exception as e:
            print(f"Fehler beim Abrufen der Daten für {symbol}: {str(e)}")
            
        return None

    def get_all_timeframes(
        self,
        symbol: str
    ) -> Dict[str, pd.DataFrame]:
        """
        Holt Daten für alle Zeiteinheiten eines Symbols.
        
        Args:
            symbol: Trading Symbol
            
        Returns:
            Dict mit Zeiteinheit -> DataFrame Zuordnung
        """
        results = {}
        for timeframe in self.TIMEFRAME_PERIODS.keys():
            df = self.get_data(symbol, timeframe)
            if df is not None:
                results[timeframe] = df
        return results

    def _is_cache_valid(self, symbol: str, timeframe: str) -> bool:
        """Prüft ob gecachte Daten noch gültig sind."""
        if (symbol in self._cache_expiry and 
            timeframe in self._cache_expiry[symbol]):
            expiry = self._cache_expiry[symbol][timeframe]
            if datetime.now(self.timezone) < expiry:
                return True
        return False

    def _update_cache(
        self,
        symbol: str,
        timeframe: str,
        data: pd.DataFrame
    ) -> None:
        """Aktualisiert den Cache mit neuen Daten."""
        if symbol not in self._cache:
            self._cache[symbol] = {}
            self._cache_expiry[symbol] = {}
            
        self._cache[symbol][timeframe] = data
        self._cache_expiry[symbol][timeframe] = (
            datetime.now(self.timezone) + self._cache_duration[timeframe]
        )

    def clear_cache(self, symbol: Optional[str] = None) -> None:
        """
        Löscht den Cache für ein Symbol oder den kompletten Cache.
        
        Args:
            symbol: Optional, spezifisches Symbol zum Löschen
        """
        if symbol:
            if symbol in self._cache:
                del self._cache[symbol]
                del self._cache_expiry[symbol]
        else:
            self._cache.clear()
            self._cache_expiry.clear()