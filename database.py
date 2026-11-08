
import sqlite3
from pathlib import Path
from contextlib import closing

DB_PATH = Path(__file__).resolve().parent / "sightings.db"


def init_db():
    with closing(sqlite3.connect(DB_PATH)) as conn:
        with conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS sightings (
                    id TEXT PRIMARY KEY,
                    date TEXT NOT NULL,
                    location TEXT NOT NULL,
                    species TEXT NOT NULL,
                    latinName TEXT NOT NULL
                )
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_location
                ON sightings(location)
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_date
                ON sightings(date)
            """)


def save_sightings(sightings):
    rows = [
        (
            s["id"],
            s["date"],
            s["location"],
            s["species"],
            s["latinName"]
        )
        for s in sightings
    ]

    with closing(sqlite3.connect(DB_PATH)) as conn:
        with conn:
            before = conn.total_changes

            conn.executemany("""
                INSERT OR IGNORE INTO sightings
                (id, date, location, species, latinName)
                VALUES (?, ?, ?, ?, ?)
            """, rows)

            inserted = conn.total_changes - before

    return inserted


def count_sightings():
    with closing(sqlite3.connect(DB_PATH)) as conn:
        result = conn.execute(
            "SELECT COUNT(*) FROM sightings"
        ).fetchone()

    return result[0]

if __name__ == "__main__":
    from service import fetch_sightings, clean_sightings

    init_db()

    sightings = fetch_sightings()
    cleaned, summary = clean_sightings(sightings)

    inserted = save_sightings(cleaned)

    print("Cleaning summary:", summary)
    print("New records inserted:", inserted)
    print("Total stored records:", count_sightings())