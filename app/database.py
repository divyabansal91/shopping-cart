"""SQLite connection helpers."""
import os
import sqlite3
from contextlib import closing


def get_db_path() -> str:
    return os.getenv("DB_PATH", "shop.db")


def db() -> sqlite3.Connection:
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with closing(db()) as c:
        c.execute(
            """CREATE TABLE IF NOT EXISTS cart (
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   name TEXT NOT NULL,
                   price REAL NOT NULL,
                   qty INTEGER NOT NULL DEFAULT 1)"""
        )
        c.commit()
