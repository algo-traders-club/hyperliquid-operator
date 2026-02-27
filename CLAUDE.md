# Hyperliquid Operator — AI pair programming context

This project is a **lean trading agent for Hyperliquid DEX**. The single source of truth for behavior and design is **`docs/hyperliquid-operator-prd.md`**. Follow the PRD faithfully; do not go out of scope.

## Layout

- **`app/cli/`** — Typer CLI (`hl-op`). Commands: health, status, trade, positions, balance, strategy, bot, history, config, serve.
- **`app/core/`** — Engine: `exchange.py` (CCXT wrapper), `risk.py` (mandatory gate), `position.py`, `bot.py` (trading loop).
- **`app/strategies/`** — Plug-in strategies; `base.py` (ABC + Signal), `sma.py` (SimpleStrategy). Registry in `__init__.py`.
- **`app/routes/`** — FastAPI: health, status, positions, balance, trades, trade, bot/start, bot/stop.
- **`app/database.py`** — SQLite (trades, signals, bot_state); aiosqlite.
- **`app/config.py`** — Pydantic Settings from `.env`.

## Conventions

- CLI: support `--json` and `--quiet` where specified in the PRD; exit codes 0=success, 1=failure, 2=bad args, 3=not found.
- All trades go through `RiskManager.approve_trade`; never bypass.
- Default `DRY_RUN=true`; real orders only when explicitly disabled.
- Symbols: normalize to `BTC/USDC:USDC` (append `:USDC` if missing).

## Quick reference

- Run server: `uv run hl-op serve`
- Bot control: `hl-op bot start` / `hl-op bot stop` (server must be running) or `POST /bot/start`, `POST /bot/stop`.
- Add a strategy: new file in `app/strategies/` with `@register` and `BaseStrategy` implementation.
