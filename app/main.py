"""FastAPI app, lifespan, router includes."""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config import get_settings
from app.database import close_db, init_db
from app.core.exchange import HyperliquidClient
from app.core.bot import TradingBot
from app.strategies import get_strategy

from app.routes import health, trading


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: init DB, exchange, bot. Shutdown: stop bot, close DB."""
    await init_db()
    settings = get_settings()
    exchange = HyperliquidClient(
        wallet_address=settings.wallet_address,
        private_key=settings.private_key,
    )
    strategy = get_strategy(settings.strategy)
    strategy.configure({"symbol": settings.symbol})
    bot = TradingBot(exchange=exchange, strategy=strategy, settings=settings)
    app.state.bot = bot
    app.state.exchange = exchange

    if getattr(settings, "auto_start", False):
        await bot.start(interval=settings.loop_interval)

    yield

    await bot.stop()
    await close_db()


app = FastAPI(
    title="Hyperliquid Operator",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(health.router, tags=["health"])
app.include_router(trading.router, tags=["trading"])
