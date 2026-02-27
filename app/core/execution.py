"""Shared trade execution — used by CLI and API for parity."""

from typing import Any

from app.config import get_settings
from app.core.exchange import HyperliquidClient, normalize_symbol
from app.core.risk import RiskManager
from app.strategies.base import Signal, SignalType


def execute_manual_trade(
    side: str,
    symbol: str,
    size: float,
    dry_run_override: bool | None = None,
    exchange: HyperliquidClient | None = None,
) -> dict[str, Any]:
    """
    Execute a manual trade (buy or sell). Shared by CLI and API.
    Pass exchange to reuse (e.g. app.state.exchange); otherwise creates a new client.
    Returns dict with: success, approved, reason, executed, dry_run, symbol, size, estimated_cost, etc.
    """
    settings = get_settings()
    dry_run = dry_run_override if dry_run_override is not None else settings.dry_run
    sym = normalize_symbol(symbol)
    if exchange is None:
        exchange = HyperliquidClient(
            wallet_address=settings.wallet_address,
            private_key=settings.private_key,
        )
    balance = exchange.get_balance()
    positions = exchange.get_positions()
    ohlcv = exchange.fetch_ohlcv(sym, limit=1)
    price = ohlcv[-1]["close"] if ohlcv else 0.0
    notional = size * price
    signal_type = SignalType.BUY if side == "buy" else SignalType.SELL
    signal = Signal(signal_type, sym, 0.5, "manual", None, None)
    rm = RiskManager(settings)
    approved, reason = rm.approve_trade(
        signal, balance, positions, estimated_notional=notional
    )

    executed = False
    if approved and not dry_run:
        exchange.create_order(sym, side, size, price=price, dry_run=False)
        executed = True

    return {
        "success": approved,
        "approved": approved,
        "reason": reason,
        "executed": executed,
        "dry_run": dry_run,
        "symbol": sym,
        "side": side,
        "size": size,
        "estimated_cost": round(notional, 2),
        "risk_check": "approved" if approved else reason,
    }
