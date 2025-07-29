import sqlite3
import csv

DB_PATH = "data/cards.db"
CSV_PATH = "data/all_cards_export.csv"

def export_cards_to_csv(db_path=DB_PATH, csv_path=CSV_PATH):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM cards")
    columns = [desc[0] for desc in cursor.description]
    rows = cursor.fetchall()

    with open(csv_path, "w", newline='', encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(columns)
        writer.writerows(rows)

    print(f"Exported {len(rows)} cards to {csv_path}")

if __name__ == "__main__":
    export_cards_to_csv()