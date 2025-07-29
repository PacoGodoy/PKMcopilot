import os
import json

DECKLISTS_PATH = "data/decklists"

def load_deck(deck_name):
    """Load a deck from its JSON file."""
    deck_file = os.path.join(DECKLISTS_PATH, f"{deck_name}.json")
    with open(deck_file, encoding="utf-8") as f:
        deck_data = json.load(f)
    return deck_data["cards"]

def initialize_game_engine():
    # Example: Load available decks and prepare state
    available_decks = [
        fname.replace(".json", "")
        for fname in os.listdir(DECKLISTS_PATH)
        if fname.endswith(".json")
    ]
    print(f"Available decks: {available_decks}")
    # Extend this to initialize the game state, shuffle decks, etc.

class GameState:
    def __init__(self, player_deck, ai_deck):
        self.player_deck = player_deck
        self.ai_deck = ai_deck
        self.board = {}  # Placeholder for full board state
        self.phase = "start"

    def advance_phase(self):
        # Stub: Move to the next game phase
        pass

    def is_game_over(self):
        # Stub: Check win/loss condition
        return False

    def apply_move(self, move):
        # Stub: Apply a move/action to the board state
        pass

def start_new_game(player_deck_name, ai_deck_name):
    player_deck = load_deck(player_deck_name)
    ai_deck = load_deck(ai_deck_name)
    state = GameState(player_deck, ai_deck)
    return state