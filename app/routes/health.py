"""GET /health, GET /status."""

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

router = APIRouter()


@router.get("/health")
async def health() -> dict:
    """Liveness probe. Returns {"status": "ok"}. Always 200."""
    return {"status": "ok"}


@router.get("/status", response_model=None)
async def status(request: Request):
    """Bot status: running, strategy, last tick, errors, uptime. 503 if not running."""
    bot = getattr(request.app.state, "bot", None)
    if not bot:
        return JSONResponse(
            status_code=503,
            content={
                "is_running": False,
                "message": "Bot not initialized",
            },
        )
    payload = {
        "is_running": bot.is_running,
        "active_strategy": bot.strategy.name if hasattr(bot.strategy, "name") else None,
        "last_heartbeat": (
            bot.last_heartbeat.isoformat() if bot.last_heartbeat else None
        ),
        "last_error": bot.last_error,
        "uptime_seconds": bot.uptime_seconds,
    }
    if not bot.is_running:
        return JSONResponse(status_code=503, content=payload)
    return payload
