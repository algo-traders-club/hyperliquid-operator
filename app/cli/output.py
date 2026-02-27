"""Dual-mode output: Rich for TTY, JSON for --json or non-TTY."""

import json
import sys
from typing import Any

import typer


def is_json_mode(json_flag: bool = False) -> bool:
    """Use JSON output if --json or stdout is not a TTY."""
    return json_flag or not sys.stdout.isatty()


def emit_json(data: Any) -> None:
    """Print JSON to stdout (for agents)."""
    print(json.dumps(data, default=str))


def emit_error(
    error_code: str,
    message: str,
    input_data: dict | None = None,
    suggestion: str | None = None,
    exit_code: int = 1,
) -> None:
    """Structured error for agents (PRD 5.5). Prints to stdout in JSON, stderr message, then exits."""
    payload: dict = {"success": False, "error_code": error_code, "message": message}
    if input_data is not None:
        payload["input"] = input_data
    if suggestion is not None:
        payload["suggestion"] = suggestion
    typer.echo(f"Error: {message}", err=True)
    print(json.dumps(payload, default=str))
    raise typer.Exit(exit_code)


def emit_rich_table(headers: list[str], rows: list[tuple]) -> None:
    """Print Rich table to stdout (for humans)."""
    from rich.console import Console
    from rich.table import Table
    table = Table()
    for h in headers:
        table.add_column(h)
    for row in rows:
        table.add_row(*[str(x) for x in row])
    Console().print(table)
