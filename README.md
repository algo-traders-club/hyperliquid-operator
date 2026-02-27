# Hyperliquid Operator

Lean, modular Python trading agent for **Hyperliquid DEX** — by Algo Traders Club.

- **CLI-first**: Every feature via `hl-op` (agents and humans).
- **Modular strategies**: Plug-and-play; drop a file in `app/strategies/`.
- **Mandatory risk gate**: All trades pass the risk manager; dry-run by default.
- **SQLite**: Trades, signals, and bot state in one file.

## Quick start

**Install UV** (if needed): `curl -LsSf https://astral.sh/uv/install.sh | sh`

```bash
git clone https://github.com/algo-traders-club/hyperliquid-operator.git
cd hyperliquid-operator
cp .env.example .env   # Edit with WALLET_ADDRESS and PRIVATE_KEY
uv sync
uv run hl-op config validate --json
uv run hl-op balance --json
uv run hl-op trade buy BTC/USDC:USDC 0.001 --dry-run --json
uv run hl-op serve
```

Then from another terminal: `uv run hl-op bot start` (or `POST /bot/start`).

## Commands (summary)

| Command | Description |
|--------|-------------|
| `hl-op health` | Liveness (exit 0) |
| `hl-op status` | Bot status (strategy, heartbeat, uptime) |
| `hl-op positions` | Open positions |
| `hl-op balance` | Account balance/equity |
| `hl-op trade buy/sell <symbol> <size>` | Open position (risk-checked) |
| `hl-op trade close <symbol>` | Close position |
| `hl-op strategy list` | List strategies |
| `hl-op strategy set <name>` | Set active strategy |
| `hl-op bot start/stop` | Start/stop loop (server must be running) |
| `hl-op history trades/signals/pnl` | History from DB |
| `hl-op config show/validate` | Config and connectivity |
| `hl-op serve` | Start FastAPI server (default :8000) |

Use `--json` for machine-readable output; `--dry-run` on trades to preview.

## Config

See `.env.example`. Required: `WALLET_ADDRESS`, `PRIVATE_KEY`. Defaults: `DRY_RUN=true`, `STRATEGY=simple_sma`, `SYMBOL=BTC/USDC:USDC`.

## Deploy

- **Docker**: `docker compose up -d` (mount `./data` for persistence).
- **Render**: Use `render.yaml`; set secrets in dashboard; attach 1GB disk.

## License

MIT.
