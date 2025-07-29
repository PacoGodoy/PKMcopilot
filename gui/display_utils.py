from PyQt5.QtGui import QColor

def get_zone_color(zone):
    # Light theme colors for different game zones
    colors = {
        "active": QColor(200, 250, 200),
        "bench": QColor(230, 230, 255),
        "hand": QColor(255, 250, 200),
        "deck": QColor(220, 220, 220),
        "discard": QColor(255, 200, 200),
        "prize": QColor(255, 240, 220),
        "stadium": QColor(210, 230, 210)
    }
    return colors.get(zone, QColor(240, 240, 240))