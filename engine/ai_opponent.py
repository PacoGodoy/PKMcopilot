"""
engine/ai_opponent.py
Version: 1.1
Last updated: 2025-07-29

Simple AI logic: makes basic moves, benches Pokémon, attacks, or draws cards if needed.
Includes debug output and error handling.
"""

import random
import traceback

DEBUG = True
def debug_print(*args, **kwargs):
    if DEBUG:
        print("[DEBUG][AI]", *args, **kwargs)

def error_print(msg, exc=None):
    print("[ERROR][AI]", msg)
    if exc:
        print(traceback.format_exc())

class AIOpponent:
    def __init__(self, decklist):
        self.decklist = decklist

    def choose_move(self, state):
        """Decides on a move for the AI. Tries to bench Pokémon if possible, otherwise attacks."""
        try:
            zone = state.ai
            if zone.can_bench():
                for idx, card in enumerate(zone.hand):
                    if "Pokémon" in card.get("supertype", ""):
                        zone.move_hand_to_bench(idx)
                        state.log_action("AI benched a Pokémon.")
                        debug_print("Benched Pokémon:", card.get("name"))
                        return "Bench Pokémon"
            state.log_action("AI attacks.")
            debug_print("Attacked")
            return "Attack"
        except Exception as e:
            error_print("AI move error", e)
            state.log_action("AI move error: " + str(e))
            return "Error"