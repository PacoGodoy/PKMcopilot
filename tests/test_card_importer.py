import unittest
import os
import sqlite3
from scraper import card_importer

class TestCardImporter(unittest.TestCase):
    TEST_DB = "data/test_cards.db"

    def setUp(self):
        # Create a fresh test DB
        if os.path.exists(self.TEST_DB):
            os.remove(self.TEST_DB)
        # Minimal schema
        con = sqlite3.connect(self.TEST_DB)
        cur = con.cursor()
        cur.execute("CREATE TABLE cards (card_id TEXT PRIMARY KEY, name TEXT, supertype TEXT, subtype TEXT, hp INTEGER, types TEXT, retreat_cost INTEGER, attacks TEXT, abilities TEXT, rules TEXT, expansion TEXT, number TEXT, rarity TEXT, image_url TEXT, source TEXT);")
        con.commit()
        con.close()

    def test_manual_card_entry(self):
        card_data = {
            "id": "manual-001",
            "name": "Testmon",
            "supertype": "Pokemon",
            "subtype": "Basic",
            "hp": 50,
            "types": ["Fire"],
            "retreatCost": 1,
            "attacks": "[{'name':'Ember','damage':'30'}]",
            "abilities": None,
            "rules": "",
            "expansion": "SVTEST",
            "number": "1",
            "rarity": "Common",
            "image_url": "",
            "source": "manual"
        }
        card_importer.manual_card_entry(card_data, db_path=self.TEST_DB)
        # Check DB for entry
        con = sqlite3.connect(self.TEST_DB)
        cur = con.cursor()
        cur.execute("SELECT name FROM cards WHERE card_id = ?", (card_data["id"],))
        result = cur.fetchone()
        con.close()
        self.assertEqual(result[0], "Testmon")

    def tearDown(self):
        if os.path.exists(self.TEST_DB):
            os.remove(self.TEST_DB)

if __name__ == "__main__":
    unittest.main()