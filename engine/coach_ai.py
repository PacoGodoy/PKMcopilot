"""
engine/coach_ai.py
Version: 1.1
Last updated: 2025-07-29

CoachAI tracks player actions, logs basic mistakes, and provides advice.
Includes debug output and error handling.
"""

import traceback

DEBUG = True
def debug_print(*args, **kwargs):
    if DEBUG:
        print("[DEBUG][COACH]", *args, **kwargs)

def error_print(msg, exc=None):
    print("[ERROR][COACH]", msg)
    if exc:
        print(traceback.format_exc())

class CoachAI:
    def __init__(self):
        self.history = []

    def log_turn(self, state, action, optimal, note):
        """Logs a turn for analysis and advice."""
        try:
            debug_print("Turn log:", action, optimal, note)
            self.history.append({"action": action, "optimal": optimal, "note": note})
        except Exception as e:
            error_print("Failed to log coach turn", e)

    def summarize_feedback(self):
        """Summarizes feedback for the player."""
        try:
            tips = []
            for item in self.history:
                if not item["optimal"]:
                    tips.append(f"Consider: {item['note']}")
            if not tips:
                tips.append("Keep it up! No major mistakes detected.")
            debug_print("Advice tips:", tips)
            return {"tips": tips}
        except Exception as e:
            error_print("Failed to summarize feedback", e)
            return {"tips": ["Error generating feedback."]}