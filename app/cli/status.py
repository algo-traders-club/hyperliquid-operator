"""hl-op status — bot status from DB or server."""

import asyncio
from typing import Optional

import typer

from app.cli.output import emit_json, is_json_mode
from app.database import get_bot_state, init_db


async def _load_status() -> dict:
    await init_db()
    last = await get_bot_state("last_heartbeat")
    strategy = await get_bot_state("active_strategy")
    running = await get_bot_state("is_running")
    return {
        "is_running": running == "true" if running else False,
        "active_strategy": strategy,
        "last_heartbeat": last,
        "last_error": await get_bot_state("last_error"),
        "uptime_seconds": None,
    }


def status_cmd(
    json_output: bool = typer.Option(False, "--json", help="Structured JSON output"),
    quiet: bool = typer.Option(False, "--quiet", "-q", help="Bare value only"),
) -> None:
    """Bot status (running, last tick, errors, uptime)."""
    data = asyncio.run(_load_status())
    if quiet:
        typer.echo("running" if data["is_running"] else "stopped")
        return
    if is_json_mode(json_output):
        emit_json(data)
    else:
        typer.echo(f"Running: {data['is_running']}")
        typer.echo(f"Strategy: {data['active_strategy'] or 'none'}")
        typer.echo(f"Last heartbeat: {data['last_heartbeat'] or 'never'}")
