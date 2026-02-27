# Hyperliquid Operator — Product Requirements Document

> **Version**: 0.1.0 (Living Document)
> **Last Updated**: 2026-02-27
> **Author**: Algo Traders Club
> **Status**: Draft → In Development

---

## 1. Vision & Philosophy

### 1.1 One-Liner

Hyperliquid Operator is a lean, modular Python trading agent that does one thing flawlessly: **execute trades on Hyperliquid DEX**.

### 1.2 Design Principles

1. **Lean and Mean** — No heavy compute. The agent executes; NexWave thinks. Trading agents should be thin execution clients, not monolithic analytics platforms.
2. **Build for Agents, Not Just Humans** — Every feature is accessible via CLI first. If an AI agent can't use it from a terminal, it doesn't ship. CLI is the universal interface.
3. **Modular by Default** — Strategies are plug-and-play. Swap them by dropping a file. An OpenClaw operator with the right SKILL.md can spin up a Hyperliquid agent without reading a line of code.
4. **Educational First** — This is a learning tool for the ATC community. Every architectural decision prioritizes clarity and teachability over cleverness.
5. **Close the Loop** — Inspired by Peter Steinberger's agent methodology: the agent (or an AI orchestrating it) should be able to plan, execute, verify, and iterate without human intervention.

### 1.3 What This Is NOT

- **Not a data platform** — NexWave handles signals, analytics, and heavy compute (future x402 integration).
- **Not a backtesting engine** — Use dedicated tools for that. This agent trades live.
- **Not a multi-exchange aggregator** — Hyperliquid only. One DEX, done right.
- **Not a framework** — It's a working trading agent you can fork, learn from, and customize.

---

## 2. Architecture Overview

### 2.1 System Context

```
┌─────────────────────────────────────────────────────────────────┐
│                        USER / AI AGENT                          │
│                                                                 │
│   Terminal (CLI)          HTTP Client          OpenClaw          │
│        │                      │                    │            │
│   $ hl-op status         GET /status          SKILL.md          │
│   $ hl-op trade ...      POST /trade          triggers          │
│   $ hl-op positions      GET /positions       hl-op CLI         │
└────────┬──────────────────────┬────────────────────┘            │
         │                      │                                 │
         ▼                      ▼                                 │
┌─────────────────────────────────────────────┐                   │
│         HYPERLIQUID OPERATOR                │                   │
│                                             │                   │
│  ┌──────────┐  ┌──────────┐  ┌───────────┐ │                   │
│  │   CLI    │  │ FastAPI  │  │  Trading  │ │                   │
│  │ (Typer)  │  │  Server  │  │   Loop    │ │                   │
│  └────┬─────┘  └────┬─────┘  └─────┬─────┘ │                   │
│       │              │              │       │                   │
│       ▼              ▼              ▼       │                   │
│  ┌─────────────────────────────────────┐   │                   │
│  │          CORE ENGINE                │   │                   │
│  │                                     │   │                   │
│  │  Strategy (modular)                 │   │                   │
│  │  Risk Manager (mandatory gate)      │   │                   │
│  │  Exchange Client (CCXT wrapper)     │   │                   │
│  │  Position Manager                   │   │                   │
│  │  Trade Logger (SQLite)              │   │                   │
│  └─────────────────────────────────────┘   │                   │
│                    │                       │                   │
└────────────────────┼───────────────────────┘                   │
                     │                                           │
                     ▼                                           │
          ┌─────────────────────┐      ┌──────────────────┐      │
          │   Hyperliquid DEX   │      │   NexWave.so     │      │
          │   (via CCXT)        │      │   (future, REST) │ ◄────┘
          │   Mainnet           │      │   Signals + Data │
          └─────────────────────┘      └──────────────────┘
```

### 2.2 Core Components

| Component | Responsibility | Tech |
|-----------|---------------|------|
| **CLI** | Agent-friendly terminal interface. Primary interaction layer. | Typer 0.24+ |
| **API Server** | HTTP endpoints for remote monitoring and manual triggers. | FastAPI 0.115+ |
| **Trading Loop** | Background async loop: fetch data → run strategy → execute. | asyncio |
| **Strategy Engine** | Modular plug-and-play strategies via abstract base class. | Python ABC |
| **Risk Manager** | Mandatory, non-bypassable trade approval gate. | Pure Python |
| **Exchange Client** | Thin CCXT wrapper for Hyperliquid. Handles auth, retries, precision. | CCXT 4.0+ |
| **Trade Logger** | Persists all trades, signals, positions, and bot state. | SQLite + aiosqlite |
| **Config** | Typed, validated settings from `.env` files. | Pydantic Settings |

---

## 3. Technology Stack

### 3.1 Runtime

| Technology | Version | Rationale |
|-----------|---------|-----------|
| **Python** | 3.12+ | Latest stable. Pattern matching, performance improvements, better typing. |
| **UV** | 0.10+ | 10-100x faster than pip. Single binary replaces pip, venv, pyenv, poetry. Rust-based. |
| **FastAPI** | 0.115+ | Async-native, auto-generates OpenAPI docs, lifespan events for background loop. |
| **Typer** | 0.24+ | FastAPI's CLI sibling. Type-hint based, auto `--help`, shell completion. |
| **SQLite** | Built-in | Zero-config, single-file database. Perfect for educational use and Render deployment. |
| **CCXT** | 4.0+ | Unified crypto exchange API. Mature Hyperliquid integration. |

### 3.2 Required Dependencies

```toml
[project]
name = "hyperliquid-operator"
version = "0.1.0"
description = "Lean trading agent for Hyperliquid DEX — by Algo Traders Club"
requires-python = ">=3.12"
license = { text = "MIT" }

dependencies = [
    "fastapi[standard]>=0.115.0",
    "uvicorn[standard]>=0.34.0",
    "typer>=0.24.0",
    "pydantic-settings>=2.6.0",
    "ccxt>=4.4.0",
    "aiosqlite>=0.20.0",
    "coincurve>=20.0.0",    # 900x faster ECDSA signing for CCXT
    "orjson>=3.10.0",        # Fast JSON serialization for CCXT
    "rich>=13.9.0",          # Beautiful terminal output for humans
]

[dependency-groups]
dev = [
    "pytest>=8.3.0",
    "pytest-asyncio>=0.24.0",
    "ruff>=0.9.0",
    "mypy>=1.14.0",
    "pre-commit>=4.0.0",
]

[tool.uv]
package = false

[project.scripts]
hl-op = "app.cli:main"
```

### 3.3 Why These Choices

**coincurve is REQUIRED, not optional.** CCXT auto-detects it for Hyperliquid's ECDSA wallet signing. Without it, every API call takes ~45ms for signing alone. With it: <0.05ms. That's a 900x speedup. For a trading agent, this is non-negotiable.

**orjson is REQUIRED, not optional.** CCXT auto-detects it for JSON serialization. Faster parsing of market data responses directly impacts loop latency.

**Typer + Rich together** provide dual-mode output: beautiful Rich tables for humans in TTY mode, clean JSON for agents when `--json` is passed or stdin is not a TTY.

---

## 4. Project Structure

```
hyperliquid-operator/
│
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI app, lifespan, router includes
│   ├── config.py               # Pydantic BaseSettings, .env loading
│   ├── database.py             # aiosqlite init, helpers, schema
│   ├── models.py               # Pydantic schemas (Signal, Trade, Position)
│   │
│   ├── cli/                    # ═══ CLI LAYER (Typer) ═══
│   │   ├── __init__.py         # Typer app, main() entry point
│   │   ├── status.py           # hl-op status, hl-op health
│   │   ├── trade.py            # hl-op trade buy/sell, hl-op positions
│   │   ├── strategy.py         # hl-op strategy list/set/info
│   │   ├── history.py          # hl-op history trades/signals/pnl
│   │   └── config_cmd.py       # hl-op config show/validate
│   │
│   ├── routes/                 # ═══ API LAYER (FastAPI) ═══
│   │   ├── __init__.py
│   │   ├── health.py           # GET /health, GET /status
│   │   └── trading.py          # POST /trade, GET /positions, GET /trades
│   │
│   ├── core/                   # ═══ CORE ENGINE ═══
│   │   ├── __init__.py
│   │   ├── bot.py              # TradingBot: background loop, start/stop
│   │   ├── exchange.py         # HyperliquidClient: CCXT wrapper
│   │   ├── risk.py             # RiskManager: mandatory trade gate
│   │   └── position.py         # PositionManager: lifecycle tracking
│   │
│   └── strategies/             # ═══ STRATEGY PLUGINS ═══
│       ├── __init__.py         # Strategy registry, auto-discovery
│       ├── base.py             # BaseStrategy ABC + Signal dataclass
│       └── sma.py              # SimpleStrategy: SMA-20 crossover
│
├── data/                       # SQLite DB lives here (gitignored)
├── tests/
│   ├── test_cli.py
│   ├── test_strategy.py
│   ├── test_risk.py
│   └── test_exchange.py
│
├── SKILL.md                    # OpenClaw / Claude Code / Codex skill file
├── CLAUDE.md                   # AI pair programming context
├── pyproject.toml
├── uv.lock
├── Dockerfile
├── docker-compose.yml
├── render.yaml
├── .env.example
└── README.md
```

---

## 5. The CLI — Building for Agents

> *"CLIs are super exciting precisely because they are a 'legacy' technology, which means AI agents can natively and easily use them."* — Andrej Karpathy

> *"I ship code I don't read... verifying is the way to make things good."* — Peter Steinberger

### 5.1 Design Philosophy: Agents Are First-Class Users

The CLI (`hl-op`) is the **primary interface** — not an afterthought bolted onto the API. Every capability of the Hyperliquid Operator is accessible from the terminal. This means:

- **Claude Code** can install it and start trading in 3 commands.
- **OpenClaw** can trigger it via SKILL.md shell execution.
- **Codex** can compose it into larger pipelines.
- **A human** gets beautiful Rich output with the same commands.

### 5.2 Agent-Friendly CLI Contract

Every command follows these 8 rules, derived from real-world agent workflow failures:

| # | Rule | Implementation |
|---|------|---------------|
| 1 | **Structured output is not optional** | Every command supports `--json`. JSON goes to stdout, human messages to stderr. |
| 2 | **Exit codes are the agent's control flow** | 0=success, 1=failure, 2=bad args, 3=not found, 4=permission denied, 5=conflict. |
| 3 | **Commands are idempotent where possible** | `hl-op trade close` on a closed position returns 0 (no-op), not an error. |
| 4 | **Self-documenting beats external docs** | `--help` on every command shows args, flags, types, defaults, and examples. |
| 5 | **Composable by design** | `--quiet` outputs bare values (one per line). Pipe-friendly. |
| 6 | **Dry-run and confirmation bypass** | `--dry-run` on destructive commands. `--yes` to skip prompts. |
| 7 | **Errors are actionable** | Structured error JSON with `error_code`, failing input echoed back, and `suggestion` field. |
| 8 | **Noun-verb grammar** | `hl-op trade buy`, `hl-op strategy list`, `hl-op history pnl`. Hierarchical, explorable. |

### 5.3 Command Reference

```
hl-op
├── status                      # Bot status (running, last tick, errors, uptime)
├── health                      # Liveness check (just "ok" + exit 0)
│
├── trade                       # ═══ TRADE COMMANDS ═══
│   ├── buy <symbol> <size>     # Open long position
│   ├── sell <symbol> <size>    # Open short position
│   ├── close <symbol>          # Close position
│   └── close-all               # Emergency: close everything
│
├── positions                   # List open positions
├── balance                     # Account balance and equity
│
├── strategy                    # ═══ STRATEGY COMMANDS ═══
│   ├── list                    # Available strategies
│   ├── active                  # Currently running strategy
│   ├── set <name>              # Hot-swap active strategy
│   └── info <name>             # Strategy description and parameters
│
├── bot                         # ═══ BOT CONTROL ═══
│   ├── start                   # Start the trading loop
│   ├── stop                    # Stop the trading loop (graceful)
│   └── restart                 # Stop + start
│
├── history                     # ═══ TRADE HISTORY ═══
│   ├── trades                  # Past trades with P&L
│   ├── signals                 # Signal log (all generated signals)
│   └── pnl                     # Profit/loss summary
│
├── config                      # ═══ CONFIGURATION ═══
│   ├── show                    # Current config (secrets masked)
│   └── validate                # Verify config + exchange connectivity
│
├── serve                       # Start FastAPI server (default: 0.0.0.0:8000)
│
└── version                     # Version info
```

### 5.4 Dual-Mode Output: Humans vs Agents

Every command auto-detects whether it's talking to a human (TTY) or an agent (pipe/redirect), and formats accordingly. The `--json` flag forces JSON regardless.

**Human (TTY detected):**
```bash
$ hl-op positions
┌──────────┬──────┬────────┬───────────┬──────────┐
│ Symbol   │ Side │ Size   │ Entry     │ PnL      │
├──────────┼──────┼────────┼───────────┼──────────┤
│ BTC/USDC │ LONG │ 0.001  │ 96,432.10 │ +$12.34  │
│ ETH/USDC │ SHORT│ 0.05   │ 3,521.00  │ -$3.21   │
└──────────┴──────┴────────┴───────────┴──────────┘
```

**Agent (piped or `--json`):**
```bash
$ hl-op positions --json
[
  {"symbol": "BTC/USDC:USDC", "side": "long", "size": 0.001, "entry_price": 96432.10, "unrealized_pnl": 12.34, "leverage": 3},
  {"symbol": "ETH/USDC:USDC", "side": "short", "size": 0.05, "entry_price": 3521.00, "unrealized_pnl": -3.21, "leverage": 5}
]
```

**Agent composability in action:**
```bash
# Get losing positions as bare symbols
$ hl-op positions --json | jq -r '.[] | select(.unrealized_pnl < 0) | .symbol'
ETH/USDC:USDC

# Close all losing positions (agent pipeline)
$ hl-op positions --json \
  | jq -r '.[] | select(.unrealized_pnl < 0) | .symbol' \
  | xargs -I {} hl-op trade close {} --yes --json

# Quick balance check in a script
$ hl-op balance --quiet
1523.47

# Dry-run a trade to preview
$ hl-op trade buy BTC/USDC:USDC 0.001 --dry-run --json
{"action": "buy", "symbol": "BTC/USDC:USDC", "size": 0.001, "estimated_cost": 96.43,
 "risk_check": "approved", "would_execute": true}
```

### 5.5 Structured Error Output

When things fail, agents need machine-parseable errors to decide: retry, fix, or abort.

```bash
$ hl-op trade buy BTC/USDC:USDC 100.0 --json
# exit code: 1
# stderr: Error: risk check failed — position size exceeds maximum
# stdout:
{
  "success": false,
  "error_code": "RISK_MAX_POSITION",
  "message": "Position size 100.0 exceeds maximum allowed 0.01 BTC",
  "input": {"symbol": "BTC/USDC:USDC", "size": 100.0},
  "suggestion": "reduce size or adjust max_position_size in config"
}
```

### 5.6 Implementation: Typer + FastAPI Shared Core

The CLI and API share the same core engine — they're just different interfaces to identical logic. No duplication.

```
CLI (Typer) ──┐
              ├──► Core Engine ──► Exchange (CCXT) ──► Hyperliquid
API (FastAPI)─┘        │
                       ▼
                    SQLite DB
```

The CLI commands call the same service functions as the API routes. The only difference is output formatting: Rich tables vs JSON responses.

---

## 6. Strategy System

### 6.1 BaseStrategy Abstract Class

All strategies implement this contract:

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional

class SignalType(str, Enum):
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"

@dataclass
class Signal:
    type: SignalType
    symbol: str
    strength: float          # 0.0 to 1.0
    reason: str              # Human-readable explanation
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    metadata: dict = None    # Strategy-specific data

class BaseStrategy(ABC):
    """All strategies must implement this interface."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique strategy identifier (e.g., 'sma_crossover')."""

    @property
    @abstractmethod
    def description(self) -> str:
        """One-line description for --help and strategy list."""

    @property
    @abstractmethod
    def required_candles(self) -> int:
        """Minimum OHLCV candles needed before generating signals."""

    @abstractmethod
    def generate_signal(self, candles: List[dict]) -> Signal:
        """
        Given OHLCV candle data, return a trading signal.

        Args:
            candles: List of dicts with keys: timestamp, open, high, low, close, volume
                     Ordered oldest-first. Length >= self.required_candles.

        Returns:
            Signal with type (BUY/SELL/HOLD), strength, reason, and optional SL/TP.
        """

    def configure(self, params: dict) -> None:
        """Optional: accept runtime parameters for tuning."""
        pass
```

### 6.2 SimpleStrategy: SMA-20 Crossover

The reference implementation. Intentionally straightforward for educational value.

**Logic:** Buy when price crosses above the 20-period SMA. Sell when it crosses below. Hold otherwise.

```python
class SimpleStrategy(BaseStrategy):
    name = "simple_sma"
    description = "SMA-20 crossover: buy above, sell below"
    required_candles = 21  # 20 for SMA + 1 for previous comparison

    def __init__(self, period: int = 20):
        self.period = period

    def generate_signal(self, candles: List[dict]) -> Signal:
        closes = [c["close"] for c in candles]
        sma = sum(closes[-self.period:]) / self.period
        prev_sma = sum(closes[-(self.period + 1):-1]) / self.period

        curr_price = closes[-1]
        prev_price = closes[-2]

        curr_above = curr_price > sma
        prev_above = prev_price > prev_sma

        if curr_above and not prev_above:
            spread = (curr_price - sma) / sma
            return Signal(
                type=SignalType.BUY, symbol=self.symbol,
                strength=min(abs(spread) * 10, 1.0),
                reason=f"Price crossed above SMA-{self.period}",
                stop_loss=sma * 0.98,
                take_profit=curr_price * 1.04,
            )
        elif not curr_above and prev_above:
            spread = (sma - curr_price) / sma
            return Signal(
                type=SignalType.SELL, symbol=self.symbol,
                strength=min(abs(spread) * 10, 1.0),
                reason=f"Price crossed below SMA-{self.period}",
                stop_loss=sma * 1.02,
                take_profit=curr_price * 0.96,
            )
        else:
            return Signal(
                type=SignalType.HOLD, symbol=self.symbol,
                strength=0.0, reason="No crossover detected",
            )
```

### 6.3 Strategy Registry & Auto-Discovery

Drop a `.py` file in `app/strategies/` and it's automatically available. No registration boilerplate.

```python
# app/strategies/__init__.py
import importlib
import pkgutil
from pathlib import Path
from app.strategies.base import BaseStrategy

_registry: dict[str, type[BaseStrategy]] = {}

def register(cls: type[BaseStrategy]) -> type[BaseStrategy]:
    _registry[cls.name] = cls
    return cls

def get_strategy(name: str) -> BaseStrategy:
    if name not in _registry:
        raise ValueError(f"Unknown strategy: {name}. Available: {list_strategies()}")
    return _registry[name]()

def list_strategies() -> list[str]:
    return list(_registry.keys())

# Auto-discover all strategy modules in this package
_pkg_path = Path(__file__).parent
for _importer, _modname, _ispkg in pkgutil.iter_modules([str(_pkg_path)]):
    if _modname not in ("base", "__init__"):
        importlib.import_module(f".{_modname}", __package__)
```

Each strategy file uses the `@register` decorator:
```python
from app.strategies import register
from app.strategies.base import BaseStrategy

@register
class SimpleStrategy(BaseStrategy):
    ...
```

### 6.4 Strategy Swapping

Strategies can be swapped at runtime via CLI or API — no restart required:

```bash
# List available strategies
$ hl-op strategy list --json
[{"name": "simple_sma", "description": "SMA-20 crossover: buy above, sell below", "active": true}]

# Swap to a different strategy
$ hl-op strategy set momentum_rsi
Strategy changed: simple_sma → momentum_rsi

# Check what's active
$ hl-op strategy active --quiet
momentum_rsi
```

---

## 7. Risk Management

### 7.1 The Mandatory Gate

**Every trade MUST pass through the RiskManager before reaching the exchange.** This is non-bypassable by design — not middleware that can be skipped, but a hard gate in the execution path.

```python
class RiskManager:
    """
    Mandatory trade approval gate.
    Returns (approved: bool, reason: str) for every trade.
    """

    def approve_trade(self, signal: Signal, balance: float, positions: list) -> tuple[bool, str]:
        """All checks must pass. Returns (True, "approved") or (False, "reason")."""

        checks = [
            self._check_position_size(signal, balance),
            self._check_max_positions(positions),
            self._check_daily_loss_limit(),
            self._check_max_drawdown(),
            self._check_risk_per_trade(signal, balance),
        ]

        for approved, reason in checks:
            if not approved:
                return False, reason

        return True, "approved"
```

### 7.2 Risk Parameters (Configurable via .env)

| Parameter | Default | Description |
|-----------|---------|-------------|
| `RISK_PER_TRADE` | 0.02 (2%) | Max equity risked per trade |
| `MAX_POSITION_SIZE_USD` | 500.0 | Max single position notional value |
| `MAX_OPEN_POSITIONS` | 3 | Max concurrent positions |
| `MAX_DAILY_LOSS` | 0.05 (5%) | Stop trading after losing 5% in a day |
| `MAX_DRAWDOWN` | 0.15 (15%) | Circuit breaker: halt if equity drops 15% from peak |
| `DRY_RUN` | true | Paper trade by default. Must explicitly set to false. |

### 7.3 Dry Run as Default

**The operator ships with `DRY_RUN=true`.** This is a critical safety feature for an educational tool. The bot does everything — generates signals, runs risk checks, logs trades — but never actually submits orders to Hyperliquid. Users must explicitly set `DRY_RUN=false` in their `.env` to trade with real money.

```bash
$ hl-op trade buy ETH/USDC:USDC 0.01
⚠️  DRY RUN MODE — no real order submitted
Signal: BUY ETH/USDC:USDC × 0.01
Risk check: ✅ approved
Would execute: limit buy 0.01 ETH @ ~$3,521.00

# To trade for real:
$ DRY_RUN=false hl-op trade buy ETH/USDC:USDC 0.01 --yes
```

---

## 8. Exchange Client (CCXT Wrapper)

### 8.1 Hyperliquid-Specific Configuration

```python
class HyperliquidClient:
    """Thin wrapper around CCXT's Hyperliquid implementation."""

    def __init__(self, wallet_address: str, private_key: str):
        self.exchange = ccxt.hyperliquid({
            "walletAddress": wallet_address,
            "privateKey": private_key,
            "enableRateLimit": True,
            "options": {"defaultType": "swap"},  # Perpetuals
        })
```

### 8.2 Critical Gotchas (Must Handle)

These are real issues discovered in CCXT's Hyperliquid integration:

| Gotcha | Impact | Mitigation |
|--------|--------|------------|
| **No native market orders** | CCXT simulates with 5% slippage limit orders | Use limit orders explicitly. If simulating market, set `slippage` param. |
| **fetch_ohlcv without `since`** | Defaults to `startTime=0`, takes ~3 seconds | ALWAYS pass `since` parameter. Calculate from `required_candles * timeframe_ms`. |
| **Price precision (5 sig figs)** | Orders rejected with "Price must be divisible by tick size" | Use `exchange.price_to_precision(symbol, price)` before every order. |
| **Nonce conflicts** | Multiple processes sharing one API wallet cause failures | One API wallet per bot instance. Document clearly. |
| **$10 minimum collateral** | Even small test trades need minimum balance | Validate balance before first trade. Clear error message. |
| **Symbol format** | Must use `BTC/USDC:USDC` for perps, not `BTC/USDC` | Normalize symbols in exchange client. Auto-append `:USDC` if missing. |

### 8.3 Rate Limits

Hyperliquid allows 1,200 weighted requests per minute per IP. CCXT's built-in rate limiter handles this, but the trading loop should respect it:

- **Info requests** (balances, positions, OHLCV): weight 2-60
- **Exchange actions** (orders): weight 1+
- **Recommended loop interval**: 60 seconds minimum for SMA-based strategies
- **Emergency close-all**: May burst; acceptable for safety operations

---

## 9. Database Schema

### 9.1 SQLite Configuration

```python
# Applied at connection time
PRAGMA journal_mode = WAL;     -- Write-ahead logging for concurrent reads
PRAGMA foreign_keys = ON;       -- Enforce referential integrity
PRAGMA busy_timeout = 5000;     -- 5s timeout for locked DB
```

### 9.2 Tables

**trades** — Every executed trade (entries and exits)
```sql
CREATE TABLE IF NOT EXISTS trades (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL,
    side TEXT NOT NULL,              -- 'buy' or 'sell'
    size REAL NOT NULL,
    entry_price REAL,
    exit_price REAL,
    pnl REAL,
    fees REAL,
    strategy TEXT NOT NULL,
    signal_strength REAL,
    exit_reason TEXT,               -- 'signal', 'stop_loss', 'take_profit', 'manual', 'emergency'
    is_dry_run BOOLEAN DEFAULT TRUE,
    opened_at TEXT NOT NULL,
    closed_at TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);
```

**signals** — Every signal generated (including HOLD)
```sql
CREATE TABLE IF NOT EXISTS signals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL,
    signal_type TEXT NOT NULL,       -- 'buy', 'sell', 'hold'
    strength REAL NOT NULL,
    reason TEXT,
    strategy TEXT NOT NULL,
    was_executed BOOLEAN DEFAULT FALSE,
    risk_approved BOOLEAN,
    risk_reason TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);
```

**bot_state** — Key-value store for crash recovery
```sql
CREATE TABLE IF NOT EXISTS bot_state (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at TEXT DEFAULT (datetime('now'))
);
-- Keys: equity, peak_equity, daily_pnl, daily_pnl_reset_date,
--        is_running, last_heartbeat, active_strategy
```

---

## 10. FastAPI Server

### 10.1 Lifespan Pattern

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    # STARTUP
    await init_db()
    exchange = HyperliquidClient(settings.wallet_address, settings.private_key)
    bot = TradingBot(exchange=exchange, strategy=get_strategy(settings.strategy))
    app.state.bot = bot

    if settings.auto_start:
        await bot.start(interval=settings.loop_interval)

    yield  # App is running

    # SHUTDOWN
    await bot.stop()
    await close_db()

app = FastAPI(title="Hyperliquid Operator", version="0.1.0", lifespan=lifespan)
```

### 10.2 Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Liveness probe. Returns `{"status": "ok"}`. Always 200. |
| GET | `/status` | Bot status: running, strategy, last tick, errors, uptime. 503 if not running. |
| GET | `/positions` | Current open positions from exchange. |
| GET | `/balance` | Account balance and equity. |
| GET | `/trades` | Trade history from DB. Supports `?limit=`, `?symbol=`, `?since=`. |
| POST | `/trade` | Manual trade. Body: `{"symbol": "...", "side": "buy", "size": 0.01}`. |
| POST | `/bot/start` | Start trading loop. |
| POST | `/bot/stop` | Stop trading loop. |

---

## 11. Configuration

### 11.1 Environment Variables

```bash
# .env.example

# ═══ EXCHANGE (required) ═══
WALLET_ADDRESS=0x...               # Hyperliquid master wallet (holds funds)
PRIVATE_KEY=0x...                  # API wallet private key (from app.hyperliquid.xyz/API)

# ═══ TRADING ═══
SYMBOL=BTC/USDC:USDC               # Default trading pair
STRATEGY=simple_sma                 # Active strategy name
LOOP_INTERVAL=60                    # Seconds between trading loop ticks
LEVERAGE=1                          # Default leverage (1 = no leverage)
DRY_RUN=true                        # Paper trade by default!

# ═══ RISK ═══
RISK_PER_TRADE=0.02                 # 2% equity per trade
MAX_POSITION_SIZE_USD=500           # Max position in USD
MAX_OPEN_POSITIONS=3
MAX_DAILY_LOSS=0.05                 # 5% daily loss limit
MAX_DRAWDOWN=0.15                   # 15% drawdown circuit breaker

# ═══ SERVER ═══
HOST=0.0.0.0
PORT=8000
LOG_LEVEL=INFO

# ═══ DATABASE ═══
DATABASE_PATH=data/trading.db
```

### 11.2 Pydantic Settings

```python
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # Exchange
    wallet_address: str
    private_key: str

    # Trading
    symbol: str = "BTC/USDC:USDC"
    strategy: str = "simple_sma"
    loop_interval: int = 60
    leverage: int = 1
    dry_run: bool = True  # Safe default

    # Risk
    risk_per_trade: float = 0.02
    max_position_size_usd: float = 500.0
    max_open_positions: int = 3
    max_daily_loss: float = 0.05
    max_drawdown: float = 0.15

    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    log_level: str = "INFO"

    # Database
    database_path: str = "data/trading.db"
```

---

## 12. Deployment

### 12.1 Local Development (UV)

```bash
# Clone and setup
git clone https://github.com/algo-traders-club/hyperliquid-operator.git
cd hyperliquid-operator
cp .env.example .env    # Edit with your keys

# Install and run
uv sync                 # Install all dependencies
uv run hl-op serve      # Start FastAPI server
# or
uv run hl-op status     # Check bot status via CLI
```

### 12.2 Docker (Advanced Users)

```dockerfile
FROM python:3.12-slim AS builder
COPY --from=ghcr.io/astral-sh/uv:0.10.7 /uv /uvx /bin/
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project --no-dev
COPY . .
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

FROM python:3.12-slim
RUN groupadd -g 10001 app && useradd -u 10000 -g app -m appuser \
    && mkdir -p /data && chown appuser:app /data
WORKDIR /app
COPY --from=builder --chown=appuser:app /app /app
ENV PATH="/app/.venv/bin:$PATH"
USER appuser
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s CMD ["hl-op", "health", "--quiet"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```yaml
# docker-compose.yml
services:
  operator:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - ./data:/data
    env_file:
      - .env
    restart: unless-stopped
```

### 12.3 Render.com

**Recommended plan:** Starter ($7/month) + 1GB persistent disk ($0.25/month) = **$7.25/month**.

The free tier will NOT work — it sleeps after 15 minutes of inactivity and has ephemeral storage. A trading bot must be always-on.

```yaml
# render.yaml
services:
  - type: web
    name: hyperliquid-operator
    runtime: docker
    plan: starter
    branch: main
    autoDeploy: true
    healthCheckPath: /health
    envVars:
      - key: WALLET_ADDRESS
        sync: false
      - key: PRIVATE_KEY
        sync: false
      - key: DRY_RUN
        value: "true"
      - key: DATABASE_PATH
        value: /data/trading.db
    disk:
      name: trading-data
      mountPath: /data
      sizeGB: 1
```

---

## 13. SKILL.md — OpenClaw & AI Agent Integration

```markdown
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
```

---

## 14. Future Integration Points

### 14.1 NexWave.so (Planned)

NexWave will serve as the data and signals platform. The operator will consume NexWave signals via REST API, replacing or augmenting the local strategy engine.

```
NexWave Signal API ──► Operator receives signal ──► Risk check ──► Execute on Hyperliquid
```

The `BaseStrategy` interface already supports this — a `NexWaveStrategy` would simply call the NexWave REST endpoint in `generate_signal()` instead of computing indicators locally. Future payment integration via x402 protocol.

### 14.2 OpenClaw Orchestration (Planned)

OpenClaw operators with the ATC SKILL.md can orchestrate multiple Hyperliquid Operators — managing a portfolio of strategies across different symbols or risk profiles, all through CLI commands that compose naturally in shell pipelines.

---

## 15. Success Metrics

### For the ATC Community

| Metric | Target |
|--------|--------|
| Time from `git clone` to first (dry-run) trade | < 5 minutes |
| Time for an AI agent to understand the codebase | < 2 minutes (via SKILL.md + CLAUDE.md) |
| Lines of code in core (excluding tests) | < 1,500 |
| Number of dependencies | < 15 |
| Docker image size | < 200 MB |
| Deployment cost (Render) | $7.25/month |

### For the Trading Agent

| Metric | Target |
|--------|--------|
| Loop tick latency (signal → order submitted) | < 2 seconds |
| Crash recovery time | < 30 seconds (auto-restart via Render/Docker) |
| Uptime | 99.5%+ |
| Risk check bypass rate | 0% (by design) |

---

## 16. Implementation Phases

### Phase 1: Foundation (Week 1-2)
- [ ] Project scaffolding with UV + pyproject.toml
- [ ] Core engine: exchange client, risk manager, base strategy
- [ ] SimpleStrategy (SMA-20) implementation
- [ ] SQLite schema and database layer
- [ ] Configuration system (.env + Pydantic)
- [ ] Basic FastAPI server with health/status endpoints

### Phase 2: CLI Layer (Week 2-3)
- [ ] Typer CLI with all command groups
- [ ] Dual-mode output (Rich tables + JSON)
- [ ] Agent-friendly error handling
- [ ] `--json`, `--quiet`, `--dry-run`, `--yes` flags on all commands
- [ ] Shell completion setup

### Phase 3: Trading Loop (Week 3-4)
- [ ] Background async trading loop with lifespan
- [ ] Position manager with order lifecycle
- [ ] Trade logging to SQLite
- [ ] Bot start/stop/restart via CLI and API
- [ ] Crash recovery from bot_state table

### Phase 4: Polish & Deploy (Week 4-5)
- [ ] Dockerfile + docker-compose.yml
- [ ] render.yaml for one-click Render deployment
- [ ] SKILL.md for OpenClaw integration
- [ ] CLAUDE.md for AI pair programming
- [ ] README.md with quickstart guide
- [ ] Tests for risk manager, strategies, and CLI

### Phase 5: Community & Content (Ongoing)
- [ ] Video 1: "Building a Trading Bot CLI That AI Agents Can Use"
- [ ] Video 2: "Writing Your First Strategy Plugin"
- [ ] Community strategy contributions via PR
- [ ] NexWave signal integration (when ready)

---

## Appendix A: Quick Start for AI Agents

If you're an AI agent (Claude Code, Codex, OpenClaw) reading this:

```bash
# 1. Install
git clone https://github.com/algo-traders-club/hyperliquid-operator.git
cd hyperliquid-operator && uv sync

# 2. Configure (set your keys)
cp .env.example .env
# Edit .env with wallet address and private key

# 3. Verify
uv run hl-op config validate --json

# 4. Check balance
uv run hl-op balance --json

# 5. Paper trade (DRY_RUN=true by default)
uv run hl-op trade buy BTC/USDC:USDC 0.001 --json

# 6. Start auto-trading loop
uv run hl-op bot start
uv run hl-op status --json
```

---

## Appendix B: Changelog

| Version | Date | Changes |
|---------|------|---------|
| 0.1.0 | 2026-02-27 | Initial PRD. Core architecture, CLI design, strategy system, risk management. |

---

*This is a living document. Update it as the project evolves.*
*Next step: Generate the implementation prompt from this PRD.*
