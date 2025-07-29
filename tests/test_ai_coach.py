import unittest
from engine import coach_ai

class TestCoachAI(unittest.TestCase):
    def setUp(self):
        self.coach = coach_ai.CoachAI()

    def test_log_turn_and_feedback(self):
        self.coach.log_turn(
            game_state="mock_state",
            move="attack",
            is_optimal=True,
            reasoning="Best move"
        )
        self.coach.log_turn(
            game_state="mock_state",
            move="pass",
            is_optimal=False,
            reasoning="Missed KO opportunity"
        )
        summary = self.coach.summarize_feedback()
        self.assertIn("optimal_moves", summary)
        self.assertIn("suboptimal_moves", summary)
        self.assertIn("common_errors", summary)
        self.assertIsInstance(summary["tips"], list)

    def test_reset(self):
        self.coach.log_turn("state", "move", True, "reason")
        self.assertTrue(len(self.coach.history) > 0)
        self.coach.reset()
        self.assertEqual(len(self.coach.history), 0)

if __name__ == "__main__":
    unittest.main()