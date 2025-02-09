from typing import Dict, Tuple, Union
import pandas as pd
from core.pivot_base import OHLC, check_historical_levels, check_pivot_status
# Importiere die Funktion check_demark_setup aus dem Modul core/setup_analyzer.
from core.setup_analyzer import check_demark_setup

class PivotCalculator:
    """Berechnet und analysiert Pivot-Punkte."""
    
    @staticmethod
    def calculate_standard_pivots(data: OHLC) -> Dict[str, float]:
        """Berechnet Standard Pivot-Punkte (P, R1-R5, S1-S5)."""
        try:
            # Pivot-Punkt
            pivot = (data.high + data.low + data.close) / 3

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

            return {
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
        except Exception as e:
            print(f"Fehler bei Standard Pivot Berechnung: {str(e)}")
            return {}
    
    @staticmethod
    def calculate_demark_pivots(data: OHLC) -> Dict[str, float]:
        """Berechnet Demark Pivot-Punkte (P, R1/R2, S1/S2)."""
        try:
            # X-Wert berechnen
            if data.close < data.open:
                x = data.high + (2 * data.low) + data.close
            elif data.close > data.open:
                x = (2 * data.high) + data.low + data.close
            else:  # close == open
                x = data.high + data.low + (2 * data.close)

            # Pivot-Punkte berechnen
            pivot = x / 4
            r1 = (x / 2) - data.low
            r2 = data.high + (r1 - data.low)  # R2 nach DeMark Methode
            s1 = (x / 2) - data.high
            s2 = data.low - (data.high - s1)  # S2 nach DeMark Methode

            return {
                'R2': r2,
                'R1': r1,
                'P': pivot,
                'S1': s1,
                'S2': s2
            }
        except Exception as e:
            print(f"Fehler bei Demark Pivot Berechnung: {str(e)}")
            return {}
    
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
            # OHLC Daten aus DataFrame extrahieren
            ohlc = OHLC.from_dataframe(df)

            # Pivot-Punkte berechnen
            standard_pivots = cls.calculate_standard_pivots(ohlc)
            demark_pivots = cls.calculate_demark_pivots(ohlc)

            # Historische Überprüfung
            # Bestimme den Zeitrahmen aus dem DataFrame-Index
            index_diff = df.index[-1] - df.index[-2]
            timeframe = "1d"  # Standard ist Tagesdaten
            if index_diff.days >= 28:  # Ungefähr ein Monat
                timeframe = "1m"
            elif index_diff.days >= 7:  # Eine Woche
                timeframe = "1w"
                
            standard_history = check_historical_levels(df, standard_pivots, timeframe)
            demark_history = check_historical_levels(df, demark_pivots, timeframe)

            # Pivot Status
            pivot_status = check_pivot_status(df, standard_pivots['P'])

            analysis = {
                'standard': {
                    'levels': standard_pivots,
                    'history': standard_history,
                    'status': pivot_status
                },
                'demark': {
                    'levels': demark_pivots,
                    'history': demark_history
                }
            }

            # DeMark Setup Check
            analysis['demark']['setups'] = check_demark_setup(
                df,
                analysis['demark']['levels'],
                analysis['demark']['history'],
                analysis['standard']['levels']
            )

            return analysis
        except Exception as e:
            print(f"Fehler bei der Timeframe-Analyse: {str(e)}")
            return {
                'standard': {
                    'levels': {},
                    'history': {},
                    'status': {
                        'status': 'Fehler',
                        'color': '#6B7280',
                        'distance': '-'
                    }
                },
                'demark': {
                    'levels': {},
                    'history': {},
                    'setups': {
                        'long': {'active': False, 'trigger': 0, 'target': 0, 'distance': ''},
                        'short': {'active': False, 'trigger': 0, 'target': 0, 'distance': ''}
                    }
                }
            }
