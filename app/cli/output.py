"""Dual-mode output: Rich for TTY, JSON for --json or non-TTY."""

import json
import sys
from typing import Any

def is_json_mode(json_flag: bool = False) -> bool:
    """Use JSON output if --json or stdout is not a TTY."""
    return json_flag or not sys.stdout.isatty()


def emit_json(data: Any) -> None:
    """Print JSON to stdout (for agents)."""
    print(json.dumps(data, default=str))


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
