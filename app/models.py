"""Pydantic schemas and shared data structures."""

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class Position(BaseModel):
    """Open position from exchange or internal state."""

    symbol: str
    side: str  # 'long' | 'short'
    size: float
    entry_price: Optional[float] = None
    unrealized_pnl: Optional[float] = None
    leverage: Optional[float] = None


class Trade(BaseModel):
    """Executed trade record."""

    symbol: str
    side: str
    size: float
    entry_price: Optional[float] = None
    exit_price: Optional[float] = None
    pnl: Optional[float] = None
    fees: Optional[float] = None
    strategy: str
    signal_strength: Optional[float] = None
    exit_reason: Optional[str] = None
    is_dry_run: bool = True
    opened_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None
    created_at: Optional[datetime] = None


class SignalRecord(BaseModel):
    """Signal as stored or returned."""

    symbol: str
    signal_type: str  # 'buy' | 'sell' | 'hold'
    strength: float
    reason: Optional[str] = None
    strategy: str
    was_executed: bool = False
    risk_approved: Optional[bool] = None
    risk_reason: Optional[str] = None
    created_at: Optional[datetime] = None


class BotStatus(BaseModel):
    """Bot status for /status and CLI."""

    is_running: bool = False
    active_strategy: Optional[str] = None
    last_heartbeat: Optional[datetime] = None
    last_error: Optional[str] = None
    uptime_seconds: Optional[float] = None
