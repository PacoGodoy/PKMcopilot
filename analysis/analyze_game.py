"""
analysis/analyze_game.py
Version: 1.1
Last updated: 2025-07-29

Performs analytic routines over game logs and player actions.
Includes robust error handling and debug logging.
"""

import traceback

DEBUG = True
def debug_print(*args, **kwargs):
    if DEBUG:
        print("[DEBUG][ANALYSIS]", *args, **kwargs)

def error_print(msg, exc=None):
    print("[ERROR][ANALYSIS]", msg)
    if exc:
        print(traceback.format_exc())

def analyze_turns(game_log):
    """
    Analyze player and AI turns from the game log.
    Returns a dictionary with summary statistics.
    """
    try:
        debug_print("Analyzing turns...")
        player_turns = [entry for entry in game_log if "Player" in entry]
        ai_turns = [entry for entry in game_log if "AI" in entry]
        debug_print(f"Player turns: {len(player_turns)}, AI turns: {len(ai_turns)}")
        return {
            "player_turns": len(player_turns),
            "ai_turns": len(ai_turns),
        }
    except Exception as e:
        error_print("Failed to analyze turns", e)
        return {}

def most_common_action(game_log):
    """
    Analyzes the log to find the most common action type.
    """
    try:
        from collections import Counter
        actions = []
        for entry in game_log:
            if "attack" in entry:
                actions.append("attack")
            elif "bench" in entry:
                actions.append("bench")
            elif "draw" in entry:
                actions.append("draw")
        count = Counter(actions)
        most = count.most_common(1)[0] if count else ("None", 0)
        debug_print("Most common action:", most)
        return most
    except Exception as e:
        error_print("Failed to compute most common action", e)
        return ("Error", 0)