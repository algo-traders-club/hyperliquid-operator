"""hl-op positions, hl-op balance."""

import typer

from app.cli.output import emit_json, is_json_mode
from app.config import get_settings
from app.core.exchange import HyperliquidClient


def _exchange() -> HyperliquidClient:
    s = get_settings()
    return HyperliquidClient(wallet_address=s.wallet_address, private_key=s.private_key)


def positions_cmd(
    json_output: bool = typer.Option(False, "--json"),
    quiet: bool = typer.Option(False, "--quiet", "-q"),
) -> None:
    """List open positions."""
    positions = _exchange().get_positions()
    if quiet:
        for p in positions:
            typer.echo(p.get("symbol", ""))
        return
    if is_json_mode(json_output):
        emit_json(positions)
    else:
        from rich.console import Console
        from rich.table import Table
        t = Table("Symbol", "Side", "Size", "Entry", "PnL")
        for p in positions:
            t.add_row(
                p.get("symbol", ""),
                p.get("side", ""),
                str(p.get("size")),
                str(p.get("entry_price")),
                str(p.get("unrealized_pnl")),
            )
        Console().print(t)


def balance_cmd(
    json_output: bool = typer.Option(False, "--json"),
    quiet: bool = typer.Option(False, "--quiet", "-q"),
) -> None:
    """Account balance (total, free, used)."""
    b = _exchange().get_balance_breakdown()
    if quiet:
        typer.echo(b.get("total", 0))
        return
    if is_json_mode(json_output):
        emit_json(b)
    else:
        typer.echo(f"Total: {b.get('total', 0)}")
        typer.echo(f"Free:  {b.get('free', 0)}")
        typer.echo(f"Used:  {b.get('used', 0)}")
