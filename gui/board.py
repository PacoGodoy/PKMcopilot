"""
gui/board.py
Version: 1.1
Last updated: 2025-07-29

Main game board GUI. Handles player actions, drag-and-drop, zone displays, game logic, and coach feedback.
Includes detailed comments and robust error handling.
"""

import requests
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QListWidget, QListWidgetItem, QMessageBox, QTextEdit
)
from PyQt5.QtCore import Qt, QMimeData
from PyQt5.QtGui import QDrag, QPixmap, QIcon
from engine.game_state import GameState
from engine.ai_opponent import AIOpponent
from engine.coach_ai import CoachAI
from gui.card_zone import CardZone
import traceback

DEBUG = True
def debug_print(*args, **kwargs):
    if DEBUG:
        print("[DEBUG][BOARD]", *args, **kwargs)

def error_print(msg, exc=None):
    print("[ERROR][BOARD]", msg)
    if exc:
        print(traceback.format_exc())

class BoardWindow(QMainWindow):
    def __init__(self, player_deck, ai_deck):
        try:
            super().__init__()
            self.setWindowTitle("Pokémon TCG Simulator")
            self.resize(1200, 800)

            self.state = GameState(player_deck, ai_deck)
            self.ai = AIOpponent(ai_deck)
            self.coach = CoachAI()
            self.card_image_cache = {}

            central = QWidget()
            self.setCentralWidget(central)
            main_layout = QVBoxLayout()
            central.setLayout(main_layout)

            self.deck_label = QLabel()
            self.discard_label = QLabel()
            self.prize_label = QLabel()
            deck_info_layout = QHBoxLayout()
            deck_info_layout.addWidget(self.deck_label)
            deck_info_layout.addWidget(self.discard_label)
            deck_info_layout.addWidget(self.prize_label)
            main_layout.addLayout(deck_info_layout)

            self.opp_active = CardZone("AI Active", self)
            self.opp_bench = QLabel("AI Bench: (hidden)")
            opp_layout = QHBoxLayout()
            opp_layout.addWidget(self.opp_active)
            opp_layout.addWidget(self.opp_bench)
            main_layout.addLayout(opp_layout)

            self.log_area = QTextEdit()
            self.log_area.setReadOnly(True)
            self.log_area.setMinimumHeight(120)
            main_layout.addWidget(self.log_area)

            self.player_active = CardZone("Your Active", self)
            self.player_bench = [CardZone(f"Bench {i+1}", self) for i in range(5)]
            player_bench_layout = QHBoxLayout()
            player_bench_layout.addWidget(self.player_active)
            for bench_zone in self.player_bench:
                player_bench_layout.addWidget(bench_zone)
            main_layout.addLayout(player_bench_layout)

            self.hand_list = QListWidget()
            self.hand_list.setDragEnabled(True)
            self.hand_list.setViewMode(QListWidget.IconMode)
            self.hand_list.setIconSize(QPixmap(100, 140).size())
            self.hand_list.setMaximumHeight(170)
            self.hand_list.mouseMoveEvent = self.start_drag_from_hand
            main_layout.addWidget(QLabel("Your Hand:"))
            main_layout.addWidget(self.hand_list)

            controls = QHBoxLayout()
            self.btn_attack = QPushButton("Attack")
            self.btn_attack.clicked.connect(self.attack)
            self.btn_end_turn = QPushButton("End Turn")
            self.btn_end_turn.clicked.connect(self.end_turn)
            controls.addWidget(self.btn_attack)
            controls.addWidget(self.btn_end_turn)
            main_layout.addLayout(controls)

            self.update_ui()
            self.log_area.append("Game started! Your turn.")
        except Exception as e:
            error_print("Failed to initialize BoardWindow", e)
            raise

    def load_card_image(self, url):
        """Download image or use cache. Handles errors gracefully."""
        try:
            if url in self.card_image_cache:
                return self.card_image_cache[url]
            resp = requests.get(url)
            if resp.status_code == 200:
                self.card_image_cache[url] = resp.content
                debug_print("Loaded image from", url)
                return resp.content
            else:
                debug_print("Failed to load image:", url)
        except Exception as e:
            error_print("Image download error", e)
        return b""

    def update_ui(self):
        """Update all UI elements to match game state."""
        try:
            self.hand_list.clear()
            for card in self.state.player.hand:
                item = QListWidgetItem(card["name"])
                if card.get("image_url"):
                    pixmap = QPixmap()
                    pixmap.loadFromData(self.load_card_image(card["image_url"]))
                    item.setIcon(QIcon(pixmap.scaled(90, 126, Qt.KeepAspectRatio)))
                self.hand_list.addItem(item)
            self.player_active.set_card(self.state.player.active)
            for i in range(5):
                if i < len(self.state.player.bench):
                    self.player_bench[i].set_card(self.state.player.bench[i])
                else:
                    self.player_bench[i].set_card(None)
            self.deck_label.setText(f"Deck: {len(self.state.player.deck)}")
            self.discard_label.setText(f"Discard: {len(self.state.player.discard)}")
            self.prize_label.setText(f"Prize: {len(self.state.player.prize)}")
            debug_print("UI updated")
        except Exception as e:
            error_print("Failed to update UI", e)

    def start_drag_from_hand(self, event):
        """Start a drag with card name."""
        try:
            item = self.hand_list.itemAt(event.pos())
            if item:
                mime = QMimeData()
                mime.setText(item.text())
                drag = QDrag(self.hand_list)
                drag.setMimeData(mime)
                debug_print("Started drag:", item.text())
                drag.exec_(Qt.MoveAction)
        except Exception as e:
            error_print("Failed to start drag from hand", e)

    def handle_zone_drop(self, zone, card_name):
        """Move the card from hand to the specified zone (bench/active)."""
        try:
            for idx, card in enumerate(self.state.player.hand):
                if card["name"] == card_name:
                    if zone.zone_name.startswith("Bench"):
                        try:
                            self.state.player.move_hand_to_bench(idx)
                            self.state.log_action(f"Moved {card_name} to bench.")
                            self.update_ui()
                        except Exception as e:
                            QMessageBox.warning(self, "Bench Error", str(e))
                    elif zone.zone_name == "Your Active":
                        if self.state.player.active is None:
                            self.state.player.active = self.state.player.hand.pop(idx)
                            self.state.log_action(f"Promoted {card_name} to active.")
                            self.update_ui()
                        else:
                            QMessageBox.warning(self, "Active Error", "Active spot already filled.")
                    break
        except Exception as e:
            error_print("Failed to handle zone drop", e)

    def attack(self):
        """Player attacks. For demo, just log and take a prize."""
        try:
            self.state.log_action("You attacked!")
            self.state.ai.discard_from_active()
            self.state.player.take_prize()
            self.coach.log_turn(self.state, "attack", True, "Standard attack.")
            self.check_game_end()
            self.update_ui()
        except Exception as e:
            error_print("Attack failed", e)

    def end_turn(self):
        """AI turn: simple move, then back to player."""
        try:
            self.state.log_action("AI's turn...")
            move = self.ai.choose_move(self.state)
            self.state.log_action(f"AI move: {move}")
            self.state.player.discard_from_active()
            self.state.ai.take_prize()
            self.state.log_action("AI attacked and took a prize.")
            self.coach.log_turn(self.state, "ai_attack", True, "AI just attacked.")
            self.state.switch_turn()
            self.check_game_end()
            self.update_ui()
            self.state.switch_turn()
            self.log_area.append("Your turn!")
            if len(self.coach.history) > 0 and len(self.coach.history) % 3 == 0:
                summary = self.coach.summarize_feedback()
                self.log_area.append(f"Coach advice: {summary['tips'][0]}")
        except Exception as e:
            error_print("End turn failed", e)

    def check_game_end(self):
        """Checks if the game has ended and shows the analysis if so."""
        try:
            result = self.state.check_win_conditions()
            if result:
                self.log_area.append(result)
                self.show_analysis()
        except Exception as e:
            error_print("Failed to check for game end", e)

    def show_analysis(self):
        """Show end-game stats and coach advice."""
        try:
            advice = self.coach.summarize_feedback()["tips"]
            msg = "\n".join([
                f"Winner: {self.state.winner}",
                "Game Log:",
                "\n".join(self.state.log),
                "Coach Advice:",
                *advice,
            ])
            debug_print("Game over, showing analysis.")
            QMessageBox.information(self, "Game Over", msg)
            self.close()
        except Exception as e:
            error_print("Failed to show game analysis", e)

def run_board_gui(player_deck, ai_deck):
    import sys
    try:
        app = QApplication(sys.argv)
        window = BoardWindow(player_deck, ai_deck)
        window.show()
        sys.exit(app.exec_())
    except Exception as e:
        error_print("Failed to start board GUI", e)