import collections

PLAYSTYLE_LABELS = [
    "control",
    "aggro",
    "stall",
    "toolbox",
    "tempo",
    "combo",
    "one-prizer",
    "two-/three-prizer"
]

class StyleProfiler:
    def __init__(self):
        self.turn_data = []

    def log_turn(self, turn_info):
        """turn_info: dict, e.g. {'phase': 'mid', 'action': 'attack', 'card': 'Boss', ...}"""
        self.turn_data.append(turn_info)

    def detect_playstyle(self):
        # Simple heuristic: count actions/decisions by type
        actions = [t["action"] for t in self.turn_data]
        action_counts = collections.Counter(actions)
        # Example rules (expand for depth)
        if action_counts.get("disrupt", 0) > 3:
            return "control"
        if action_counts.get("attack", 0) > 8 and action_counts.get("setup", 0) < 3:
            return "aggro"
        if action_counts.get("heal", 0) > 3 or action_counts.get("wall", 0) > 1:
            return "stall"
        if action_counts.get("tool", 0) > 5 or action_counts.get("switch", 0) > 4:
            return "toolbox"
        # Fallback
        return "tempo"

    def get_action_breakdown(self):
        return collections.Counter([t["action"] for t in self.turn_data])

    def reset(self):
        self.turn_data = []