"""hl-op health — liveness check."""

import typer

from app.cli.output import emit_json, is_json_mode


def health_cmd(
    json_output: bool = typer.Option(False, "--json", help="Structured JSON output"),
    quiet: bool = typer.Option(False, "--quiet", "-q", help="Bare output for healthchecks"),
) -> None:
    """Liveness check: print ok and exit 0."""
    if quiet:
        typer.echo("ok")
        return
    if is_json_mode(json_output):
        emit_json({"status": "ok"})
    else:
        typer.echo("ok")
