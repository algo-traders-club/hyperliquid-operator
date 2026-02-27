"""CLI layer — Typer app and main() entry point."""

import typer

from app import __version__

app = typer.Typer(
    name="hl-op",
    help="Hyperliquid Operator — lean trading agent for Hyperliquid DEX",
    no_args_is_help=True,
)


@app.command()
def version() -> None:
    """Show version info."""
    typer.echo(f"hyperliquid-operator {__version__}")


@app.command()
def status() -> None:
    """Bot status (running, last tick, errors, uptime). Placeholder."""
    typer.echo("Bot status: not implemented yet")


def main() -> None:
    """Entry point for hl-op script."""
    app()


if __name__ == "__main__":
    main()
