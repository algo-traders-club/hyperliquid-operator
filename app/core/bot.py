"""TradingBot — background loop, start/stop, status."""

import asyncio
from datetime import datetime
from typing import Any, Optional

from app.config import Settings
from app.core.exchange import HyperliquidClient
from app.core.risk import RiskManager
from app.strategies.base import BaseStrategy, SignalType


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
        self._risk = RiskManager(self.settings)

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
        """Start the background trading loop."""
        if self._running:
            return
        self._running = True
        self._started_at = datetime.utcnow()
        self._last_heartbeat = datetime.utcnow()
        self._last_error = None
        self._task = asyncio.create_task(self._loop(interval))

    async def _tick(self) -> None:
        """One loop tick: fetch data, signal, risk check, optional execute, log."""
        from app.database import (
            get_bot_state,
            insert_signal,
            insert_trade,
            set_bot_state,
        )

        symbol = self.settings.symbol
        try:
            required = self.strategy.required_candles
            timeframe_ms = 60 * 1000
            since = int(datetime.utcnow().timestamp() * 1000) - (required + 10) * timeframe_ms
            candles = await asyncio.to_thread(
                self.exchange.fetch_ohlcv,
                symbol,
                "1m",
                required + 5,
                since,
            )
            if len(candles) < required:
                return

            signal = self.strategy.generate_signal(candles)
            balance = await asyncio.to_thread(self.exchange.get_balance)
            positions = await asyncio.to_thread(self.exchange.get_positions)
            equity_peak_str = await get_bot_state("peak_equity")
            daily_pnl_str = await get_bot_state("daily_pnl")
            equity_peak = float(equity_peak_str) if equity_peak_str else balance
            daily_pnl = float(daily_pnl_str) if daily_pnl_str else 0.0
            price = candles[-1]["close"] if candles else 0
            notional = min(
                balance * self.settings.risk_per_trade,
                self.settings.max_position_size_usd,
            )
            approved, risk_reason = self._risk.approve_trade(
                signal,
                balance,
                positions,
                equity_peak=equity_peak,
                daily_pnl=daily_pnl,
                estimated_notional=notional,
            )

            await insert_signal(
                symbol=signal.symbol,
                signal_type=signal.type.value,
                strength=signal.strength,
                reason=signal.reason,
                strategy=self.strategy.name,
                was_executed=(
                    approved
                    and signal.type != SignalType.HOLD
                    and not self.settings.dry_run
                ),
                risk_approved=approved,
                risk_reason=risk_reason if not approved else None,
            )

            if (
                signal.type != SignalType.HOLD
                and approved
                and not self.settings.dry_run
            ):
                size = notional / price if price else 0
                if size > 0:
                    await asyncio.to_thread(
                        self.exchange.create_order,
                        signal.symbol,
                        "buy" if signal.type == SignalType.BUY else "sell",
                        size,
                        price=price,
                        dry_run=False,
                    )
                    opened_at = datetime.utcnow().isoformat()
                    await insert_trade(
                        symbol=signal.symbol,
                        side="buy" if signal.type == SignalType.BUY else "sell",
                        size=size,
                        strategy=self.strategy.name,
                        opened_at=opened_at,
                        entry_price=price,
                        signal_strength=signal.strength,
                        is_dry_run=False,
                    )

            await set_bot_state("last_heartbeat", datetime.utcnow().isoformat())
            await set_bot_state("active_strategy", self.strategy.name)
            await set_bot_state("is_running", "true")
            await set_bot_state("equity", str(balance))
            peak = max(balance, equity_peak)
            await set_bot_state("peak_equity", str(peak))

        except Exception as e:
            self._last_error = str(e)
            await set_bot_state("last_error", str(e))

    async def _loop(self, interval: int) -> None:
        """Run tick, then sleep."""
        while self._running:
            try:
                await self._tick()
            except asyncio.CancelledError:
                break
            except Exception as e:
                self._last_error = str(e)
            self._last_heartbeat = datetime.utcnow()
            if self._running:
                await asyncio.sleep(interval)

    async def stop(self) -> None:
        """Stop the trading loop gracefully."""
        self._running = False
        from app.database import set_bot_state
        await set_bot_state("is_running", "false")
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        self._task = None
