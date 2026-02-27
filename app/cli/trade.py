"""hl-op trade — buy, sell, close, close-all."""

import asyncio
from datetime import datetime, timezone

import typer

from app.cli.output import emit_error, emit_json, is_json_mode
from app.config import get_settings
from app.core.exchange import HyperliquidClient, normalize_symbol
from app.core.execution import execute_manual_trade
from app.database import init_db, insert_trade

trade_app = typer.Typer(help="Execute trades")


def _get_exchange() -> HyperliquidClient:
    s = get_settings()
    return HyperliquidClient(wallet_address=s.wallet_address, private_key=s.private_key)


def _trade_cmd(
    side: str,
    symbol: str,
    size: float,
    dry_run: bool,
    yes: bool,
    json_output: bool,
    quiet: bool,
    confirm_prompt: str,
    action_label: str,
) -> None:
    """Shared flow for buy/sell: always preview first, then confirm and execute if live."""
    s = get_settings()
    is_dry = dry_run or s.dry_run
    result = execute_manual_trade(side, symbol, size, dry_run_override=True)

    if is_json_mode(json_output):
        if not result["approved"]:
            emit_error(
                "RISK_CHECK_FAILED",
                result["reason"],
                input_data={"symbol": result["symbol"], "size": size},
                suggestion="reduce size or adjust risk config",
            )
        emit_json({
            "action": side,
            "symbol": result["symbol"],
            "size": result["size"],
            "estimated_cost": result.get("estimated_cost"),
            "risk_check": result["risk_check"],
            "would_execute": result["executed"] if not is_dry else False,
            "dry_run": is_dry,
        })
        return

    if not result["approved"]:
        typer.echo(f"Risk check failed: {result['reason']}", err=True)
        raise typer.Exit(1)

    if is_dry:
        typer.echo("⚠️  DRY RUN MODE — no real order submitted")
        price = result["estimated_cost"] / result["size"] if result["size"] else 0
        typer.echo(f"Would {action_label} {result['size']} {result['symbol']} @ ~{price:.2f}")
        return

    typer.echo(f"{action_label.capitalize()} {result['size']} {result['symbol']} @ ~{result['estimated_cost'] / result['size']:.2f}")
    if not yes:
        typer.confirm(confirm_prompt, abort=True)
    result = execute_manual_trade(side, symbol, size, dry_run_override=False)
    typer.echo("Order submitted.")


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
    _trade_cmd(
        "buy", symbol, size, dry_run, yes, json_output, quiet,
        confirm_prompt="Execute buy?",
        action_label="buy",
    )


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
    _trade_cmd(
        "sell", symbol, size, dry_run, yes, json_output, quiet,
        confirm_prompt="Execute sell?",
        action_label="sell",
    )


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


def _log_emergency_closes(positions: list) -> None:
    async def _run() -> None:
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
    asyncio.run(_run())


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

    positions_closed = [
        {"symbol": p.get("symbol", ""), "side": "sell" if p.get("side") == "long" else "buy", "size": p.get("size", 0)}
        for p in positions
    ]

    if is_json_mode(json_output):
        closed = 0
        if not s.dry_run and positions:
            for p in positions:
                sym = p.get("symbol", "")
                side = "sell" if p.get("side") == "long" else "buy"
                size = p.get("size", 0)
                exchange.create_order(sym, side, size, dry_run=False)
                closed += 1
            _log_emergency_closes(positions)
        emit_json({
            "action": "close-all",
            "count": len(positions),
            "closed": closed,
            "positions_closed": positions_closed,
            "dry_run": s.dry_run,
        })
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
        _log_emergency_closes(positions)
    typer.echo("All positions closed.")
