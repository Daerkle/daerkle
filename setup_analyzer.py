import pandas as pd
import numpy as np
from typing import List, Dict, Optional, TypedDict
from dataclasses import dataclass
from enum import Enum

class SetupType(Enum):
    LONG = "long"
    SHORT = "short"

class SetupSubType(Enum):
    PIVOT_BOUNCE = "pivot_bounce"
    CLUSTER = "cluster"
    VOLUME_CONFIRMED = "volume_confirmed"
    FALSE_BREAKOUT = "false_breakout"
    DIVERGENCE = "divergence"
    REPEATED_TEST = "repeated_test"

class SetupQuality(Enum):
    A_PLUS = "A+"
    A = "A"
    B = "B"

@dataclass
class Setup:
    type: SetupType
    sub_type: SetupSubType
    quality: SetupQuality
    entry: float
    stop_loss: float
    target: float
    probability: float
    rr: float
    volume_buzz: float
    timeframe: str
    trend_direction: str
    cluster: bool = False
    divergence: bool = False
    repeated_tests: int = 0
    trailing_stop: Optional[float] = None
    additional_targets: Optional[List[float]] = None
    confirmations: Optional[Dict[str, bool]] = None
    best_time: Optional[str] = None

class SetupAnalyzer:
    def __init__(self, df: pd.DataFrame, timeframe: str = "1d"):
        self.df = df
        self.timeframe = timeframe
        self.tolerance = 0.005  # 0.5% tolerance for level tests
        self.volume_ma = df["Volume"].rolling(window=20).mean()
        
    def calculate_pivot_levels(self) -> Dict[str, float]:
        """Calculate pivot levels for the current bar"""
        prev_high = self.df["High"].iloc[-2]
        prev_low = self.df["Low"].iloc[-2]
        prev_close = self.df["Close"].iloc[-2]
        
        pivot = (prev_high + prev_low + prev_close) / 3
        r1 = 2 * pivot - prev_low
        r2 = pivot + (prev_high - prev_low)
        s1 = 2 * pivot - prev_high
        s2 = pivot - (prev_high - prev_low)
        
        return {
            "P": pivot,
            "R1": r1,
            "R2": r2,
            "S1": s1,
            "S2": s2
        }

    def check_volume_confirmation(self, current_volume: float) -> bool:
        """Check if current volume is significantly higher than average"""
        avg_volume = self.volume_ma.iloc[-1]
        return current_volume >= avg_volume * 1.5

    def calculate_trend_direction(self, window: int = 20) -> str:
        """Calculate trend direction using SMA"""
        sma = self.df["Close"].rolling(window=window).mean()
        current_price = self.df["Close"].iloc[-1]
        current_sma = sma.iloc[-1]
        
        if current_price > current_sma * 1.02:  # 2% above SMA
            return "up"
        elif current_price < current_sma * 0.98:  # 2% below SMA
            return "down"
        return "sideways"

    def find_pivot_bounce_long(self) -> Optional[Setup]:
        """Find long setup based on bounce from S1 level"""
        levels = self.calculate_pivot_levels()
        s1 = levels["S1"]
        current_low = self.df["Low"].iloc[-1]
        current_close = self.df["Close"].iloc[-1]
        
        # Check if price touched S1 and bounced
        if (current_low <= s1 * (1 + self.tolerance) and 
            current_close > s1 * (1 + self.tolerance * 2)):
            
            entry = current_close
            stop_loss = current_low * 0.99  # 1% below low
            target = levels["P"]  # Target at pivot
            rr = (target - entry) / (entry - stop_loss)
            
            volume_confirmed = self.check_volume_confirmation(self.df["Volume"].iloc[-1])
            
            return Setup(
                type=SetupType.LONG,
                sub_type=SetupSubType.PIVOT_BOUNCE,
                quality=SetupQuality.A if volume_confirmed else SetupQuality.B,
                entry=entry,
                stop_loss=stop_loss,
                target=target,
                probability=65 if volume_confirmed else 55,
                rr=rr,
                volume_buzz=((self.df["Volume"].iloc[-1] / self.volume_ma.iloc[-1]) - 1) * 100,
                timeframe=self.timeframe,
                trend_direction=self.calculate_trend_direction(),
                confirmations={"volume": volume_confirmed}
            )
        return None

    def find_false_breakout_short(self) -> Optional[Setup]:
        """Find short setup based on false breakout above R1"""
        levels = self.calculate_pivot_levels()
        r1 = levels["R1"]
        current_high = self.df["High"].iloc[-1]
        current_close = self.df["Close"].iloc[-1]
        
        # Check if price broke above R1 but closed below
        if (current_high >= r1 * (1 - self.tolerance) and 
            current_close < r1 * (1 - self.tolerance)):
            
            entry = current_close
            stop_loss = current_high * 1.01  # 1% above high
            target = levels["P"]  # Target at pivot
            rr = (entry - target) / (stop_loss - entry)
            
            volume_confirmed = self.check_volume_confirmation(self.df["Volume"].iloc[-1])
            
            return Setup(
                type=SetupType.SHORT,
                sub_type=SetupSubType.FALSE_BREAKOUT,
                quality=SetupQuality.A if volume_confirmed else SetupQuality.B,
                entry=entry,
                stop_loss=stop_loss,
                target=target,
                probability=70 if volume_confirmed else 60,
                rr=rr,
                volume_buzz=((self.df["Volume"].iloc[-1] / self.volume_ma.iloc[-1]) - 1) * 100,
                timeframe=self.timeframe,
                trend_direction=self.calculate_trend_direction(),
                confirmations={"volume": volume_confirmed}
            )
        return None

    def analyze_setups(self) -> List[Setup]:
        """Find all valid setups in the current market data"""
        setups = []
        
        # Check for long setups
        pivot_bounce = self.find_pivot_bounce_long()
        if pivot_bounce:
            setups.append(pivot_bounce)
            
        # Check for short setups
        false_breakout = self.find_false_breakout_short()
        if false_breakout:
            setups.append(false_breakout)
            
        return setups
