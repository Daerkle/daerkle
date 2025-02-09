from typing import Dict, Union
import pandas as pd
# OHLC wird direkt aus core.pivot_base importiert, um zirkuläre Importe zu vermeiden.
from core.pivot_base import OHLC

def check_demark_setup(
    df: pd.DataFrame,
    demark_levels: Dict[str, float],
    demark_history: Dict[str, tuple],
    standard_levels: Dict[str, float]
) -> Dict[str, Dict[str, Union[bool, str, float]]]:
    """
    Prüft auf aktive DeMark Trading Setups.
    Ein Setup wird als aktiv erkannt, wenn:
      - Der DeMark Level (R1 bzw. S1) in der Historie berührt wurde
        ODER
      - Der aktuelle Kurs mindestens 0.1% über R1 (Long) oder unter S1 (Short) liegt
      - und das zugehörige Standard Level (R2 bzw. S2) als Target vorhanden ist.

    Dabei gilt:
      - Long Setup: DeMark R1 → Standard R2
        (Einstieg, wenn R1 getriggert wurde ODER der Kurs mind. 0.1% über DM-R1 liegt)
      - Short Setup: DeMark S1 → Standard S2
        (Einstieg, wenn S1 getriggert wurde ODER der Kurs mind. 0.1% unter DM-S1 liegt)

    Args:
        df: DataFrame mit OHLC-Daten
        demark_levels: DeMark Pivot Levels (R1/S1 als Trigger)
        demark_history: Historie der DeMark Level-Berührungen
        standard_levels: Standard Pivot Levels (R2/S2 als Targets)

    Returns:
        Dictionary mit Setup-Informationen (aktiv/inaktiv, Trigger, Target und Distanz)
    """
    try:
        current_price = df['Close'].iloc[-1]
        setups = {
            'long': {'active': False, 'trigger': 0, 'target': 0, 'distance': ''},
            'short': {'active': False, 'trigger': 0, 'target': 0, 'distance': ''}
        }

        long_active = False
        short_active = False
        price_above_r1_percent = 0
        price_below_s1_percent = 0

        # Prüfe Long Setup Bedingungen
        if 'R1' in demark_levels and 'R2' in standard_levels:
            r1_triggered = demark_history['R1'][0]
            price_above_r1_percent = ((current_price / demark_levels['R1']) - 1) * 100
            long_active = r1_triggered or price_above_r1_percent >= 0.1

        # Prüfe Short Setup Bedingungen
        if 'S1' in demark_levels and 'S2' in standard_levels:
            s1_triggered = demark_history['S1'][0]
            price_below_s1_percent = ((current_price / demark_levels['S1']) - 1) * 100
            short_active = s1_triggered or price_below_s1_percent <= -0.1

        # Aktiviere nur das Setup mit der stärkeren Tendenz
        if long_active and not short_active:
            # Aktiviere Long Setup
            setups['long'] = {
                'active': True,
                'trigger': demark_levels['R1'],
                'target': standard_levels['R2'],
                'distance': f"{((standard_levels['R2'] / current_price - 1) * 100):.1f}%"
            }
        elif short_active and not long_active:
            # Aktiviere Short Setup
            setups['short'] = {
                'active': True,
                'trigger': demark_levels['S1'],
                'target': standard_levels['S2'],
                'distance': f"{((standard_levels['S2'] / current_price - 1) * 100):.1f}%"
            }
        # Wenn beide aktiv wären, aktiviere keins (neutraler Markt)

        return setups
    except Exception as e:
        print(f"Fehler bei der DeMark Setup Prüfung: {str(e)}")
        return {
            'long': {'active': False, 'trigger': 0, 'target': 0, 'distance': ''},
            'short': {'active': False, 'trigger': 0, 'target': 0, 'distance': ''}
        }

def analyze_timeframes_setups(timeframes_data: Dict[str, pd.DataFrame]) -> Dict[str, Dict]:
    """
    Analysiert die DeMark Trading Setups für verschiedene Zeitrahmen (z. B. Tag, Woche, Monat).

    Args:
        timeframes_data: Dictionary mit DataFrames für unterschiedliche Zeitrahmen,
                         z. B. {'1d': df_tag, '1w': df_woche, '1m': df_monat}

    Returns:
        Dictionary, das für jeden Zeitrahmen die Setup-Informationen enthält.
    """
    setups_by_timeframe = {}
    for timeframe, df in timeframes_data.items():
        if df is not None and not df.empty:
            try:
                # Um zirkuläre Importe zu vermeiden, erfolgt der Import von PivotCalculator hier lokal.
                from pivot_calculator import PivotCalculator
                analysis = PivotCalculator.analyze_timeframe(df)
                demark_levels = analysis['demark']['levels']
                demark_history = analysis['demark']['history']
                standard_levels = analysis['standard']['levels']
                setups = check_demark_setup(df, demark_levels, demark_history, standard_levels)
                setups_by_timeframe[timeframe] = setups
            except Exception as e:
                print(f"Fehler bei der Setup-Analyse für {timeframe}: {str(e)}")
                setups_by_timeframe[timeframe] = {
                    'long': {'active': False, 'trigger': 0, 'target': 0, 'distance': ''},
                    'short': {'active': False, 'trigger': 0, 'target': 0, 'distance': ''}
                }
        else:
            setups_by_timeframe[timeframe] = {
                'long': {'active': False, 'trigger': 0, 'target': 0, 'distance': ''},
                'short': {'active': False, 'trigger': 0, 'target': 0, 'distance': ''}
            }
    return setups_by_timeframe
