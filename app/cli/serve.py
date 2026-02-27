"""hl-op serve — start FastAPI server."""

import typer


def serve_cmd(
    host: str = typer.Option("0.0.0.0", "--host", "-h"),
    port: int = typer.Option(8000, "--port", "-p"),
) -> None:
    """Start FastAPI server (default: 0.0.0.0:8000)."""
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        reload=False,
    )
