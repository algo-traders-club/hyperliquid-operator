"""CLI layer — Typer app and main() entry point."""

import typer

from app import __version__

from app.cli import config_cmd, history, strategy, trade
from app.cli.bot_cmd import bot_app
from app.cli.health import health_cmd
from app.cli.positions_balance import balance_cmd, positions_cmd
from app.cli.serve import serve_cmd
from app.cli.status import status_cmd

app = typer.Typer(
    name="hl-op",
    help="Hyperliquid Operator — lean trading agent for Hyperliquid DEX",
    no_args_is_help=True,
)

# Top-level commands
def version_cmd() -> None:
    typer.echo(f"hyperliquid-operator {__version__}")


app.command("version")(version_cmd)
app.command("health")(health_cmd)
app.command("status")(status_cmd)
app.command("positions")(positions_cmd)
app.command("balance")(balance_cmd)
app.command("serve")(serve_cmd)

# Groups
app.add_typer(trade.trade_app, name="trade")
app.add_typer(strategy.strategy_app, name="strategy")
app.add_typer(bot_app, name="bot")
app.add_typer(history.history_app, name="history")
app.add_typer(config_cmd.config_app, name="config")


def main() -> None:
    """Entry point for hl-op script."""
    app()


if __name__ == "__main__":
    main()
