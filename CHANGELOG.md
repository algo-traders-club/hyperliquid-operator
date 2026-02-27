# Changelog

All notable changes to this project are documented here.

## [0.1.1] - 2026-02-27

### Code review fixes

**Critical**

- **Exchange client**: Exceptions no longer swallowed; CCXT/network errors propagate. `fetch_ohlcv` `since` uses correct units (timeframe in seconds, then convert to ms). Positions `side` treated as string `"long"`/`"short"`. `normalize_symbol` always returns `BASE/USDC:USDC`. `create_order` returns dict and propagates errors.
- **Risk**: Removed `_check_risk_per_trade` from approval checks; position sizing enforced only by `max_position_size_usd`.
- **Close command**: JSON output reports `closed: true` only when an order was actually sent; `dry_run` included in response.
- **Config**: `get_settings()` cached with `@lru_cache`.

**Medium**

- **Shared execution**: New `app/core/execution.py` with `execute_manual_trade()` used by CLI and API. `POST /trade` now uses same logic as CLI.
- **Bot CLI**: API base URL built from `get_settings().host` and `.port` (127.0.0.1 when host is 0.0.0.0).
- **Close-all**: Each closed position logged to DB with `exit_reason="emergency"` when not dry-run.
- **Datetime**: Replaced deprecated `datetime.utcnow()` with `datetime.now(timezone.utc)` in bot.
- **Structured errors**: Added `emit_error()` in `output.py`; trade commands use it for risk failures in JSON mode.
- **Balance**: API and CLI expose `total`, `free`, `used` via `get_balance_breakdown()`.

**Polish**

- Removed dead root `main.py`. Added `--quiet` to status, history trades/signals/pnl. CLAUDE.md gotchas section (OHLCV `since`, precision, symbol format, nonce, min collateral). README UV install line. `.gitignore`: `.mypy_cache/`, `.ruff_cache/`.

---

## [0.1.0] - 2026-02-27

- Initial release: CLI, FastAPI server, strategy registry, risk manager, SQLite, Docker/Render/SKILL/CLAUDE.
