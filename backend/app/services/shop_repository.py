import csv
import os
import sqlite3
from pathlib import Path
from threading import Lock
from typing import Dict, List


BASE_DIR = Path(__file__).resolve().parents[2]
DB_PATH = Path(os.getenv("SQLITE_DB_PATH", str(BASE_DIR / "data" / "chedian.db")))
SCHEMA_PATH = BASE_DIR / "data" / "schema.sql"
SEED_CSV_PATH = Path(os.getenv("SHOP_SEED_CSV_PATH", str(BASE_DIR / "data" / "shops_tju_beiyangyuan.csv")))
SEED_DATASET_ID = os.getenv("SHOP_SEED_DATASET_ID", SEED_CSV_PATH.stem)

_init_lock = Lock()
_initialized = False


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _ensure_schema(conn: sqlite3.Connection) -> None:
    schema_sql = SCHEMA_PATH.read_text(encoding="utf-8")
    conn.executescript(schema_sql)


def _ensure_meta_table(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS app_meta (
            key TEXT PRIMARY KEY,
            value TEXT
        )
        """
    )


def _get_meta(conn: sqlite3.Connection, key: str) -> str | None:
    row = conn.execute("SELECT value FROM app_meta WHERE key = ?", (key,)).fetchone()
    if not row:
        return None
    return str(row["value"])


def _set_meta(conn: sqlite3.Connection, key: str, value: str) -> None:
    conn.execute(
        """
        INSERT INTO app_meta (key, value) VALUES (?, ?)
        ON CONFLICT(key) DO UPDATE SET value = excluded.value
        """,
        (key, value),
    )


def _seed_from_csv(conn: sqlite3.Connection) -> None:
    with open(SEED_CSV_PATH, "r", encoding="utf-8-sig") as f:
        records = list(csv.DictReader(f))

    conn.execute("DELETE FROM shops")
    conn.executemany(
        """
        INSERT INTO shops (
            id, name, campus, area, avg_price, open_hours, tastes, scenes, tags, is_open
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            (
                item["id"],
                item["name"],
                item["campus"],
                item["area"],
                int(item["avg_price"]),
                item["open_hours"],
                item["tastes"],
                item["scenes"],
                item["tags"],
                int(item.get("is_open", 1)),
            )
            for item in records
        ],
    )
    _set_meta(conn, "seed_dataset", SEED_DATASET_ID)


def _seed_from_csv_if_needed(conn: sqlite3.Connection) -> None:
    _ensure_meta_table(conn)
    row = conn.execute("SELECT COUNT(1) AS cnt FROM shops").fetchone()
    current_seed_dataset = _get_meta(conn, "seed_dataset")
    if row and int(row["cnt"]) > 0 and current_seed_dataset == SEED_DATASET_ID:
        return
    _seed_from_csv(conn)


def ensure_database() -> None:
    global _initialized
    if _initialized:
        return

    with _init_lock:
        if _initialized:
            return
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        with _connect() as conn:
            _ensure_schema(conn)
            _seed_from_csv_if_needed(conn)
            conn.commit()
        _initialized = True


def fetch_active_shops() -> List[Dict]:
    ensure_database()
    with _connect() as conn:
        rows = conn.execute(
            """
            SELECT id, name, campus, area, avg_price, open_hours, tastes, scenes, tags, is_open
            FROM shops
            WHERE is_open = 1
            """
        ).fetchall()
    return [dict(row) for row in rows]


def count_shops() -> int:
    ensure_database()
    with _connect() as conn:
        row = conn.execute("SELECT COUNT(1) AS cnt FROM shops WHERE is_open = 1").fetchone()
    return int(row["cnt"]) if row else 0
