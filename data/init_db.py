import sqlite3

def initialize_database(db_path="data/cards.db"):
    con = sqlite3.connect(db_path)
    cur = con.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS cards (
        card_id TEXT PRIMARY KEY,
        name TEXT,
        supertype TEXT,
        subtype TEXT,
        hp INTEGER,
        types TEXT,
        retreat_cost INTEGER,
        attacks TEXT,
        abilities TEXT,
        rules TEXT,
        expansion TEXT,
        number TEXT,
        rarity TEXT,
        image_url TEXT,
        source TEXT
    );
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS players (
        player_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        date_created TEXT DEFAULT CURRENT_TIMESTAMP
    );
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS decklists (
        deck_id INTEGER PRIMARY KEY AUTOINCREMENT,
        player_id INTEGER,
        deck_name TEXT,
        style_detected TEXT,
        date_created TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (player_id) REFERENCES players(player_id)
    );
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS deck_cards (
        deck_id INTEGER,
        card_id TEXT,
        quantity INTEGER,
        PRIMARY KEY (deck_id, card_id),
        FOREIGN KEY (deck_id) REFERENCES decklists(deck_id),
        FOREIGN KEY (card_id) REFERENCES cards(card_id)
    );
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS matches (
        match_id INTEGER PRIMARY KEY AUTOINCREMENT,
        player_id INTEGER,
        deck_id INTEGER,
        opponent_deck TEXT,
        result TEXT CHECK(result IN ('Win', 'Loss')),
        misplay_flag BOOLEAN,
        turns_played INTEGER,
        phase_performance TEXT,
        ai_feedback TEXT,
        timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (player_id) REFERENCES players(player_id),
        FOREIGN KEY (deck_id) REFERENCES decklists(deck_id)
    );
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS turn_logs (
        log_id INTEGER PRIMARY KEY AUTOINCREMENT,
        match_id INTEGER,
        turn_number INTEGER,
        player TEXT CHECK(player IN ('self', 'ai')),
        action TEXT,
        card_used TEXT,
        target_card TEXT,
        was_optimal BOOLEAN,
        reasoning TEXT,
        FOREIGN KEY (match_id) REFERENCES matches(match_id)
    );
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS meta_decks (
        meta_deck_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        archetype TEXT,
        version TEXT,
        decklist TEXT
    );
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS recommendations (
        recommendation_id INTEGER PRIMARY KEY AUTOINCREMENT,
        deck_id INTEGER,
        card_out TEXT,
        card_in TEXT,
        reason TEXT,
        date TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (deck_id) REFERENCES decklists(deck_id)
    );
    """)
    con.commit()
    con.close()

if __name__ == "__main__":
    initialize_database()