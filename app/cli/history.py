"""hl-op history — trades, signals, pnl."""

import asyncio

import typer

from app.cli.output import emit_json, is_json_mode
from app.database import get_signals, get_trades, init_db

history_app = typer.Typer(help="Trade history")


async def _ensure_db():
    await init_db()


@history_app.command("trades")
def trades_cmd(
    limit: int = typer.Option(100, "--limit", "-n"),
    symbol: str | None = typer.Option(None, "--symbol"),
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    """Past trades with P&L."""
    async def _run():
        await _ensure_db()
        return await get_trades(limit=limit, symbol=symbol)
    rows = asyncio.run(_run())
    if is_json_mode(json_output):
        emit_json(rows)
    else:
        from rich.console import Console
        from rich.table import Table
        t = Table("id", "symbol", "side", "size", "entry_price", "pnl", "created_at")
        for r in rows:
            t.add_row(
                str(r.get("id")),
                r.get("symbol", ""),
                r.get("side", ""),
                str(r.get("size")),
                str(r.get("entry_price")),
                str(r.get("pnl")),
                r.get("created_at", ""),
            )
        Console().print(t)


@history_app.command("signals")
def signals_cmd(
    limit: int = typer.Option(100, "--limit", "-n"),
    symbol: str | None = typer.Option(None, "--symbol"),
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    """Signal log."""
    async def _run():
        await _ensure_db()
        return await get_signals(limit=limit, symbol=symbol)
    rows = asyncio.run(_run())
    if is_json_mode(json_output):
        emit_json(rows)
    else:
        from rich.console import Console
        from rich.table import Table
        t = Table("id", "symbol", "signal_type", "strength", "strategy", "created_at")
        for r in rows:
            t.add_row(
                str(r.get("id")),
                r.get("symbol", ""),
                r.get("signal_type", ""),
                str(r.get("strength")),
                r.get("strategy", ""),
                r.get("created_at", ""),
            )
        Console().print(t)


@history_app.command("pnl")
def pnl_cmd(
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    """Profit/loss summary."""
    async def _run():
        await _ensure_db()
        rows = await get_trades(limit=1000)
        total = sum((r.get("pnl") or 0) for r in rows)
        return {"total_pnl": total, "trades_count": len(rows)}
    data = asyncio.run(_run())
    if is_json_mode(json_output):
        emit_json(data)
    else:
        typer.echo(f"Total P&L: {data['total_pnl']:.2f}")
        typer.echo(f"Trades: {data['trades_count']}")
