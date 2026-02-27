"""SQLite database — aiosqlite init, schema, helpers."""

from pathlib import Path
from typing import Any, List, Optional

import aiosqlite

from app.config import get_settings

# Module-level connection; set in init_db, used by helpers.
_conn: Optional[aiosqlite.Connection] = None


SCHEMA = """
PRAGMA journal_mode = WAL;
PRAGMA foreign_keys = ON;
PRAGMA busy_timeout = 5000;

CREATE TABLE IF NOT EXISTS trades (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL,
    side TEXT NOT NULL,
    size REAL NOT NULL,
    entry_price REAL,
    exit_price REAL,
    pnl REAL,
    fees REAL,
    strategy TEXT NOT NULL,
    signal_strength REAL,
    exit_reason TEXT,
    is_dry_run INTEGER DEFAULT 1,
    opened_at TEXT NOT NULL,
    closed_at TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS signals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL,
    signal_type TEXT NOT NULL,
    strength REAL NOT NULL,
    reason TEXT,
    strategy TEXT NOT NULL,
    was_executed INTEGER DEFAULT 0,
    risk_approved INTEGER,
    risk_reason TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS bot_state (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at TEXT DEFAULT (datetime('now'))
);
"""


async def init_db() -> None:
    """Create DB file, apply PRAGMAs and schema. Idempotent."""
    global _conn
    if _conn is not None:
        return
    settings = get_settings()
    path = Path(settings.database_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    _conn = await aiosqlite.connect(str(path))
    _conn.row_factory = aiosqlite.Row
    await _conn.execute("PRAGMA journal_mode = WAL")
    await _conn.execute("PRAGMA foreign_keys = ON")
    await _conn.execute("PRAGMA busy_timeout = 5000")
    for stmt in SCHEMA.strip().split(";"):
        stmt = stmt.strip()
        if stmt and "CREATE TABLE" in stmt:
            await _conn.execute(stmt)
    await _conn.commit()


async def close_db() -> None:
    """Close the database connection."""
    global _conn
    if _conn:
        await _conn.close()
        _conn = None


def _get_conn() -> aiosqlite.Connection:
    if _conn is None:
        raise RuntimeError("Database not initialized; call init_db() first")
    return _conn


async def insert_trade(
    symbol: str,
    side: str,
    size: float,
    strategy: str,
    opened_at: str,
    *,
    entry_price: Optional[float] = None,
    exit_price: Optional[float] = None,
    pnl: Optional[float] = None,
    fees: Optional[float] = None,
    signal_strength: Optional[float] = None,
    exit_reason: Optional[str] = None,
    is_dry_run: bool = True,
    closed_at: Optional[str] = None,
) -> int:
    """Insert a trade row. Returns last row id."""
    conn = _get_conn()
    await conn.execute(
        """INSERT INTO trades (
            symbol, side, size, entry_price, exit_price, pnl, fees,
            strategy, signal_strength, exit_reason, is_dry_run, opened_at, closed_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            symbol,
            side,
            size,
            entry_price,
            exit_price,
            pnl,
            fees,
            strategy,
            signal_strength,
            exit_reason,
            1 if is_dry_run else 0,
            opened_at,
            closed_at,
        ),
    )
    await conn.commit()
    cursor = await conn.execute("SELECT last_insert_rowid()")
    row = await cursor.fetchone()
    return row[0] if row else 0


async def insert_signal(
    symbol: str,
    signal_type: str,
    strength: float,
    strategy: str,
    *,
    reason: Optional[str] = None,
    was_executed: bool = False,
    risk_approved: Optional[bool] = None,
    risk_reason: Optional[str] = None,
) -> int:
    """Insert a signal row. Returns last row id."""
    conn = _get_conn()
    await conn.execute(
        """INSERT INTO signals (
            symbol, signal_type, strength, reason, strategy,
            was_executed, risk_approved, risk_reason
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            symbol,
            signal_type,
            strength,
            reason,
            strategy,
            1 if was_executed else 0,
            1 if risk_approved is True else (0 if risk_approved is False else None),
            risk_reason,
        ),
    )
    await conn.commit()
    cursor = await conn.execute("SELECT last_insert_rowid()")
    row = await cursor.fetchone()
    return row[0] if row else 0


async def get_trades(
    limit: int = 100,
    symbol: Optional[str] = None,
    since: Optional[str] = None,
) -> List[dict]:
    """Return trades, newest first."""
    conn = _get_conn()
    q = "SELECT * FROM trades WHERE 1=1"
    params: List[Any] = []
    if symbol:
        q += " AND symbol = ?"
        params.append(symbol)
    if since:
        q += " AND created_at >= ?"
        params.append(since)
    q += " ORDER BY id DESC LIMIT ?"
    params.append(limit)
    cursor = await conn.execute(q, params)
    rows = await cursor.fetchall()
    return [dict(r) for r in rows]


async def get_signals(
    limit: int = 100,
    symbol: Optional[str] = None,
) -> List[dict]:
    """Return signals, newest first."""
    conn = _get_conn()
    q = "SELECT * FROM signals WHERE 1=1"
    params: List[Any] = []
    if symbol:
        q += " AND symbol = ?"
        params.append(symbol)
    q += " ORDER BY id DESC LIMIT ?"
    params.append(limit)
    cursor = await conn.execute(q, params)
    rows = await cursor.fetchall()
    return [dict(r) for r in rows]


async def get_pnl_summary() -> dict:
    """Return total P&L and trade count via SUM/COUNT query."""
    conn = _get_conn()
    cursor = await conn.execute(
        "SELECT COALESCE(SUM(pnl), 0) AS total_pnl, COUNT(*) AS trades_count FROM trades"
    )
    row = await cursor.fetchone()
    if row is None:
        return {"total_pnl": 0.0, "trades_count": 0}
    return {"total_pnl": float(row[0]), "trades_count": int(row[1])}


async def get_bot_state(key: str) -> Optional[str]:
    """Get a bot_state value by key."""
    conn = _get_conn()
    cursor = await conn.execute(
        "SELECT value FROM bot_state WHERE key = ?",
        (key,),
    )
    row = await cursor.fetchone()
    return row[0] if row else None


async def set_bot_state(key: str, value: str) -> None:
    """Set a bot_state key-value (upsert)."""
    conn = _get_conn()
    await conn.execute(
        """INSERT INTO bot_state (key, value, updated_at)
           VALUES (?, ?, datetime('now'))
           ON CONFLICT(key) DO UPDATE SET value = ?, updated_at = datetime('now')""",
        (key, value, value),
    )
    await conn.commit()
