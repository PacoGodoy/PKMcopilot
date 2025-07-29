"""
gui/card_zone.py
Version: 1.1
Last updated: 2025-07-29

CardZone is a QLabel that can accept drag-and-drop of card names, and display images.
Includes debug logging and error handling.
"""

from PyQt5.QtWidgets import QLabel
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap
import traceback

DEBUG = True
def debug_print(*args, **kwargs):
    if DEBUG:
        print("[DEBUG][ZONE]", *args, **kwargs)

def error_print(msg, exc=None):
    print("[ERROR][ZONE]", msg)
    if exc:
        print(traceback.format_exc())

class CardZone(QLabel):
    def __init__(self, zone_name, parent=None):
        try:
            super().__init__(zone_name, parent)
            self.setAcceptDrops(True)
            self.setAlignment(Qt.AlignCenter)
            self.zone_name = zone_name
            self.card = None
        except Exception as e:
            error_print("Failed to initialize CardZone", e)
            raise

    def set_card(self, card):
        """Display card image if available, else name."""
        try:
            self.card = card
            if card and card.get('image_url'):
                pixmap = QPixmap()
                pixmap.loadFromData(self.parent().load_card_image(card['image_url']))
                self.setPixmap(pixmap.scaled(100, 140, Qt.KeepAspectRatio))
                self.setText("")
                debug_print(f"Set image for {self.zone_name}: {card.get('name')}")
            elif card:
                self.setText(card["name"])
                self.setPixmap(QPixmap())
                debug_print(f"Set text for {self.zone_name}: {card.get('name')}")
            else:
                self.setText(self.zone_name)
                self.setPixmap(QPixmap())
                debug_print(f"Cleared {self.zone_name}")
        except Exception as e:
            error_print("Failed to set card in CardZone", e)

    def dragEnterEvent(self, event):
        try:
            if event.mimeData().hasText():
                event.acceptProposedAction()
            else:
                event.ignore()
        except Exception as e:
            error_print("Drag enter event failed", e)

    def dropEvent(self, event):
        try:
            card_name = event.mimeData().text()
            debug_print(f"Dropped {card_name} on {self.zone_name}")
            self.parent().handle_zone_drop(self, card_name)
            event.acceptProposedAction()
        except Exception as e:
            error_print("Drop event failed", e)