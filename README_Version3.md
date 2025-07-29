# Pokémon TCG Training System with AI

## Features

- Full official Pokémon TCG rules simulation (Standard format)
- Drag-and-drop PyQt5 GUI (light theme, custom brand-ready)
- Advanced AI opponent (scripted + ML-ready, adapts by deck/archetype)
- Coach AI: Turn-by-turn feedback, playstyle, phase performance, common errors, recommendations
- Auto-import all legal cards from pokemontcg.io (API key required)
- Meta deck and player deck management (.json format)
- Reporting: .txt/.csv and graphs (.png) for all key metrics
- Modular, extensible architecture

## Quickstart

1. **Install dependencies**
   ```
   pip install pyqt5 pandas matplotlib seaborn requests SQLAlchemy scikit-learn torch
   ```

2. **Initialize database and import cards**
   ```
   python data/init_db.py
   python scraper/card_importer.py
   ```

3. **Run the app**
   ```
   python main.py
   ```

## Folder Structure

```
project_root/
│
├── data/
│   ├── cards.db
│   ├── decklists/
│   │   ├── Ragingbolt_v1.json
│   │   ├── Grims_ivanv1.json
│   │   └── gardevoir_V1.json
│   └── player_profiles/
│       └── sample_player.json
│
├── engine/
│   ├── game_logic.py
│   ├── rules_checker.py
│   ├── ai_opponent.py
│   └── coach_ai.py
│
├── gui/
│   ├── board.py
│   ├── player_input.py
│   └── display_utils.py
│
├── analysis/
│   ├── style_profiler.py
│   ├── matchup_analyzer.py
│   └── card_recommender.py
│
├── scraper/
│   └── card_importer.py
│
├── reports/
│   ├── summary_player_01.txt
│   ├── detail_player_01.csv
│   ├── recommendations_player_01.txt
│   └── graphics/
│       ├── winrate_by_deck.png
│       ├── phase_performance.png
│       ├── common_errors.png
│       ├── matchup_heatmap.png
│       └── style_distribution.png
│
├── tests/
│   ├── test_game_engine.py
│   ├── test_ai_coach.py
│   └── test_card_importer.py
│
└── main.py
```

## Decklist Format

All decklists use this JSON format (see `/data/decklists/`).

```json
{
  "cards": [
    { "name": "Card Name", "set": "SETCODE", "number": "CARDNUMBER", "category": "pokemon|trainer|energy", "count": 4 },
    ...
  ]
}
```

## Manual Card Entry

If a card is missing, supply JSON:
```json
{
  "id": "custom-id",
  "name": "Card Name",
  "supertype": "Pokemon|Trainer|Energy",
  "subtype": "Basic|Stage 1|Item|Stadium|...",
  "hp": 120,
  "types": ["Psychic"],
  "retreatCost": 2,
  "attacks": [...],
  "abilities": [...],
  "rules": "...",
  "expansion": "SVI",
  "number": "84",
  "rarity": "Rare",
  "image_url": "",
  "source": "manual"
}
```

## Extending

- Add decks to `/data/decklists/`
- Add card images to `/data/images/` (future support)
- Add analysis plugins to `/analysis/`

## License

MIT
