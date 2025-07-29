import collections
from typing import Dict, List, Optional, Any
from .card_analyzer import CardAnalyzer

class CardRecommender:
    def __init__(self):
        self.history = []
        self.analyzer = None
        
    def initialize_analyzer(self):
        """Initialize the comprehensive card analyzer if not already done"""
        if self.analyzer is None:
            try:
                self.analyzer = CardAnalyzer()
                print("CardAnalyzer integrated successfully")
            except Exception as e:
                print(f"Failed to initialize CardAnalyzer: {e}")
                self.analyzer = None

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
        
        # Enhanced suggestions using comprehensive analyzer
        if self.analyzer is None:
            self.initialize_analyzer()
            
        if self.analyzer is not None:
            try:
                enhanced_suggestions = self._get_enhanced_suggestions(decklist, error_stats)
                suggestions.extend(enhanced_suggestions)
            except Exception as e:
                print(f"Enhanced suggestions failed: {e}")
                
        return suggestions
    
    def _get_enhanced_suggestions(self, decklist, error_stats):
        """Get enhanced suggestions using the comprehensive analyzer"""
        suggestions = []
        
        try:
            # Extract card features for analysis
            card_features = self.analyzer.extract_card_features()
            
            # Analyze synergies in the current decklist
            synergy_analysis = self.analyzer.detect_synergies(decklist, card_features)
            
            # Convert analyzer recommendations to card recommender format
            for rec in synergy_analysis.recommendations:
                if rec['type'] == 'inclusion':
                    suggestions.append({
                        "out": "Consider adding",
                        "in": rec['suggestion'],
                        "reason": f"[AI Analysis] {rec['reason']}"
                    })
                elif rec['type'] == 'exclusion':
                    suggestions.append({
                        "out": rec['suggestion'],
                        "in": "Better synergy card",
                        "reason": f"[AI Analysis] {rec['reason']}"
                    })
            
            # Add archetype-specific suggestions
            primary_archetype = max(synergy_analysis.archetype_fit.items(), key=lambda x: x[1])
            if primary_archetype[1] > 0.5:
                suggestions.append({
                    "out": "General cards",
                    "in": f"{primary_archetype[0].title()} cards",
                    "reason": f"[AI Analysis] Deck fits {primary_archetype[0]} archetype ({primary_archetype[1]:.1%} confidence)"
                })
                
        except Exception as e:
            print(f"Enhanced analysis failed: {e}")
            
        return suggestions

    def summarize_recommendations(self, deck_name):
        # Stub: Compile global deck suggestions for reporting
        return [
            f"Replace Ultra Ball with Battle VIP Pass for better early-game setup.",
            f"Consider trimming Stage 2 lines if consistent evolution is not achieved by Turn 4."
        ]