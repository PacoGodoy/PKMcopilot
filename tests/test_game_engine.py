import unittest
import os
from engine import game_logic

class TestGameLogic(unittest.TestCase):
    def setUp(self):
        # Use sample deck files included in data/decklists/
        self.player_deck = game_logic.load_deck("Ragingbolt_v1")
        self.ai_deck = game_logic.load_deck("Grims_ivanv1")
        self.game_state = game_logic.GameState(self.player_deck, self.ai_deck)

    def test_deck_loading(self):
        self.assertTrue(len(self.player_deck) > 0)
        self.assertTrue(len(self.ai_deck) > 0)

    def test_game_state_initialization(self):
        self.assertEqual(self.game_state.phase, "start")
        self.assertIsInstance(self.game_state.player_deck, list)
        self.assertIsInstance(self.game_state.ai_deck, list)

    def test_start_new_game(self):
        state = game_logic.start_new_game("Ragingbolt_v1", "Grims_ivanv1")
        self.assertIsInstance(state, game_logic.GameState)

    def test_advance_phase(self):
        self.game_state.advance_phase()
        # Stub: Just ensure no crash
        self.assertTrue(True)

    def test_is_game_over(self):
        self.assertFalse(self.game_state.is_game_over())

if __name__ == "__main__":
    unittest.main()