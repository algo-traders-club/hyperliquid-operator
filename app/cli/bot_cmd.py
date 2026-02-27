"""hl-op bot — start, stop, restart. Uses API when server is running."""

import typer

from app.cli.output import emit_json, is_json_mode

bot_app = typer.Typer(help="Bot control")


def _api(method: str, path: str, body: dict | None = None) -> dict | None:
    import urllib.request
    import json as _json
    url = "http://127.0.0.1:8000" + path
    try:
        data = _json.dumps(body).encode() if body else None
        req = urllib.request.Request(url, data=data, method=method)
        if body:
            req.add_header("Content-Type", "application/json")
        with urllib.request.urlopen(req, timeout=5) as r:
            return _json.loads(r.read().decode())
    except Exception:
        return None


@bot_app.command("start")
def start_cmd(
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    """Start the trading loop (requires server: hl-op serve)."""
    r = _api("POST", "/bot/start")
    if is_json_mode(json_output):
        emit_json(r or {"success": False, "error": "Server not reachable"})
    else:
        if r and r.get("success"):
            typer.echo(r.get("message", "Bot started"))
        else:
            typer.echo("Start the server first: hl-op serve", err=True)
            raise typer.Exit(1)


@bot_app.command("stop")
def stop_cmd(
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    """Stop the trading loop (graceful)."""
    r = _api("POST", "/bot/stop")
    if is_json_mode(json_output):
        emit_json(r or {"success": False, "error": "Server not reachable"})
    else:
        if r and r.get("success"):
            typer.echo(r.get("message", "Bot stopped"))
        else:
            typer.echo("Server not reachable", err=True)


@bot_app.command("restart")
def restart_cmd(
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    """Stop then start the trading loop."""
    _api("POST", "/bot/stop")
    import time
    time.sleep(1)
    r = _api("POST", "/bot/start")
    if is_json_mode(json_output):
        emit_json(r or {"success": False})
    else:
        typer.echo("Restarted" if r and r.get("success") else "Restart failed")
