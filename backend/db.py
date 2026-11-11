"""資料庫：沒設定 DATABASE_URL 用 SQLite，有設定就用 Postgres。

SQL 一律用 `?` 當參數佔位符，Postgres 模式會自動轉成 `%s`。
時間一律存 UTC 的 ISO 字串（例如 2026-11-11T03:00:00Z），兩種資料庫都能直接比大小。
"""
import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

from .config import ROOT

DATABASE_URL = os.getenv("DATABASE_URL") or os.getenv("POSTGRES_URL") or ""
IS_POSTGRES = DATABASE_URL.startswith(("postgres://", "postgresql://"))
IS_VERCEL = bool(os.getenv("VERCEL"))


def _sqlite_path() -> Path:
    if os.getenv("SQLITE_PATH"):
        return Path(os.environ["SQLITE_PATH"])
    # Vercel 只有 /tmp 可以寫，而且隨時會被清掉 → 正式上線請改用 Postgres
    return Path("/tmp/qa.db") if IS_VERCEL else ROOT / "data" / "qa.db"


SCHEMA_SQLITE = """
CREATE TABLE IF NOT EXISTS questions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_name TEXT NOT NULL,
    question TEXT NOT NULL,
    answer TEXT,
    error TEXT,
    model TEXT,
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_questions_created ON questions (created_at);
CREATE INDEX IF NOT EXISTS idx_questions_student ON questions (student_name, created_at);
"""

SCHEMA_POSTGRES = SCHEMA_SQLITE.replace("INTEGER PRIMARY KEY AUTOINCREMENT", "SERIAL PRIMARY KEY")

_initialized = False


@contextmanager
def connect():
    if IS_POSTGRES:
        import psycopg
        from psycopg.rows import dict_row

        conn = psycopg.connect(DATABASE_URL, row_factory=dict_row)
    else:
        path = _sqlite_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(path)
        conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def _sql(query: str) -> str:
    return query.replace("?", "%s") if IS_POSTGRES else query


def execute(query: str, params: tuple = ()) -> list[dict]:
    init_db()
    with connect() as conn:
        cur = conn.cursor()
        cur.execute(_sql(query), params)
        rows = cur.fetchall() if cur.description else []
        return [dict(r) for r in rows]


def init_db() -> None:
    global _initialized
    if _initialized:
        return
    with connect() as conn:
        cur = conn.cursor()
        schema = SCHEMA_POSTGRES if IS_POSTGRES else SCHEMA_SQLITE
        for stmt in filter(None, (s.strip() for s in schema.split(";"))):
            cur.execute(stmt)
    _initialized = True


def backend_info() -> dict:
    return {
        "database": "postgres" if IS_POSTGRES else "sqlite",
        # True 代表資料會不見（Vercel 上用 SQLite）
        "ephemeral": IS_VERCEL and not IS_POSTGRES,
    }


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def to_iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# ---------- 問答紀錄 ----------

def add_question(student_name: str, question: str, answer: str | None, error: str | None, model: str) -> None:
    execute(
        "INSERT INTO questions (student_name, question, answer, error, model, created_at) VALUES (?, ?, ?, ?, ?, ?)",
        (student_name, question, answer, error, model, now_iso()),
    )


def count_since(student_name: str, since_iso: str) -> int:
    rows = execute(
        "SELECT COUNT(*) AS n FROM questions WHERE student_name = ? AND created_at >= ? AND error IS NULL",
        (student_name, since_iso),
    )
    return int(rows[0]["n"])


def list_questions(limit: int = 200, student: str | None = None) -> list[dict]:
    if student:
        return execute(
            "SELECT * FROM questions WHERE student_name = ? ORDER BY id DESC LIMIT ?", (student, limit)
        )
    return execute("SELECT * FROM questions ORDER BY id DESC LIMIT ?", (limit,))


def stats(since_iso: str) -> dict:
    total = execute("SELECT COUNT(*) AS n FROM questions")[0]["n"]
    today = execute("SELECT COUNT(*) AS n FROM questions WHERE created_at >= ?", (since_iso,))[0]["n"]
    students = execute("SELECT COUNT(DISTINCT student_name) AS n FROM questions")[0]["n"]
    top = execute(
        "SELECT student_name, COUNT(*) AS n FROM questions GROUP BY student_name ORDER BY n DESC LIMIT 10"
    )
    return {"total": int(total), "today": int(today), "students": int(students), "topStudents": top}
