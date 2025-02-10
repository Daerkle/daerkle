import unittest
import json
import os
from api_server import init_watchlist, read_watchlist, write_watchlist

class TestWatchlist(unittest.TestCase):
    def setUp(self):
        """Test-Setup: Sichert existierende Watchlist und erstellt Test-Umgebung"""
        # Backup der originalen Watchlist
        self.original_watchlist = None
        if os.path.exists('watchlist.json'):
            with open('watchlist.json', 'r') as f:
                self.original_watchlist = f.read()
            os.remove('watchlist.json')
        
        print("\nTest-Umgebung vorbereitet")

    def tearDown(self):
        """Test-Cleanup: Stellt originale Watchlist wieder her"""
        # Entferne Test-Watchlist
        if os.path.exists('watchlist.json'):
            os.remove('watchlist.json')
        
        # Stelle Original wieder her
        if self.original_watchlist:
            with open('watchlist.json', 'w') as f:
                f.write(self.original_watchlist)
        
        print("Test-Umgebung aufgeräumt")

    def test_init_watchlist(self):
        """Test der Watchlist-Initialisierung"""
        print("\nTest: Watchlist Initialisierung")
        
        # Stelle sicher, dass keine Watchlist existiert
        if os.path.exists('watchlist.json'):
            os.remove('watchlist.json')
        
        init_watchlist()
        self.assertTrue(os.path.exists('watchlist.json'), "watchlist.json wurde nicht erstellt")
        
        with open('watchlist.json', 'r') as f:
            data = json.load(f)
        self.assertEqual(data, {"symbols": []}, "Watchlist wurde nicht korrekt initialisiert")
        print("✓ Watchlist wurde korrekt initialisiert")

    def test_write_read_watchlist(self):
        """Test des Schreibens und Lesens der Watchlist"""
        print("\nTest: Schreiben und Lesen der Watchlist")
        test_data = {"symbols": ["AAPL", "MSFT"]}
        
        # Schreiben testen
        write_watchlist(test_data)
        print("✓ Watchlist wurde geschrieben")
        
        # Lesen testen
        read_data = read_watchlist()
        self.assertEqual(read_data, test_data, "Gelesene Daten stimmen nicht mit geschriebenen überein")
        print("✓ Watchlist wurde korrekt gelesen")

    def test_watchlist_persistence(self):
        """Test der Datenpersistenz"""
        print("\nTest: Watchlist Datenpersistenz")
        
        # Erste Schreib-/Leseoperation
        write_watchlist({"symbols": ["AAPL"]})
        data1 = read_watchlist()
        print("✓ Erste Schreiboperation erfolgreich")
        
        # Zweite Schreib-/Leseoperation
        write_watchlist({"symbols": ["AAPL", "MSFT"]})
        data2 = read_watchlist()
        print("✓ Zweite Schreiboperation erfolgreich")
        
        self.assertEqual(data2["symbols"], ["AAPL", "MSFT"], "Daten wurden nicht korrekt gespeichert")
        print("✓ Datenpersistenz verifiziert")

if __name__ == '__main__':
    print("Starte Watchlist Tests...")
    unittest.main(verbosity=2)