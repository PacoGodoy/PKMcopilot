import os
import requests
import sqlite3
import json
import time
from typing import Optional, List

DB_PATH = "data/cards.db"
API_URL = "https://api.pokemontcg.io/v2/cards"
DEFAULT_API_KEY = "11ac24b1-3a85-4fde-aac8-88077c503e75"
ERROR_LOG_PATH = "data/import_errors.log"

def log_error(log_file: str, card: Optional[dict], error: Exception, stage: str = "insert", extra_context: str = ""):
    """
    Write a detailed error log entry.
    """
    try:
        with open(log_file, "a", encoding="utf-8") as f:
            f.write("="*60 + "\n")
            f.write(f"Stage: {stage}\n")
            if card:
                f.write(f"Card Name: {card.get('name', 'Unknown')}\n")
                f.write(f"Card ID: {card.get('id', 'Unknown')}\n")
            if extra_context:
                f.write(f"Extra Context: {extra_context}\n")
            f.write(f"Error Type: {type(error).__name__}\n")
            f.write(f"Error Message: {str(error)}\n")
            if card:
                f.write("Card Data: " + json.dumps(card, ensure_ascii=False) + "\n")
            f.write("="*60 + "\n\n")
    except Exception as log_exc:
        print(f"Failed to write to log {log_file}: {log_exc}")

def fetch_cards(api_key: str, page_size: int = 250) -> List[dict]:
    """
    Generator to fetch all cards in batches from the API.
    """
    headers = {"X-Api-Key": api_key}
    page = 1
    while True:
        params = {"page": page, "pageSize": page_size}
        response = requests.get(API_URL, headers=headers, params=params)
        if response.status_code != 200:
            raise Exception(f"API fetch error: Status {response.status_code} - {response.text}")
        data = response.json()
        cards = data.get("data", [])
        if not cards:
            break
        yield from cards
        if len(cards) < page_size:
            break
        page += 1
        time.sleep(0.5)  # Be polite to the API

def normalize_card_for_db(card: dict) -> tuple:
    """
    Prepare card data for DB insert.
    Handles retreat cost, attacks, abilities, etc.
    """
    # Normalize retreat cost
    retreat_cost = card.get("retreatCost", [])
    if isinstance(retreat_cost, list):
        retreat_cost_val = len(retreat_cost)
    else:
        try:
            retreat_cost_val = int(retreat_cost)
        except Exception:
            retreat_cost_val = None

    # Normalize types
    card_types = card.get("types", [])
    if isinstance(card_types, list):
        card_types_str = ",".join(card_types)
    else:
        card_types_str = str(card_types) if card_types else ""

    # Normalize attacks and abilities as JSON
    attacks = json.dumps(card.get("attacks", []), ensure_ascii=False)
    abilities = json.dumps(card.get("abilities", []), ensure_ascii=False)
    rules = " | ".join(card.get("rules", [])) if card.get("rules") else ""

    return (
        card.get("id"),
        card.get("name"),
        card.get("supertype"),
        card.get("subtypes", [None])[0] if card.get("subtypes") else None,
        card.get("hp"),
        card_types_str,
        retreat_cost_val,
        attacks,
        abilities,
        rules,
        card.get("set", {}).get("name"),
        card.get("number"),
        card.get("rarity"),
        card.get("images", {}).get("large") or card.get("images", {}).get("small"),
        "api"
    )

def update_card_db(api_key: Optional[str] = None, db_path: str = DB_PATH, error_log_path: str = ERROR_LOG_PATH) -> List[str]:
    """
    Imports cards from PokémonTCG.io API to local DB.
    Logs errors in detail.
    Returns a list of error strings (empty if all OK).
    """
    api_key = api_key or DEFAULT_API_KEY

    if not os.path.exists(os.path.dirname(db_path)):
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
    if not os.path.exists(os.path.dirname(error_log_path)):
        os.makedirs(os.path.dirname(error_log_path), exist_ok=True)

    errors = []
    n_ok = 0
    n_total = 0

    # Connect to DB
    con = sqlite3.connect(db_path)
    cur = con.cursor()

    # Prepare insert statement
    sql = """INSERT OR REPLACE INTO cards (
        card_id, name, supertype, subtype, hp, types, retreat_cost,
        attacks, abilities, rules, expansion, number, rarity, image_url, source
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"""

    # Fetch and insert cards
    for card in fetch_cards(api_key):
        n_total += 1
        try:
            row = normalize_card_for_db(card)
            cur.execute(sql, row)
            n_ok += 1
        except Exception as e:
            error_line = f"Failed to import card {card.get('name', 'Unknown')} (ID: {card.get('id', 'Unknown')}): {e}"
            errors.append(error_line)
            log_error(error_log_path, card, e, stage="insert")
    con.commit()
    con.close()

    # Summary log
    try:
        with open(error_log_path, "a", encoding="utf-8") as f:
            f.write(f"Import summary: {n_ok} cards imported successfully, {len(errors)} errors out of {n_total} total cards.\n")
    except Exception as log_exc:
        print(f"Failed to write to log {error_log_path}: {log_exc}")

    return errors

def manual_card_entry(card_data: dict, db_path: str = DB_PATH):
    """
    Insert a single card manually (for tests).
    """
    con = sqlite3.connect(db_path)
    cur = con.cursor()
    sql = """INSERT OR REPLACE INTO cards (
        card_id, name, supertype, subtype, hp, types, retreat_cost,
        attacks, abilities, rules, expansion, number, rarity, image_url, source
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"""
    row = (
        card_data.get("id"),
        card_data.get("name"),
        card_data.get("supertype"),
        card_data.get("subtype"),
        card_data.get("hp"),
        ",".join(card_data.get("types", [])) if card_data.get("types") else "",
        card_data.get("retreatCost", 0) if isinstance(card_data.get("retreatCost", 0), int) else len(card_data.get("retreatCost", [])),
        card_data.get("attacks"),
        card_data.get("abilities"),
        card_data.get("rules"),
        card_data.get("expansion"),
        card_data.get("number"),
        card_data.get("rarity"),
        card_data.get("image_url"),
        card_data.get("source", "manual")
    )
    cur.execute(sql, row)
    con.commit()
    con.close()

if __name__ == "__main__":
    # Run full import and print summary
    errors = update_card_db(api_key=DEFAULT_API_KEY)
    if errors:
        print(f"Import completed with {len(errors)} errors. See {ERROR_LOG_PATH}")
    else:
        print("All cards imported successfully!")