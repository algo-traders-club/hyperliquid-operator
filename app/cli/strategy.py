"""hl-op strategy — list, active, set, info."""

import asyncio

import typer

from app.cli.output import emit_json, is_json_mode
from app.database import get_bot_state, init_db, set_bot_state
from app.strategies import get_strategy, list_strategies

strategy_app = typer.Typer(help="Strategy management")


@strategy_app.command("list")
def list_cmd(
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    """List available strategies."""
    names = list_strategies()
    active = asyncio.run(_get_active_strategy())
    items = []
    for n in names:
        s = get_strategy(n)
        items.append({
            "name": n,
            "description": getattr(s, "description", n),
            "active": n == active,
        })
    if is_json_mode(json_output):
        emit_json(items)
    else:
        from rich.console import Console
        from rich.table import Table
        t = Table("Name", "Description", "Active")
        for i in items:
            t.add_row(i["name"], i["description"], "✓" if i["active"] else "")
        Console().print(t)


async def _get_active_strategy() -> str | None:
    await init_db()
    return await get_bot_state("active_strategy")


@strategy_app.command("active")
def active_cmd(
    quiet: bool = typer.Option(False, "--quiet", "-q", help="Bare value only"),
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    """Show currently active strategy."""
    name = asyncio.run(_get_active_strategy())
    if quiet:
        typer.echo(name or "")
        return
    if is_json_mode(json_output):
        emit_json({"active_strategy": name})
    else:
        typer.echo(f"Active strategy: {name or 'none'}")


@strategy_app.command("set")
def set_cmd(
    name: str = typer.Argument(..., help="Strategy name"),
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    """Set active strategy (hot-swap)."""
    names = list_strategies()
    if name not in names:
        typer.echo(f"Unknown strategy: {name}. Available: {names}", err=True)
        raise typer.Exit(2)
    async def _set():
        await init_db()
        prev = await get_bot_state("active_strategy")
        await set_bot_state("active_strategy", name)
        return prev
    prev = asyncio.run(_set())
    if is_json_mode(json_output):
        emit_json({"previous": prev, "active_strategy": name})
    else:
        typer.echo(f"Strategy changed: {prev or 'none'} → {name}")


@strategy_app.command("info")
def info_cmd(
    name: str = typer.Argument(..., help="Strategy name"),
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    """Strategy description and parameters."""
    names = list_strategies()
    if name not in names:
        typer.echo(f"Unknown strategy: {name}", err=True)
        raise typer.Exit(3)
    s = get_strategy(name)
    data = {
        "name": name,
        "description": getattr(s, "description", ""),
        "required_candles": getattr(s, "required_candles", 0),
    }
    if is_json_mode(json_output):
        emit_json(data)
    else:
        typer.echo(f"Name: {data['name']}")
        typer.echo(f"Description: {data['description']}")
        typer.echo(f"Required candles: {data['required_candles']}")
