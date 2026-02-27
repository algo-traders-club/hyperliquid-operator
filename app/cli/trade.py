"""hl-op trade — buy, sell, close, close-all."""

import asyncio

import typer

from app.cli.output import emit_error, emit_json, is_json_mode
from app.config import get_settings
from app.core.exchange import HyperliquidClient, normalize_symbol
from app.core.execution import execute_manual_trade
from app.database import init_db, insert_trade
from datetime import datetime, timezone

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
    quiet: bool = typer.Option(False, "--quiet", "-q", help="Bare output"),
) -> None:
    """Open long position."""
    s = get_settings()
    # First call: dry if (user asked dry-run or config dry_run) or we need to confirm
    dry_first = dry_run or s.dry_run or (not yes)
    result = execute_manual_trade("buy", symbol, size, dry_run_override=dry_first)
    if is_json_mode(json_output):
        if not result["approved"]:
            emit_error(
                "RISK_CHECK_FAILED",
                result["reason"],
                input_data={"symbol": result["symbol"], "size": size},
                suggestion="reduce size or adjust risk config",
            )
        emit_json({
            "action": "buy",
            "symbol": result["symbol"],
            "size": result["size"],
            "estimated_cost": result["estimated_cost"],
            "risk_check": result["risk_check"],
            "would_execute": result["executed"],
            "dry_run": result["dry_run"],
        })
        return
    if not result["approved"]:
        typer.echo(f"Risk check failed: {result['reason']}", err=True)
        raise typer.Exit(1)
    if result["dry_run"]:
        typer.echo("⚠️  DRY RUN MODE — no real order submitted")
        return
    if not yes:
        typer.confirm("Execute buy?", abort=True)
        result = execute_manual_trade("buy", symbol, size, dry_run_override=False)
    price = result["estimated_cost"] / result["size"] if result["size"] else 0
    typer.echo(f"Buy {result['size']} {result['symbol']} @ ~{price:.2f}")


@trade_app.command("sell")
def sell_cmd(
    symbol: str = typer.Argument(..., help="e.g. BTC/USDC:USDC"),
    size: float = typer.Argument(..., help="Size in base asset"),
    dry_run: bool = typer.Option(False, "--dry-run"),
    yes: bool = typer.Option(False, "--yes", "-y"),
    json_output: bool = typer.Option(False, "--json"),
    quiet: bool = typer.Option(False, "--quiet", "-q"),
) -> None:
    """Open short position."""
    s = get_settings()
    dry_first = dry_run or s.dry_run or (not yes)
    result = execute_manual_trade("sell", symbol, size, dry_run_override=dry_first)
    if is_json_mode(json_output):
        if not result["approved"]:
            emit_error(
                "RISK_CHECK_FAILED",
                result["reason"],
                input_data={"symbol": result["symbol"], "size": size},
                suggestion="reduce size or adjust risk config",
            )
        emit_json({
            "action": "sell",
            "symbol": result["symbol"],
            "size": result["size"],
            "risk_check": result["risk_check"],
            "would_execute": result["executed"],
            "dry_run": result["dry_run"],
        })
        return
    if not result["approved"]:
        typer.echo(f"Risk check failed: {result['reason']}", err=True)
        raise typer.Exit(1)
    if result["dry_run"]:
        typer.echo("⚠️  DRY RUN MODE — no real order submitted")
        return
    if not yes:
        typer.confirm("Execute sell?", abort=True)
        result = execute_manual_trade("sell", symbol, size, dry_run_override=False)
    typer.echo(f"Sell {result['size']} {result['symbol']}")


@trade_app.command("close")
def close_cmd(
    symbol: str = typer.Argument(..., help="Symbol to close"),
    yes: bool = typer.Option(False, "--yes", "-y"),
    json_output: bool = typer.Option(False, "--json"),
    quiet: bool = typer.Option(False, "--quiet", "-q"),
) -> None:
    """Close position for symbol (idempotent)."""
    sym = normalize_symbol(symbol)
    s = get_settings()
    exchange = _get_exchange()
    positions = [p for p in exchange.get_positions() if p.get("symbol") == sym]
    if not positions:
        if is_json_mode(json_output):
            emit_json({"action": "close", "symbol": sym, "closed": False, "message": "No position", "dry_run": s.dry_run})
        else:
            typer.echo(f"No open position for {sym}")
        return
    p = positions[0]
    side = "sell" if p.get("side") == "long" else "buy"
    size = p.get("size", 0)
    if is_json_mode(json_output):
        actually_closed = False
        if not s.dry_run:
            exchange.create_order(sym, side, size, dry_run=False)
            actually_closed = True
        emit_json({
            "action": "close",
            "symbol": sym,
            "closed": actually_closed,
            "dry_run": s.dry_run,
        })
        return
    if not yes:
        typer.confirm(f"Close position {sym}?", abort=True)
    if s.dry_run:
        typer.echo("DRY RUN — would close")
    else:
        exchange.create_order(sym, side, size, dry_run=False)
    typer.echo(f"Closed {sym}")


@trade_app.command("close-all")
def close_all_cmd(
    yes: bool = typer.Option(False, "--yes", "-y"),
    json_output: bool = typer.Option(False, "--json"),
    quiet: bool = typer.Option(False, "--quiet", "-q"),
) -> None:
    """Emergency: close all positions. Logs each close to DB with exit_reason=emergency."""
    s = get_settings()
    exchange = _get_exchange()
    positions = exchange.get_positions()
    if is_json_mode(json_output):
        emit_json({"action": "close-all", "count": len(positions), "dry_run": s.dry_run})
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
        if not s.dry_run:
            exchange.create_order(sym, side, size, dry_run=False)
        typer.echo(f"Closed {sym}")

    if not s.dry_run and positions:

        async def _log_closes() -> None:
            await init_db()
            now = datetime.now(timezone.utc).isoformat()
            for p in positions:
                sym = p.get("symbol", "")
                side = "sell" if p.get("side") == "long" else "buy"
                size_val = p.get("size", 0)
                entry_price = p.get("entry_price")
                await insert_trade(
                    symbol=sym,
                    side=side,
                    size=size_val,
                    strategy="manual",
                    opened_at=now,
                    closed_at=now,
                    entry_price=entry_price,
                    exit_reason="emergency",
                    is_dry_run=False,
                )

        asyncio.run(_log_closes())
    typer.echo("All positions closed.")
