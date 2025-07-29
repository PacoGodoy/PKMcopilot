"""
gui/main_menu.py
Version: 1.1
Last updated: 2025-07-29

Pokémon TCG Training System - Main Menu GUI.
Features:
- Robust error handling and debug logging
- Decklist validation before starting the simulator
- Detailed code comments throughout

Author: PacoGodoy
"""

import sys
import os
import sqlite3
import traceback
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget,
    QMessageBox, QComboBox, QLabel
)
from data.init_db import initialize_database
from scraper.card_importer import update_card_db
from engine.game_logic import load_deck
from reports.graphics.generate_graphs import (
    winrate_by_deck, phase_performance, common_errors, matchup_heatmap, style_distribution
)
from tools.export_cards_to_csv import export_cards_to_csv
from gui.board import run_board_gui

# --- Deck validation utility ---
def validate_decklist(deck):
    """
    Validates a decklist.
    Returns (is_valid, [list of error strings])
    """
    errors = []
    if not isinstance(deck, list):
        return False, ["Deck is not a list."]
    if len(deck) == 0:
        errors.append("Deck is empty.")
    for idx, card in enumerate(deck):
        if not isinstance(card, dict):
            errors.append(f"Card at position {idx+1} is not a dictionary: {repr(card)}")
            continue
        for field in ("name", "supertype"):
            if field not in card:
                errors.append(f"Card at position {idx+1} missing field '{field}'.")
    basic_pokemon = [
        card for card in deck
        if isinstance(card, dict)
        and card.get("supertype") == "Pokémon"
        and card.get("subtype", "").lower() == "basic"
    ]
    if len(basic_pokemon) < 1:
        errors.append("Deck must contain at least 1 Basic Pokémon.")
    # Uncomment for strict size check
    # if len(deck) != 60:
    #     errors.append(f"Deck size is {len(deck)} (should be 60).")
    return (len(errors) == 0), errors

DECKLISTS_PATH = "data/decklists"

def count_cards(db_path="data/cards.db"):
    """Count cards in DB for diagnostic display."""
    total = pokemon = trainer = energy = 0
    try:
        con = sqlite3.connect(db_path)
        cur = con.cursor()
        total = cur.execute("SELECT COUNT(*) FROM cards").fetchone()[0]
        pokemon = cur.execute("SELECT COUNT(*) FROM cards WHERE supertype LIKE 'Pok%mon' OR supertype LIKE 'Pokémon'").fetchone()[0]
        trainer = cur.execute("SELECT COUNT(*) FROM cards WHERE supertype LIKE 'Trainer'").fetchone()[0]
        energy = cur.execute("SELECT COUNT(*) FROM cards WHERE supertype LIKE 'Energy'").fetchone()[0]
        con.close()
    except Exception as e:
        print("[ERROR][MainMenu] Failed to count cards:", e)
    return total, pokemon, trainer, energy

class MainMenu(QMainWindow):
    """
    Main menu for the Pokémon TCG Training System.
    Handles DB resets, decklist selection, validation, and launching the game or analysis modules.
    """
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Pokémon TCG Training System - Main Menu")
        self.setGeometry(200, 200, 500, 430)

        layout = QVBoxLayout()

        # Option 1: Delete DB and recreate
        self.btn_reset_db = QPushButton("1. Delete DB and Recreate (with Validation)")
        self.btn_reset_db.clicked.connect(self.reset_db)
        layout.addWidget(self.btn_reset_db)

        # Option 2: Initialize simulator
        self.label_deck = QLabel("Select Player Decklist:")
        layout.addWidget(self.label_deck)
        self.combo_player_deck = QComboBox()
        self.combo_player_deck.addItems(self.get_decklists())
        layout.addWidget(self.combo_player_deck)

        self.label_ai = QLabel("Select AI Decklist:")
        layout.addWidget(self.label_ai)
        self.combo_ai_deck = QComboBox()
        self.combo_ai_deck.addItems(self.get_decklists())
        layout.addWidget(self.combo_ai_deck)

        self.btn_simulator = QPushButton("2. Start Simulator")
        self.btn_simulator.clicked.connect(self.start_simulator)
        layout.addWidget(self.btn_simulator)

        # Option 3: Generate reports
        self.label_report_deck = QLabel("Select Decklist for Report:")
        layout.addWidget(self.label_report_deck)
        self.combo_report_deck = QComboBox()
        self.combo_report_deck.addItems(self.get_decklists())
        layout.addWidget(self.combo_report_deck)

        self.btn_report = QPushButton("3. Generate Reports and Graphs")
        self.btn_report.clicked.connect(self.generate_reports)
        layout.addWidget(self.btn_report)

        # Option 4: Export DB to CSV
        self.btn_export_csv = QPushButton("4. Export DB Tables to CSV")
        self.btn_export_csv.clicked.connect(self.export_db_csv)
        layout.addWidget(self.btn_export_csv)

        # Set Layout
        central = QWidget()
        central.setLayout(layout)
        self.setCentralWidget(central)

        # For counting matches (for advice after 3rd match)
        self.match_counter = {}

    def get_decklists(self):
        """List all available decklists by name (without .json extension)."""
        try:
            if not os.path.exists(DECKLISTS_PATH):
                return []
            return [f.replace(".json", "") for f in os.listdir(DECKLISTS_PATH) if f.endswith(".json")]
        except Exception as e:
            print("[ERROR][MainMenu] Could not list decklists:", e)
            return []

    def load_decklist(self, deck_name):
        """
        Loads a decklist from file by name (without .json), returns list of dicts.
        Uses engine.game_logic.load_deck.
        """
        try:
            path = os.path.join(DECKLISTS_PATH, deck_name + ".json")
            deck = load_deck(path)
            return deck
        except Exception as e:
            print(f"[ERROR][MainMenu] Failed to load decklist '{deck_name}': {e}")
            return None

    def reset_db(self):
        """
        Deletes and recreates the database, re-imports all cards.
        Provides user feedback and error logging.
        """
        confirm = QMessageBox.question(
            self, "Reset DB", "Are you sure you want to DELETE and RECREATE the entire database?\nThis will also re-import all cards.",
            QMessageBox.Yes | QMessageBox.No
        )
        if confirm == QMessageBox.Yes:
            db_path = "data/cards.db"
            error_log_path = "data/import_errors.log"
            if os.path.exists(db_path):
                try:
                    os.remove(db_path)
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Failed to delete old database: {e}")
                    return
            initialize_database()
            try:
                errors = update_card_db(api_key="11ac24b1-3a85-4fde-aac8-88077c503e75", error_log_path=error_log_path)
                total, pokemon, trainer, energy = count_cards(db_path)
                message = (
                    f"Cards imported successfully!\n\n"
                    f"Total cards: {total}\n"
                    f"Pokémon: {pokemon}\n"
                    f"Trainers: {trainer}\n"
                    f"Energy: {energy}\n"
                )
                if errors:
                    message += f"\nSome errors occurred during import. See {error_log_path}."
                    QMessageBox.warning(self, "Import Completed With Errors", message)
                else:
                    QMessageBox.information(self, "Import Complete", message)
            except Exception as e:
                tb = traceback.format_exc()
                QMessageBox.critical(self, "Error", f"Error updating card DB: {e}\n\n{tb}")
        else:
            QMessageBox.information(self, "Cancelled", "Operation cancelled.")

    def start_simulator(self):
        """
        Validates both selected decklists before trying to start the simulator.
        If validation fails, shows detailed error messages.
        """
        player_deck_name = self.combo_player_deck.currentText()
        ai_deck_name = self.combo_ai_deck.currentText()
        player_deck = self.load_decklist(player_deck_name)
        ai_deck = self.load_decklist(ai_deck_name)

        # Validate both decks before launching simulator
        is_valid, errors = validate_decklist(player_deck)
        is_valid_ai, errors_ai = validate_decklist(ai_deck)
        if not is_valid or not is_valid_ai:
            msg = ""
            if not is_valid:
                msg += f"Player deck errors ({player_deck_name}):\n" + "\n".join(errors) + "\n"
            if not is_valid_ai:
                msg += f"AI deck errors ({ai_deck_name}):\n" + "\n".join(errors_ai)
            QMessageBox.warning(self, "Invalid Decklist", msg)
            return

        key = (player_deck_name, ai_deck_name)
        self.match_counter[key] = self.match_counter.get(key, 0) + 1
        match_num = self.match_counter[key]

        # Launch the full board GUI with validated decks
        self.close()
        run_board_gui(player_deck, ai_deck)

        # On 3rd match of same player/decklist, trigger advice
        if match_num == 3:
            QMessageBox.information(self, "Advice", f"Detailed analysis & advice unlocked for {player_deck_name} after 3 matches!")

    def generate_reports(self):
        """Run analyses and produce graphs for the selected deck."""
        decklist = self.combo_report_deck.currentText()
        try:
            winrate_by_deck()
            phase_performance()
            common_errors()
            matchup_heatmap()
            style_distribution()
            QMessageBox.information(self, "Reports", f"Reports and graphs generated for {decklist}!\nCheck the reports/graphics/ directory.")
        except Exception as e:
            tb = traceback.format_exc()
            QMessageBox.warning(self, "Error", f"Error generating reports: {e}\n\n{tb}")

    def export_db_csv(self):
        """Exports all cards from DB to CSV, handles errors."""
        try:
            export_cards_to_csv()
            QMessageBox.information(self, "Export", "All cards exported to data/all_cards_export.csv!")
        except Exception as e:
            tb = traceback.format_exc()
            QMessageBox.warning(self, "Error", f"Error exporting CSV: {e}\n\n{tb}")

def run_main_menu():
    """Entry point for running the main menu GUI."""
    app = QApplication(sys.argv)
    window = MainMenu()
    window.show()
    sys.exit(app.exec_())