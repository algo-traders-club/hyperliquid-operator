"""hl-op trade — buy, sell, close, close-all."""

import typer

from app.cli.output import emit_json, is_json_mode
from app.config import get_settings
from app.core.exchange import HyperliquidClient, normalize_symbol
from app.core.risk import RiskManager
from app.strategies.base import SignalType

trade_app = typer.Typer(help="Execute trades")


def _get_exchange() -> HyperliquidClient:
    s = get_settings()
    return HyperliquidClient(wallet_address=s.wallet_address, private_key=s.private_key)


@trade_app.command("buy")
def buy_cmd(
    symbol: str = typer.Argument(..., help="e.g. BTC/USDC:USDC"),
    size: float = typer.Argument(..., help="Size in base asset"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Preview only"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation"),
    json_output: bool = typer.Option(False, "--json", help="JSON output"),
) -> None:
    """Open long position."""
    sym = normalize_symbol(symbol)
    s = get_settings()
    exchange = _get_exchange()
    balance = exchange.get_balance()
    positions = exchange.get_positions()
    # Estimate notional (size * current price)
    ohlcv = exchange.fetch_ohlcv(sym, limit=1)
    price = ohlcv[-1]["close"] if ohlcv else 0.0
    notional = size * price
    from app.strategies.base import Signal
    signal = Signal(SignalType.BUY, sym, 0.5, "manual", None, None)
    rm = RiskManager(s)
    approved, reason = rm.approve_trade(signal, balance, positions, estimated_notional=notional)
    if is_json_mode(json_output):
        emit_json({
            "action": "buy",
            "symbol": sym,
            "size": size,
            "estimated_cost": round(notional, 2),
            "risk_check": "approved" if approved else reason,
            "would_execute": approved and not s.dry_run and not dry_run,
            "dry_run": s.dry_run or dry_run,
        })
        return
    if s.dry_run or dry_run:
        typer.echo("⚠️  DRY RUN MODE — no real order submitted")
    if not approved:
        typer.echo(f"Risk check failed: {reason}", err=True)
        raise typer.Exit(1)
    if not (s.dry_run or dry_run) and not yes:
        typer.confirm("Execute buy?", abort=True)
    if not s.dry_run and not dry_run:
        exchange.create_order(sym, "buy", size, price=price, dry_run=False)
    typer.echo(f"Buy {size} {sym} @ ~{price:.2f}")


@trade_app.command("sell")
def sell_cmd(
    symbol: str = typer.Argument(..., help="e.g. BTC/USDC:USDC"),
    size: float = typer.Argument(..., help="Size in base asset"),
    dry_run: bool = typer.Option(False, "--dry-run"),
    yes: bool = typer.Option(False, "--yes", "-y"),
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    """Open short position."""
    sym = normalize_symbol(symbol)
    s = get_settings()
    exchange = _get_exchange()
    balance = exchange.get_balance()
    positions = exchange.get_positions()
    ohlcv = exchange.fetch_ohlcv(sym, limit=1)
    price = ohlcv[-1]["close"] if ohlcv else 0.0
    notional = size * price
    from app.strategies.base import Signal
    signal = Signal(SignalType.SELL, sym, 0.5, "manual", None, None)
    rm = RiskManager(s)
    approved, reason = rm.approve_trade(signal, balance, positions, estimated_notional=notional)
    if is_json_mode(json_output):
        emit_json({
            "action": "sell",
            "symbol": sym,
            "size": size,
            "risk_check": "approved" if approved else reason,
            "would_execute": approved and not s.dry_run and not dry_run,
            "dry_run": s.dry_run or dry_run,
        })
        return
    if s.dry_run or dry_run:
        typer.echo("⚠️  DRY RUN MODE — no real order submitted")
    if not approved:
        typer.echo(f"Risk check failed: {reason}", err=True)
        raise typer.Exit(1)
    if not (s.dry_run or dry_run) and not yes:
        typer.confirm("Execute sell?", abort=True)
    if not s.dry_run and not dry_run:
        exchange.create_order(sym, "sell", size, price=price, dry_run=False)
    typer.echo(f"Sell {size} {sym} @ ~{price:.2f}")


@trade_app.command("close")
def close_cmd(
    symbol: str = typer.Argument(..., help="Symbol to close"),
    yes: bool = typer.Option(False, "--yes", "-y"),
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    """Close position for symbol (idempotent)."""
    sym = normalize_symbol(symbol)
    exchange = _get_exchange()
    positions = [p for p in exchange.get_positions() if p.get("symbol") == sym]
    if is_json_mode(json_output):
        if not positions:
            emit_json({"action": "close", "symbol": sym, "closed": False, "message": "No position"})
        else:
            emit_json({"action": "close", "symbol": sym, "closed": True})
        return
    if not positions:
        typer.echo(f"No open position for {sym}")
        return
    if not yes:
        typer.confirm(f"Close position {sym}?", abort=True)
    # Close by placing opposite order (simplified)
    p = positions[0]
    side = "sell" if p.get("side") == "long" else "buy"
    size = p.get("size", 0)
    if get_settings().dry_run:
        typer.echo("DRY RUN — would close")
    else:
        exchange.create_order(sym, side, size, dry_run=False)
    typer.echo(f"Closed {sym}")


@trade_app.command("close-all")
def close_all_cmd(
    yes: bool = typer.Option(False, "--yes", "-y"),
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    """Emergency: close all positions."""
    exchange = _get_exchange()
    positions = exchange.get_positions()
    if is_json_mode(json_output):
        emit_json({"action": "close-all", "count": len(positions)})
        return
    if not positions:
        typer.echo("No open positions")
        return
    if not yes:
        typer.confirm(f"Close all {len(positions)} position(s)?", abort=True)
    for p in positions:
        sym = p.get("symbol", "")
        side = "sell" if p.get("side") == "long" else "buy"
        size = p.get("size", 0)
        if not get_settings().dry_run:
            exchange.create_order(sym, side, size, dry_run=False)
        typer.echo(f"Closed {sym}")
    typer.echo("All positions closed.")
