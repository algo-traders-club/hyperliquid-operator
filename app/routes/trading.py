"""POST /trade, GET /positions, GET /balance, GET /trades, POST /bot/start, POST /bot/stop."""

from typing import Optional

from fastapi import APIRouter, Request
from pydantic import BaseModel

from app.database import get_trades

router = APIRouter()


class TradeBody(BaseModel):
    """Manual trade request body."""

    symbol: str
    side: str  # 'buy' | 'sell'
    size: float


@router.get("/positions")
async def positions(request: Request) -> list:
    """Current open positions from exchange."""
    exchange = getattr(request.app.state, "exchange", None)
    if not exchange:
        return []
    return exchange.get_positions()


@router.get("/balance")
async def balance(request: Request) -> dict:
    """Account balance and equity (total, free, used)."""
    exchange = getattr(request.app.state, "exchange", None)
    if not exchange:
        return {"total": 0.0, "free": 0.0, "used": 0.0}
    return exchange.get_balance_breakdown()


@router.get("/trades")
async def trades(
    request: Request,
    limit: int = 100,
    symbol: Optional[str] = None,
    since: Optional[str] = None,
) -> list:
    """Trade history from DB."""
    return await get_trades(limit=limit, symbol=symbol, since=since)


@router.post("/trade")
async def trade(request: Request, body: TradeBody) -> dict:
    """Manual trade. Body: symbol, side, size. Same logic as CLI (shared execution)."""
    from app.core.execution import execute_manual_trade
    from app.config import get_settings
    settings = get_settings()
    if body.side not in ("buy", "sell"):
        return {"success": False, "error": "side must be 'buy' or 'sell'"}
    exchange = getattr(request.app.state, "exchange", None)
    result = execute_manual_trade(
        body.side,
        body.symbol,
        body.size,
        dry_run_override=settings.dry_run,
        exchange=exchange,
    )
    return {
        "success": result["approved"],
        "approved": result["approved"],
        "reason": result["reason"],
        "executed": result["executed"],
        "dry_run": result["dry_run"],
        "symbol": result["symbol"],
        "side": result["side"],
        "size": result["size"],
        "estimated_cost": result["estimated_cost"],
        "risk_check": result["risk_check"],
    }


@router.post("/bot/start")
async def bot_start(request: Request) -> dict:
    """Start trading loop."""
    bot = getattr(request.app.state, "bot", None)
    if not bot:
        return {"success": False, "error": "Bot not initialized"}
    if bot.is_running:
        return {"success": True, "message": "Bot already running"}
    await bot.start(interval=bot.settings.loop_interval)
    return {"success": True, "message": "Bot started"}


@router.post("/bot/stop")
async def bot_stop(request: Request) -> dict:
    """Stop trading loop."""
    bot = getattr(request.app.state, "bot", None)
    if not bot:
        return {"success": False, "error": "Bot not initialized"}
    if not bot.is_running:
        return {"success": True, "message": "Bot already stopped"}
    await bot.stop()
    return {"success": True, "message": "Bot stopped"}
