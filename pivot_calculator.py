from dataclasses import dataclass
from typing import Dict, List, Literal, Union, Tuple
import pandas as pd
import numpy as np
from datetime import datetime
import pytz

TimeFrame = Literal["1d", "1w", "1m", "3m", "6m", "1y"]
PivotType = Literal["standard", "demark"]

@dataclass
class OHLC:
    open: float
    high: float
    low: float
    close: float
    
    @classmethod
    def from_dataframe(cls, df: pd.DataFrame) -> 'OHLC':
        """Erstellt OHLC aus einem DataFrame."""
        if df.empty:
            raise ValueError("DataFrame ist leer")
            
        try:
            print("\nErstelle OHLC aus DataFrame:")
            print(f"Shape: {df.shape}")
            print(f"Columns: {df.columns.tolist()}")
            print("\nErste und letzte Zeile:")
            print(df.iloc[[0, -1]])
            
            # Berechne OHLC-Werte
            ohlc = cls(
                open=float(df['Open'].iloc[0]),      # Erste Eröffnung
                high=float(df['High'].max()),        # Höchster Wert
                low=float(df['Low'].min()),          # Tiefster Wert
                close=float(df['Close'].iloc[-1])    # Letzter Schlusskurs
            )
            
            # Debug-Ausgabe der berechneten Werte
            print("\nBerechnete OHLC-Werte:")
            print(f"Open:  {ohlc.open:.2f}")
            print(f"High:  {ohlc.high:.2f}")
            print(f"Low:   {ohlc.low:.2f}")
            print(f"Close: {ohlc.close:.2f}")
            
            return ohlc
            
        except Exception as e:
            print(f"Fehler bei OHLC-Erstellung: {str(e)}")
            raise

class PivotCalculator:
    """Berechnet verschiedene Arten von Pivot-Punkten."""
    
    @staticmethod
    def calculate_standard_pivots(data: OHLC) -> Dict[str, float]:
        """Berechnet Standard Pivot-Punkte (P, R1-R5, S1-S5)."""
        try:
            print("\nBerechne Standard Pivot-Punkte:")
            
            # Pivot-Punkt
            pivot = (data.high + data.low + data.close) / 3
            print(f"Pivot (H+L+C)/3: ({data.high:.2f} + {data.low:.2f} + {data.close:.2f}) / 3 = {pivot:.2f}")
            
            # Resistances
            r1 = (2 * pivot) - data.low
            r2 = pivot + (data.high - data.low)
            r3 = data.high + 2 * (pivot - data.low)
            r4 = r3 + (r3 - r2)
            r5 = r4 + (r4 - r3)
            
            # Supports
            s1 = (2 * pivot) - data.high
            s2 = pivot - (data.high - data.low)
            s3 = data.low - 2 * (data.high - pivot)
            s4 = s3 - (s2 - s3)
            s5 = s4 - (s3 - s4)
            
            results = {
                'R5': r5,
                'R4': r4,
                'R3': r3,
                'R2': r2,
                'R1': r1,
                'P': pivot,
                'S1': s1,
                'S2': s2,
                'S3': s3,
                'S4': s4,
                'S5': s5
            }
            
            print("\nBerechnete Standard Pivot-Punkte:")
            for level, value in results.items():
                print(f"{level}: {value:.2f}")
            
            return results
            
        except Exception as e:
            print(f"Fehler bei Standard Pivot Berechnung: {str(e)}")
            return {}
    
    @staticmethod
    def calculate_demark_pivots(data: OHLC) -> Dict[str, float]:
        """Berechnet Demark Pivot-Punkte (P, R1, S1)."""
        try:
            print("\nBerechne Demark Pivot-Punkte:")
            print(f"Open: {data.open:.2f}, High: {data.high:.2f}, Low: {data.low:.2f}, Close: {data.close:.2f}")
            
            # X-Wert berechnen
            if data.close < data.open:
                x = data.high + (2 * data.low) + data.close
                print(f"Close < Open: X = H + 2L + C = {data.high:.2f} + 2*{data.low:.2f} + {data.close:.2f}")
            elif data.close > data.open:
                x = (2 * data.high) + data.low + data.close
                print(f"Close > Open: X = 2H + L + C = 2*{data.high:.2f} + {data.low:.2f} + {data.close:.2f}")
            else:  # close == open
                x = data.high + data.low + (2 * data.close)
                print(f"Close = Open: X = H + L + 2C = {data.high:.2f} + {data.low:.2f} + 2*{data.close:.2f}")
            
            print(f"X = {x:.2f}")
            
            # Pivot-Punkte berechnen
            pivot = x / 4
            r1 = (x / 2) - data.low
            s1 = (x / 2) - data.high
            
            results = {
                'R1': r1,
                'P': pivot,
                'S1': s1
            }
            
            print("\nBerechnete Demark Pivot-Punkte:")
            for level, value in results.items():
                print(f"{level}: {value:.2f}")
            
            return results
            
        except Exception as e:
            print(f"Fehler bei Demark Pivot Berechnung: {str(e)}")
            return {}

    @staticmethod
    def check_historical_levels(
        df: pd.DataFrame,
        levels: Dict[str, float],
        tolerance_percent: float = 0.1
    ) -> Dict[str, Tuple[bool, str]]:
        """
        Überprüft für jeden Pivot-Punkt, ob er in der Historie erreicht wurde.
        
        Args:
            df: DataFrame mit OHLC-Daten
            levels: Dictionary mit Pivot-Punkten
            tolerance_percent: Toleranz in Prozent (default 0.1%)
            
        Returns:
            Dictionary mit Level -> (erreicht (bool), Zeitpunkt)
        """
        results = {}
        
        try:
            print("\nPrüfe historische Level-Erreichung:")
            
            for level_name, level_value in levels.items():
                # Toleranzband berechnen
                tolerance = level_value * (tolerance_percent / 100)
                upper_bound = level_value + tolerance
                lower_bound = level_value - tolerance
                
                print(f"\nLevel {level_name} ({level_value:.2f}):")
                print(f"Toleranzband: {lower_bound:.2f} - {upper_bound:.2f}")
                
                # Prüfe Überschneidungen mit dem Level (+/- Toleranz)
                hits = df[
                    (df['Low'] <= upper_bound) &
                    (df['High'] >= lower_bound)
                ]
                
                if not hits.empty:
                    # Level wurde erreicht
                    last_hit = hits.index[-1]
                    hit_date = last_hit.strftime('%d.%m.%Y')
                    results[level_name] = (True, hit_date)
                    print(f"✓ Erreicht am {hit_date}")
                else:
                    results[level_name] = (False, '')
                    print("✗ Nicht erreicht")
                    
        except Exception as e:
            print(f"Fehler bei der historischen Überprüfung: {str(e)}")
            # Fallback: Keine Treffer
            for level_name in levels:
                results[level_name] = (False, '')
                
        return results

    @classmethod
    def analyze_timeframe(
        cls,
        df: pd.DataFrame
    ) -> Dict[str, Dict[str, Union[Dict[str, float], Dict[str, Tuple[bool, str]]]]]:
        """
        Analysiert einen Zeitrahmen und berechnet beide Arten von Pivot-Punkten
        plus historische Überprüfung.
        
        Args:
            df: DataFrame mit OHLC Daten
            
        Returns:
            Dict mit Standard und Demark Pivot-Punkten und deren Historie
        """
        try:
            print("\n=== Timeframe Analyse Start ===")
            
            # OHLC Daten aus DataFrame extrahieren
            ohlc = OHLC.from_dataframe(df)
            
            # Pivot-Punkte berechnen
            standard_pivots = cls.calculate_standard_pivots(ohlc)
            demark_pivots = cls.calculate_demark_pivots(ohlc)
            
            # Historische Überprüfung
            standard_history = cls.check_historical_levels(df, standard_pivots)
            demark_history = cls.check_historical_levels(df, demark_pivots)
            
            print("\n=== Timeframe Analyse Ende ===")
            
            return {
                'standard': {
                    'levels': standard_pivots,
                    'history': standard_history
                },
                'demark': {
                    'levels': demark_pivots,
                    'history': demark_history
                }
            }
            
        except Exception as e:
            print(f"Fehler bei der Timeframe-Analyse: {str(e)}")
            return {
                'standard': {'levels': {}, 'history': {}},
                'demark': {'levels': {}, 'history': {}}
            }