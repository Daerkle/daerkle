from dataclasses import dataclass
import pandas as pd
from typing import Dict, Tuple, Union

@dataclass
class OHLC:
    open: float
    high: float
    low: float
    close: float
    
    @classmethod
    def from_dataframe(cls, df: pd.DataFrame) -> 'OHLC':
        """
        Erstellt OHLC aus einem DataFrame mit korrekter Zeitraumfilterung.
        Für tägliche Daten wird nur der letzte Handelstag verwendet.
        Für wöchentliche/monatliche Daten wird der gesamte Zeitraum verwendet.
        """
        if df.empty:
            raise ValueError("DataFrame ist leer")
            
        try:
            # Identifiziere den Zeitraum basierend auf dem DataFrame-Index
            index_diff = df.index[-1] - df.index[-2]
            
            if index_diff.days <= 1:  # Tägliche Daten
                # Filtere nur den letzten Handelstag
                last_date = df.index[-1].date()
                df = df[df.index.date == last_date]
            
            # Berechne OHLC-Werte für den gefilterten Zeitraum
            ohlc = cls(
                open=float(df['Open'].iloc[0]),      # Erste Eröffnung des Zeitraums
                high=float(df['High'].max()),        # Höchster Wert des Zeitraums
                low=float(df['Low'].min()),          # Tiefster Wert des Zeitraums
                close=float(df['Close'].iloc[-1])    # Letzter Schlusskurs des Zeitraums
            )
            return ohlc
            
        except Exception as e:
            print(f"Fehler bei OHLC-Erstellung: {str(e)}")
            raise

def check_historical_levels(
    df: pd.DataFrame,
    levels: Dict[str, float],
    timeframe: str,  # "1d", "1w", oder "1m"
    tolerance_percent: float = 0.5
) -> Dict[str, Tuple[bool, str, str]]:
    """
    Überprüft für jeden Pivot-Punkt, ob er in der Historie erreicht wurde.
    Für Wochen- und Monatscharts werden auch nicht getestete Levels markiert.
    
    Returns:
        Dict mit (wurde_erreicht, datum_erreicht, status_text)
        Status kann sein: "" (für Tagesdaten), "Noch nicht getestet" oder "Wartet auf Test"
    """
    results = {}
    
    try:
        for level_name, level_value in levels.items():
            # Toleranzband berechnen
            tolerance = level_value * (tolerance_percent / 100)
            upper_bound = level_value + tolerance
            lower_bound = level_value - tolerance
            
            # Prüfe Überschneidungen mit dem Level (+/- Toleranz)
            hits = df[
                (df['Low'] <= upper_bound) &
                (df['High'] >= lower_bound)
            ]
            
            # Aktuelle Position zum Level ermitteln
            current_price = df['Close'].iloc[-1]
            is_above = level_value > current_price
            
            if not hits.empty:
                # Level wurde erreicht - zeige Datum
                last_hit = hits.index[-1]
                hit_date = last_hit.strftime('%d.%m')  # Kompakteres Datumsformat
                results[level_name] = (True, hit_date, '')
            else:
                # Level wurde nicht getestet
                if timeframe in ["1w", "1m"]:
                    # Spezielle Markierung für Wochen- und Monatscharts
                    is_demark_s1 = level_name == "S1" and "demark" in str(levels)
                    is_pivot = level_name == "P"
                    is_key_level = level_name in ["R1", "S1"]
                    
                    if is_demark_s1:
                        # DMS1 als wichtige Marke markieren
                        status = "⚑" if is_above else "⚐"
                    elif is_pivot or is_key_level:
                        # Offene wichtige Levels markieren
                        status = "○↑" if is_above else "○↓"
                    else:
                        # Standard Level-Markierung
                        status = "↑" if is_above else "↓"
                else:
                    # Einfache Markierung für Tagesdaten
                    status = "↑" if is_above else "↓"
                
                results[level_name] = (False, '', status)
                
    except Exception as e:
        print(f"Fehler bei der historischen Überprüfung: {str(e)}")
        # Fallback: Keine Treffer
        for level_name in levels:
            results[level_name] = (False, '', '')
            
    return results

def check_pivot_status(df: pd.DataFrame, pivot: float) -> Dict[str, str]:
    """Prüft den Status des Standard Pivots."""
    try:
        current_price = df['Close'].iloc[-1]
        
        if current_price > pivot:
            return {
                'status': 'Über Pivot',
                'color': '#10B981',  # Grün
                'distance': f"+{((current_price/pivot - 1) * 100):.1f}%"
            }
        elif current_price < pivot:
            return {
                'status': 'Unter Pivot',
                'color': '#EF4444',  # Rot
                'distance': f"{((current_price/pivot - 1) * 100):.1f}%"
            }
        else:
            return {
                'status': 'Am Pivot',
                'color': '#6B7280',  # Grau
                'distance': "0%"
            }
    except Exception as e:
        print(f"Fehler bei Pivot-Status Prüfung: {str(e)}")
        return {
            'status': 'Unbekannt',
            'color': '#6B7280',
            'distance': '-'
        }