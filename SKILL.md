---
name: hyperliquid-operator
description: >
  Lean trading agent for Hyperliquid DEX. Use when asked to check positions,
  execute trades, view trading status, manage the trading bot, or analyze
  trading history on Hyperliquid.
version: "0.1.0"
license: MIT
metadata:
  author: algo-traders-club
  category: trading
  tags: [hyperliquid, trading, defi, perps, ccxt]
---

# Hyperliquid Operator

## When to use this skill
- User asks about trading positions on Hyperliquid
- User wants to execute a trade (buy/sell/close)
- User asks about trading bot status or P&L
- User wants to start/stop/configure the trading bot
- User asks about trading history or performance

## Available commands
All commands support `--json` for structured output.

### Check status
hl-op status --json
hl-op balance --json
hl-op positions --json

### Execute trades
hl-op trade buy <SYMBOL> <SIZE> --yes --json
hl-op trade sell <SYMBOL> <SIZE> --yes --json
hl-op trade close <SYMBOL> --yes --json
hl-op trade close-all --yes --json     # Emergency only

### Bot control
hl-op bot start
hl-op bot stop
hl-op strategy list --json
hl-op strategy set <name>

### History and analysis
hl-op history trades --json --limit 50
hl-op history pnl --json
hl-op history signals --json --limit 20

## Important notes
- Bot runs in DRY_RUN mode by default (paper trading)
- All trades pass through mandatory risk checks
- Use --dry-run to preview any trade before executing
- Default trading pair is BTC/USDC:USDC
