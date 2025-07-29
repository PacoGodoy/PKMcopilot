"""
engine/game_state.py
Version: 1.2
Last updated: 2025-07-29

Handles all game logic and player states for both the user and AI.
Includes debug logging, robust error handling, and is optimized for rapid testing.
"""

import random
import traceback

DEBUG = True
def debug_print(*args, **kwargs):
    """Print debug messages if DEBUG is enabled."""
    if DEBUG:
        print("[DEBUG][GameState]", *args, **kwargs)

def error_print(msg, exc=None):
    """Print error messages with optional traceback."""
    print("[ERROR][GameState]", msg)
    if exc:
        print(traceback.format_exc())

class PlayerZone:
    """
    Represents all card zones for a player: deck, hand, bench, active, discard, prize.
    All zones are lists of dict objects, except 'active' (single dict or None).
    """
    def __init__(self, decklist):
        """
        Initialize a PlayerZone with a decklist (list of card dicts).
        Shuffles the deck and sets up all play zones.
        """
        try:
            if not isinstance(decklist, list):
                raise ValueError("Decklist must be a list of card dicts.")
            if any(not isinstance(card, dict) for card in decklist):
                raise ValueError("All cards in decklist must be dicts.")
            self.deck = list(decklist)
            random.shuffle(self.deck)
            self.hand = []
            self.bench = []
            self.active = None
            self.discard = []
            self.prize = []
            self.reset_zones()
        except Exception as e:
            error_print("Failed to initialize PlayerZone", e)
            raise

    def reset_zones(self):
        """
        Initializes hand, prizes, active, and bench with robust error handling:
        - Ensures all cards are dicts and have 'supertype'
        - Never pops from a list while iterating
        - Always leaves hand as a list of dicts
        """
        try:
            self.hand = []
            self.prize = []
            self.bench = []
            self.active = None

            # Draw up to 7 cards for hand, 6 for prizes
            for _ in range(7):
                if self.deck:
                    card = self.deck.pop()
                    if not isinstance(card, dict):
                        raise TypeError(f"Deck card is not a dict: {card}")
                    self.hand.append(card)
            for _ in range(6):
                if self.deck:
                    card = self.deck.pop()
                    if not isinstance(card, dict):
                        raise TypeError(f"Deck card is not a dict: {card}")
                    self.prize.append(card)

            # Find first Basic Pokémon for active
            self.active = None
            for idx, card in enumerate(self.hand):
                if not isinstance(card, dict):
                    continue
                if card.get("supertype") == "Pokémon" and card.get("subtype", "").lower() == "basic":
                    self.active = self.hand.pop(idx)
                    break

            # Fill bench with up to 5 more Basic Pokémon
            bench_candidates = []
            for card in self.hand:
                if (
                    isinstance(card, dict)
                    and card.get("supertype") == "Pokémon"
                    and card.get("subtype", "").lower() == "basic"
                ):
                    bench_candidates.append(card)
                    if len(bench_candidates) == 5:
                        break
            for card in bench_candidates:
                self.hand.remove(card)
                self.bench.append(card)

            # Remove any non-dict from hand (shouldn't happen, but extra robust)
            self.hand = [c for c in self.hand if isinstance(c, dict)]
            debug_print("Zones reset: hand size", len(self.hand), "active", self.active["name"] if self.active else None, "bench size", len(self.bench), "prizes", len(self.prize))
        except Exception as e:
            error_print("Failed to robustly reset zones", e)
            raise

    def can_bench(self):
        """Check if bench has capacity for more Pokémon."""
        return len(self.bench) < 5

    def move_hand_to_bench(self, card_idx):
        """
        Move a Pokémon from hand to bench by index.
        Only Basic Pokémon are allowed to bench in most rulesets.
        """
        try:
            if not self.can_bench():
                raise Exception("Bench is full!")
            if card_idx < 0 or card_idx >= len(self.hand):
                raise IndexError("Card index out of range.")
            card = self.hand[card_idx]
            if "Pokémon" not in card.get("supertype", ""):
                raise Exception("You can only bench Pokémon.")
            self.bench.append(card)
            del self.hand[card_idx]
            debug_print("Moved to bench:", card.get("name"))
        except Exception as e:
            error_print(f"Failed to move card to bench: {e}", e)
            raise

    def draw_card(self, n=1):
        """
        Draw n cards from deck to hand.
        Returns True if successful, False if deck out.
        """
        try:
            for _ in range(n):
                if self.deck:
                    card = self.deck.pop()
                    if not isinstance(card, dict):
                        raise TypeError(f"Deck card is not a dict: {card}")
                    self.hand.append(card)
                else:
                    debug_print("Deck out!")
                    return False
            debug_print("Drew card(s), hand now:", [c.get("name") for c in self.hand])
            return True
        except Exception as e:
            error_print("Failed to draw card", e)
            return False

    def discard_from_active(self):
        """
        Move active Pokémon to discard, clear active.
        """
        try:
            if self.active:
                self.discard.append(self.active)
                debug_print("Discarded active:", self.active.get("name"))
                self.active = None
        except Exception as e:
            error_print("Failed to discard active Pokémon", e)
            raise

    def promote_from_bench(self, bench_idx):
        """
        Promote a benched Pokémon to active by index.
        """
        try:
            if not self.bench:
                self.active = None
                return
            if bench_idx < 0 or bench_idx >= len(self.bench):
                raise IndexError("Bench index out of range.")
            self.active = self.bench.pop(bench_idx)
            debug_print("Promoted to active:", self.active.get("name"))
        except Exception as e:
            error_print("Failed to promote Pokémon from bench", e)
            raise

    def take_prize(self):
        """
        Take one prize card (on KO).
        """
        try:
            if self.prize:
                card = self.prize.pop()
                self.hand.append(card)
                debug_print("Prize taken, prizes left:", len(self.prize))
        except Exception as e:
            error_print("Failed to take prize card", e)
            raise

    def lose(self):
        """
        Check if the player has lost
        (deck out or no active and no bench Pokémon).
        """
        try:
            result = not self.deck or (self.active is None and not self.bench)
            if result:
                debug_print("Lose detected")
            return result
        except Exception as e:
            error_print("Error in lose() check", e)
            return True

class GameState:
    """
    Manages two PlayerZone objects (user and AI), and tracks turn/phase.
    """
    def __init__(self, player_deck, ai_deck):
        """
        Set up the game state with provided decks.
        """
        try:
            self.player = PlayerZone(player_deck)
            self.ai = PlayerZone(ai_deck)
            self.turn = "player"
            self.log = []
            self.game_over = False
            self.winner = None
        except Exception as e:
            error_print("Failed to initialize GameState", e)
            raise

    def switch_turn(self):
        """Switches the turn from player to AI or vice versa."""
        try:
            self.turn = "ai" if self.turn == "player" else "player"
            debug_print("Turn switched to", self.turn)
        except Exception as e:
            error_print("Failed to switch turn", e)

    def get_current_player(self):
        """Returns the PlayerZone for the current turn."""
        return self.player if self.turn == "player" else self.ai

    def get_opponent(self):
        """Returns the PlayerZone for the opponent."""
        return self.ai if self.turn == "player" else self.player

    def check_win_conditions(self):
        """
        Check for any win/loss conditions.
        Returns a string if there is an end condition, else None.
        """
        try:
            if self.player.lose():
                self.game_over = True
                self.winner = "AI"
                return "Deck out or no Pokémon. You lose!"
            if self.ai.lose():
                self.game_over = True
                self.winner = "Player"
                return "Opponent decked out or no Pokémon. You win!"
            if not self.player.prize:
                self.game_over = True
                self.winner = "Player"
                return "You took all prizes! You win!"
            if not self.ai.prize:
                self.game_over = True
                self.winner = "AI"
                return "AI took all prizes. You lose!"
            return None
        except Exception as e:
            error_print("Error checking win conditions", e)
            self.game_over = True
            self.winner = "Error"
            return "Critical error: Game ended unexpectedly."

    def log_action(self, msg):
        """Log an action to the game log with debug print."""
        try:
            debug_print("LOG:", msg)
            self.log.append(msg)
        except Exception as e:
            error_print("Failed to log action", e)