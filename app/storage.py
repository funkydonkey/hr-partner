import aiosqlite
import json
from datetime import datetime
from typing import Optional
from app.config import settings

DB_PATH = settings.database_path

DEFAULT_QUERIES = [
    {"query": "OneStream Lead Architect", "active": True},
    {"query": "OneStream Solution Architect", "active": True},
    {"query": "OneStream Developer Consultant", "active": True},
    {"query": "EPM CPM Architect OneStream", "active": True},
]


async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_id TEXT UNIQUE NOT NULL,
                title TEXT,
                company TEXT,
                location TEXT,
                description TEXT,
                url TEXT,
                source TEXT,
                score INTEGER,
                score_reason TEXT,
                found_at TEXT,
                query TEXT
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS search_queries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                query TEXT NOT NULL,
                active INTEGER NOT NULL DEFAULT 1
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS adapted_resumes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_id TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (job_id) REFERENCES jobs(job_id)
            )
        """)
        # Seed default queries if table is empty
        cursor = await db.execute("SELECT COUNT(*) FROM search_queries")
        row = await cursor.fetchone()
        if row[0] == 0:
            for q in DEFAULT_QUERIES:
                await db.execute(
                    "INSERT INTO search_queries (query, active) VALUES (?, ?)",
                    (q["query"], 1 if q["active"] else 0),
                )
        await db.commit()


async def get_seen_job_ids() -> set[str]:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT job_id FROM jobs")
        rows = await cursor.fetchall()
        return {row[0] for row in rows}


async def save_jobs(jobs: list[dict]):
    async with aiosqlite.connect(DB_PATH) as db:
        for job in jobs:
            await db.execute(
                """INSERT OR IGNORE INTO jobs
                   (job_id, title, company, location, description, url, source, score, score_reason, found_at, query)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    job["job_id"],
                    job.get("title", ""),
                    job.get("company", ""),
                    job.get("location", ""),
                    job.get("description", ""),
                    job.get("url", ""),
                    job.get("source", ""),
                    job.get("score", 0),
                    job.get("score_reason", ""),
                    datetime.utcnow().isoformat(),
                    job.get("query", ""),
                ),
            )
        await db.commit()


async def get_recent_jobs(limit: int = 50) -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM jobs ORDER BY found_at DESC LIMIT ?", (limit,)
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]


async def get_job_by_id(job_id: str) -> Optional[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM jobs WHERE job_id = ?", (job_id,))
        row = await cursor.fetchone()
        return dict(row) if row else None


# --- Search Queries CRUD ---

async def get_queries() -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM search_queries ORDER BY id")
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]


async def get_active_queries() -> list[str]:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT query FROM search_queries WHERE active = 1"
        )
        rows = await cursor.fetchall()
        return [row[0] for row in rows]


async def add_query(query: str) -> dict:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "INSERT INTO search_queries (query, active) VALUES (?, 1)", (query,)
        )
        await db.commit()
        return {"id": cursor.lastrowid, "query": query, "active": 1}


async def update_query(query_id: int, query: str, active: bool) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "UPDATE search_queries SET query = ?, active = ? WHERE id = ?",
            (query, 1 if active else 0, query_id),
        )
        await db.commit()
        return cursor.rowcount > 0


async def delete_query(query_id: int) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "DELETE FROM search_queries WHERE id = ?", (query_id,)
        )
        await db.commit()
        return cursor.rowcount > 0


# --- Adapted Resumes ---

async def save_adapted_resume(job_id: str, content: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR REPLACE INTO adapted_resumes (job_id, content, created_at) VALUES (?, ?, ?)",
            (job_id, content, datetime.utcnow().isoformat()),
        )
        await db.commit()


async def get_adapted_resume(job_id: str) -> Optional[str]:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT content FROM adapted_resumes WHERE job_id = ?", (job_id,)
        )
        row = await cursor.fetchone()
        return row[0] if row else None
