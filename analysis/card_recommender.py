import collections

class CardRecommender:
    def __init__(self):
        self.history = []

    def log_game(self, deck, turns, errors, missed_setups):
        self.history.append({
            "deck": deck,
            "turns": turns,
            "errors": errors,
            "missed_setups": missed_setups
        })

    def suggest_replacements(self, decklist, error_stats):
        # Example rules: If error in setup, suggest more search/draw; if stuck on energy, add more energy/search
        suggestions = []
        if error_stats.get("setup_missed", 0) > 3:
            suggestions.append({
                "out": "Basic Pokémon",
                "in": "Battle VIP Pass",
                "reason": "Improve early board setup consistency."
            })
        if error_stats.get("resource_starved", 0) > 2:
            suggestions.append({
                "out": "Supporter",
                "in": "Professor's Research",
                "reason": "Boost draw power for mid-game recovery."
            })
        # Example: Remove dead cards
        dead_cards = [c for c, v in error_stats.get("dead_cards", {}).items() if v > 2]
        for card in dead_cards:
            suggestions.append({
                "out": card,
                "in": "Nest Ball",
                "reason": f"{card} was often dead in hand."
            })
        return suggestions

    def summarize_recommendations(self, deck_name):
        # Stub: Compile global deck suggestions for reporting
        return [
            f"Replace Ultra Ball with Battle VIP Pass for better early-game setup.",
            f"Consider trimming Stage 2 lines if consistent evolution is not achieved by Turn 4."
        ]