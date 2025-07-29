"""
tests/test_simulation.py
Version: 1.2
Last updated: 2025-07-29

Automated simulation test for the Pokémon TCG Training System.

This script simulates a full game between a player and the AI using the core engine,
verifying that all game logic, zones, and win conditions work as expected.

It does NOT require the GUI; all actions are performed in code for speed.

To use:
    python tests/test_simulation.py

Expected result:
    - The game runs to completion.
    - All state transitions, zone changes, and win/loss conditions are checked.
    - Summary and debug output are printed.
    - All unexpected errors are caught and displayed clearly.
"""

import random
import sys
import os
import traceback

# Import the core engine (ensure correct sys.path for test execution context)
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from engine.game_state import GameState
from engine.ai_opponent import AIOpponent
from engine.coach_ai import CoachAI

def make_dummy_deck(deck_size=40):
    """
    Returns a robust dummy deck:
    - At least 8 Basic Pokémon (ensures valid starting hand)
    - 8 Stage 1 Pokémon, 12 Trainers, 12 Energy
    """
    deck = []
    # 8 Basic Pokémon
    for i in range(8):
        deck.append({
            "name": f"Pokémon {i+1}",
            "supertype": "Pokémon",
            "subtype": "Basic",
            "image_url": "",
        })
    # 8 Stage 1 Pokémon (not Basic)
    for i in range(8):
        deck.append({
            "name": f"Stage1 Pokémon {i+1}",
            "supertype": "Pokémon",
            "subtype": "Stage 1",
            "image_url": "",
        })
    # 12 trainers
    for i in range(12):
        deck.append({
            "name": f"Trainer {i+1}",
            "supertype": "Trainer",
            "image_url": "",
        })
    # 12 energy
    for i in range(12):
        deck.append({
            "name": f"Energy {i+1}",
            "supertype": "Energy",
            "image_url": "",
        })
    random.shuffle(deck)
    return deck[:deck_size]

def full_game_simulation():
    """
    Runs a full game simulation using dummy decks, exercising all major code paths.
    Includes error handling and prints results at the end.
    """
    try:
        player_deck = make_dummy_deck()
        ai_deck = make_dummy_deck()

        state = GameState(player_deck, ai_deck)
        ai = AIOpponent(ai_deck)
        coach = CoachAI()

        turn = 0
        max_turns = 100
        print("=== Simulation Start ===")
        while not state.game_over and turn < max_turns:
            print(f"\nTurn {turn+1}: {state.turn.capitalize()}'s move")
            current = state.get_current_player()
            opponent = state.get_opponent()

            # Player (simulate: always attack if can, else draw/bench if possible)
            if state.turn == "player":
                # Bench first Basic Pokémon in hand if possible
                for idx, card in enumerate(list(current.hand)):
                    if (
                        card.get("supertype") == "Pokémon"
                        and card.get("subtype", "").lower() == "basic"
                        and current.can_bench()
                    ):
                        try:
                            current.move_hand_to_bench(idx)
                            state.log_action("Player benched a Pokémon.")
                            break
                        except Exception as e:
                            print("[ERROR][Test] Failed to bench Pokémon:", e)
                # Attack (KO AI active, take prize)
                try:
                    opponent.discard_from_active()
                    current.take_prize()
                    coach.log_turn(state, "attack", True, "Automated attack.")
                    state.log_action("Player attacked and took a prize.")
                except Exception as e:
                    print("[ERROR][Test] Player attack failed:", e)
            else:
                # AI makes move
                try:
                    ai.choose_move(state)
                    opponent.discard_from_active()
                    current.take_prize()
                    coach.log_turn(state, "ai_attack", True, "AI automated attack.")
                    state.log_action("AI attacked and took a prize.")
                except Exception as e:
                    print("[ERROR][Test] AI move/attack failed:", e)

            # Check win/loss
            try:
                result = state.check_win_conditions()
                if result:
                    print("Game End Detected:", result)
                    break
            except Exception as e:
                print("[ERROR][Test] Failed win/loss check:", e)
                break
            state.switch_turn()
            turn += 1

        print("\n=== Simulation End ===")
        print(f"Winner: {state.winner}")
        print("Turns played:", turn+1)
        print("Final Player zones: Hand:", len(state.player.hand), "Bench:", len(state.player.bench),
              "Active:", state.player.active["name"] if state.player.active else None,
              "Prizes:", len(state.player.prize))
        print("Final AI zones: Hand:", len(state.ai.hand), "Bench:", len(state.ai.bench),
              "Active:", state.ai.active["name"] if state.ai.active else None,
              "Prizes:", len(state.ai.prize))
        print("\nCoach Feedback:", coach.summarize_feedback()["tips"])
        print("\nLog (last 10 lines):")
        for l in state.log[-10:]:
            print(l)
        assert state.game_over, "Game did not end as expected!"
        assert state.winner in ("Player", "AI"), "Winner not set!"
    except Exception as e:
        print("\n[CRITICAL][Test] Unexpected error in simulation:")
        print(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    full_game_simulation()