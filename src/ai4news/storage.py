# src/ai4news/storage.py
import json
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path


class Database:
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.conn = sqlite3.connect(str(db_path))
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON")
        self._create_tables()

    def _create_tables(self):
        self.conn.executescript("""
            CREATE TABLE IF NOT EXISTS targets (
                id INTEGER PRIMARY KEY,
                url TEXT UNIQUE NOT NULL,
                type TEXT NOT NULL,
                name TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS posts (
                id INTEGER PRIMARY KEY,
                target_id INTEGER REFERENCES targets(id) ON DELETE CASCADE,
                linkedin_id TEXT UNIQUE,
                author TEXT,
                text TEXT,
                url TEXT,
                media_urls TEXT,
                posted_at TIMESTAMP,
                scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS newsletters (
                id INTEGER PRIMARY KEY,
                file_path TEXT NOT NULL,
                post_count INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        self.conn.commit()

    def upsert_target(self, url: str, target_type: str, name: str = "") -> int:
        cur = self.conn.execute("SELECT id FROM targets WHERE url = ?", (url,))
        row = cur.fetchone()
        if row:
            self.conn.execute(
                "UPDATE targets SET type = ?, name = ? WHERE id = ?",
                (target_type, name, row["id"]),
            )
            self.conn.commit()
            return row["id"]
        cur = self.conn.execute(
            "INSERT INTO targets (url, type, name) VALUES (?, ?, ?)",
            (url, target_type, name),
        )
        self.conn.commit()
        return cur.lastrowid

    def remove_target(self, url: str) -> bool:
        cur = self.conn.execute("SELECT id FROM targets WHERE url = ?", (url,))
        row = cur.fetchone()
        if not row:
            return False
        self.conn.execute("DELETE FROM posts WHERE target_id = ?", (row["id"],))
        self.conn.execute("DELETE FROM targets WHERE id = ?", (row["id"],))
        self.conn.commit()
        return True

    def list_targets(self) -> list[dict]:
        cur = self.conn.execute("SELECT id, url, type, name, created_at FROM targets")
        return [dict(row) for row in cur.fetchall()]

    def insert_post(
        self,
        target_id: int,
        linkedin_id: str,
        author: str,
        text: str,
        url: str,
        media_urls: list[str],
        posted_at: str,
    ) -> bool:
        try:
            self.conn.execute(
                """INSERT INTO posts
                   (target_id, linkedin_id, author, text, url, media_urls, posted_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (target_id, linkedin_id, author, text, url,
                 json.dumps(media_urls), posted_at),
            )
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False

    def get_new_posts(self, since_days: int = 7) -> list[dict]:
        cutoff = datetime.now() - timedelta(days=since_days)
        cur = self.conn.execute(
            """SELECT p.id, p.linkedin_id, p.author, p.text, p.url,
                      p.media_urls, p.posted_at, p.scraped_at,
                      t.name as target_name, t.type as target_type, t.url as target_url
               FROM posts p
               JOIN targets t ON p.target_id = t.id
               WHERE p.scraped_at > ?
               ORDER BY p.posted_at DESC""",
            (cutoff.isoformat(),),
        )
        results = []
        for row in cur.fetchall():
            d = dict(row)
            d["media_urls"] = json.loads(d["media_urls"])
            results.append(d)
        return results

    def record_newsletter(self, file_path: str, post_count: int) -> None:
        self.conn.execute(
            "INSERT INTO newsletters (file_path, post_count) VALUES (?, ?)",
            (file_path, post_count),
        )
        self.conn.commit()

    def close(self):
        self.conn.close()
