import sqlite3
from datetime import datetime
from typing import Dict, List, Optional
import json

class Database:
    def __init__(self, db_path: str = "pivot_plotter.db"):
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        """Initialisiert die Datenbankstruktur."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS watchlist (
                    symbol TEXT PRIMARY KEY
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS pivot_points (
                    symbol TEXT,
                    timeframe TEXT,
                    date TEXT,
                    standard_pivots TEXT,  -- JSON string
                    demark_pivots TEXT,    -- JSON string
                    PRIMARY KEY (symbol, timeframe, date)
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS level_history (
                    symbol TEXT,
                    timeframe TEXT,
                    level_type TEXT,       -- 'standard' oder 'demark'
                    level_name TEXT,       -- 'R1', 'P', 'S1' etc.
                    level_value REAL,
                    hit_date TEXT,
                    PRIMARY KEY (symbol, timeframe, level_type, level_name, hit_date)
                )
            """)
    
    def save_watchlist(self, symbols: List[str]):
        """Speichert die Watchlist."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM watchlist")
            conn.executemany(
                "INSERT INTO watchlist (symbol) VALUES (?)",
                [(s,) for s in symbols]
            )
    
    def load_watchlist(self) -> List[str]:
        """Lädt die Watchlist."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT symbol FROM watchlist")
            return [row[0] for row in cursor.fetchall()]
    
    def save_pivot_points(
        self,
        symbol: str,
        timeframe: str,
        standard_pivots: Dict[str, float],
        demark_pivots: Dict[str, float]
    ):
        """Speichert berechnete Pivot-Punkte."""
        date = datetime.now().strftime('%Y-%m-%d')
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO pivot_points 
                (symbol, timeframe, date, standard_pivots, demark_pivots)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    symbol,
                    timeframe,
                    date,
                    json.dumps(standard_pivots),
                    json.dumps(demark_pivots)
                )
            )
    
    def load_pivot_points(
        self,
        symbol: str,
        timeframe: str
    ) -> Optional[Dict]:
        """Lädt die letzten Pivot-Punkte."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                SELECT standard_pivots, demark_pivots
                FROM pivot_points
                WHERE symbol = ? AND timeframe = ?
                ORDER BY date DESC LIMIT 1
                """,
                (symbol, timeframe)
            )
            row = cursor.fetchone()
            
            if row:
                return {
                    'standard': json.loads(row[0]),
                    'demark': json.loads(row[1])
                }
            return None
    
    def save_level_hit(
        self,
        symbol: str,
        timeframe: str,
        level_type: str,
        level_name: str,
        level_value: float,
        hit_date: str
    ):
        """Speichert einen Level-Treffer."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO level_history
                (symbol, timeframe, level_type, level_name, level_value, hit_date)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (symbol, timeframe, level_type, level_name, level_value, hit_date)
            )
    
    def get_level_history(
        self,
        symbol: str,
        timeframe: str
    ) -> Dict[str, List[Dict]]:
        """Lädt die Historie der Level-Treffer."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                SELECT level_type, level_name, level_value, hit_date
                FROM level_history
                WHERE symbol = ? AND timeframe = ?
                ORDER BY hit_date DESC
                """,
                (symbol, timeframe)
            )
            
            history = {
                'standard': [],
                'demark': []
            }
            
            for row in cursor.fetchall():
                level_type, name, value, date = row
                history[level_type].append({
                    'level': name,
                    'value': value,
                    'date': date
                })
            
            return history