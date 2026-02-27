"""hl-op config — show, validate."""

import typer

from app.cli.output import emit_json, is_json_mode
from app.config import get_settings

config_app = typer.Typer(help="Configuration")


def _mask(s: str) -> str:
    if not s or len(s) < 8:
        return "***"
    return s[:4] + "..." + s[-4:]


@config_app.command("show")
def show_cmd(
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    """Current config (secrets masked)."""
    s = get_settings()
    data = {
        "wallet_address": _mask(s.wallet_address),
        "private_key": _mask(s.private_key),
        "symbol": s.symbol,
        "strategy": s.strategy,
        "loop_interval": s.loop_interval,
        "dry_run": s.dry_run,
        "risk_per_trade": s.risk_per_trade,
        "max_position_size_usd": s.max_position_size_usd,
        "max_open_positions": s.max_open_positions,
        "database_path": s.database_path,
    }
    if is_json_mode(json_output):
        emit_json(data)
    else:
        for k, v in data.items():
            typer.echo(f"{k}: {v}")


@config_app.command("validate")
def validate_cmd(
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    """Verify config and exchange connectivity."""
    from app.core.exchange import HyperliquidClient
    s = get_settings()
    errors = []
    if not s.wallet_address or not s.private_key:
        errors.append("WALLET_ADDRESS and PRIVATE_KEY must be set")
    if is_json_mode(json_output):
        if errors:
            emit_json({"valid": False, "errors": errors})
            raise typer.Exit(1)
        try:
            client = HyperliquidClient()
            bal = client.get_balance()
            emit_json({"valid": True, "balance": bal})
        except Exception as e:
            emit_json({"valid": False, "errors": [str(e)]})
            raise typer.Exit(1)
    else:
        if errors:
            for e in errors:
                typer.echo(e, err=True)
            raise typer.Exit(1)
        try:
            client = HyperliquidClient()
            bal = client.get_balance()
            typer.echo("Config valid. Balance:", bal)
        except Exception as e:
            typer.echo(f"Validation failed: {e}", err=True)
            raise typer.Exit(1)
