"""TradingBot — background loop, start/stop, status. Loop implementation in M6."""

import asyncio
from datetime import datetime
from typing import Any, Optional

from app.config import Settings
from app.core.exchange import HyperliquidClient
from app.strategies.base import BaseStrategy


class TradingBot:
    """Background trading loop; start/stop and status."""

    def __init__(
        self,
        exchange: HyperliquidClient,
        strategy: BaseStrategy,
        settings: Optional[Settings] = None,
    ) -> None:
        self.exchange = exchange
        self.strategy = strategy
        self.settings = settings or Settings()
        self._running = False
        self._task: Optional[asyncio.Task[None]] = None
        self._last_heartbeat: Optional[datetime] = None
        self._last_error: Optional[str] = None
        self._started_at: Optional[datetime] = None

    @property
    def is_running(self) -> bool:
        return self._running

    @property
    def last_heartbeat(self) -> Optional[datetime]:
        return self._last_heartbeat

    @property
    def last_error(self) -> Optional[str]:
        return self._last_error

    @property
    def uptime_seconds(self) -> Optional[float]:
        if self._started_at is None:
            return None
        return (datetime.utcnow() - self._started_at).total_seconds()

    async def start(self, interval: int = 60) -> None:
        """Start the background trading loop (stub: just sets running and heartbeat)."""
        if self._running:
            return
        self._running = True
        self._started_at = datetime.utcnow()
        self._last_heartbeat = datetime.utcnow()
        self._last_error = None
        # Real loop will be implemented in M6; for now just keep running
        self._task = asyncio.create_task(self._loop_stub(interval))

    async def _loop_stub(self, interval: int) -> None:
        """Placeholder loop until M6: just heartbeat."""
        while self._running:
            await asyncio.sleep(interval)
            if self._running:
                self._last_heartbeat = datetime.utcnow()

    async def stop(self) -> None:
        """Stop the trading loop gracefully."""
        self._running = False
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        self._task = None
