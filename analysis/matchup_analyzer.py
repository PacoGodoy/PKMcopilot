import pandas as pd
import os

REPORTS_PATH = "reports"

class MatchupAnalyzer:
    def __init__(self, player_name):
        self.player_name = player_name
        self.details_file = os.path.join(REPORTS_PATH, f"detail_{player_name}.csv")

    def generate_heatmap_matrix(self):
        """Produces a matrix: player deck vs meta deck winrates."""
        if not os.path.exists(self.details_file):
            print("No detailed match data found for analysis.")
            return None
        df = pd.read_csv(self.details_file)
        matrix = pd.pivot_table(
            df,
            values='result',
            index='player_deck',
            columns='opponent_deck',
            aggfunc=lambda results: sum(x == "Win" for x in results) / len(results)
        )
        return matrix

    def get_matchup_stats(self, player_deck, opponent_deck):
        """Return winrate for given matchup."""
        if not os.path.exists(self.details_file):
            return 0.0
        df = pd.read_csv(self.details_file)
        subset = df[
            (df['player_deck'] == player_deck) &
            (df['opponent_deck'] == opponent_deck)
        ]
        if len(subset) == 0:
            return 0.0
        return sum(subset['result'] == "Win") / len(subset)

    def get_common_opponent_decks(self):
        if not os.path.exists(self.details_file):
            return []
        df = pd.read_csv(self.details_file)
        return list(df['opponent_deck'].value_counts().keys())