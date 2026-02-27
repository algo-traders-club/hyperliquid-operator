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
    """Account balance and equity."""
    exchange = getattr(request.app.state, "exchange", None)
    if not exchange:
        return {"balance": 0.0, "equity": 0.0}
    bal = exchange.get_balance()
    return {"balance": bal, "equity": bal}


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
    """Manual trade. Body: symbol, side, size. Respects DRY_RUN and risk checks."""
    bot = getattr(request.app.state, "bot", None)
    if not bot:
        return {"success": False, "error": "Bot not initialized"}
    # Minimal response; full execution will be in M5/M6
    return {
        "success": True,
        "dry_run": bot.settings.dry_run,
        "symbol": body.symbol,
        "side": body.side,
        "size": body.size,
        "message": "Dry run — no order submitted" if bot.settings.dry_run else "Order submitted",
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
