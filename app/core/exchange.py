"""Thin CCXT wrapper for Hyperliquid — auth, retries, precision, symbol normalization."""

import time
from pathlib import Path
from typing import Any, List, Optional

import ccxt

from app.config import get_settings


def normalize_symbol(symbol: str) -> str:
    """Ensure perp symbol has quote :USDC (e.g. BTC/USDC -> BTC/USDC:USDC)."""
    s = symbol.strip().upper()
    if not s.endswith(":USDC"):
        if "/" in s and "USDC" in s:
            s = f"{s}:USDC"
        else:
            s = f"{s}:USDC" if "/" not in s else s
    return s


class HyperliquidClient:
    """Thin wrapper around CCXT's Hyperliquid implementation."""

    def __init__(
        self,
        wallet_address: Optional[str] = None,
        private_key: Optional[str] = None,
    ) -> None:
        settings = get_settings()
        self.wallet_address = wallet_address or settings.wallet_address
        self.private_key = private_key or settings.private_key
        self.exchange = ccxt.hyperliquid(
            {
                "walletAddress": self.wallet_address,
                "privateKey": self.private_key,
                "enableRateLimit": True,
                "options": {"defaultType": "swap"},
            }
        )

    def get_balance(self) -> float:
        """Fetch USDC/equity balance. Returns 0.0 on error or if not available."""
        try:
            balance = self.exchange.fetch_balance()
            # Hyperliquid perps: typically look for USDC or total equity
            if "USDC" in balance.get("total", {}):
                return float(balance["total"]["USDC"] or 0)
            if "total" in balance and balance["total"]:
                first = next(iter(balance["total"].values()), None)
                return float(first or 0)
            return 0.0
        except Exception:
            return 0.0

    def get_positions(self, symbol: Optional[str] = None) -> List[dict]:
        """Fetch open positions. Symbol optional filter. Normalize symbols to :USDC."""
        try:
            positions = self.exchange.fetch_positions(symbols=[symbol] if symbol else None)
            out = []
            for p in positions:
                if p.get("contracts") and float(p.get("contracts", 0) or 0) != 0:
                    sym = p.get("symbol") or ""
                    out.append({
                        "symbol": normalize_symbol(sym),
                        "side": "long" if float(p.get("side", 0) or 0) > 0 else "short",
                        "size": abs(float(p.get("contracts", 0) or 0)),
                        "entry_price": float(p.get("entryPrice") or 0),
                        "unrealized_pnl": float(p.get("unrealizedPnl") or 0),
                        "leverage": float(p.get("leverage") or 1),
                    })
            return out
        except Exception:
            return []

    def fetch_ohlcv(
        self,
        symbol: str,
        timeframe: str = "1m",
        limit: int = 100,
        since: Optional[int] = None,
    ) -> List[dict]:
        """
        Fetch OHLCV candles. Always pass since to avoid slow default (startTime=0).
        """
        sym = normalize_symbol(symbol)
        # PRD: since = required_candles * timeframe_ms to avoid ~3s delay
        if since is None and limit > 0:
            tf_ms = self.exchange.parse_timeframe(timeframe) * 1000
            since = int((time.time() - limit * tf_ms) * 1000)
        try:
            raw = self.exchange.fetch_ohlcv(sym, timeframe=timeframe, limit=limit, since=since)
            return [
                {
                    "timestamp": o[0],
                    "open": o[1],
                    "high": o[2],
                    "low": o[3],
                    "close": o[4],
                    "volume": o[5] if len(o) > 5 else 0,
                }
                for o in raw
            ]
        except Exception:
            return []

    def create_order(
        self,
        symbol: str,
        side: str,
        amount: float,
        order_type: str = "limit",
        price: Optional[float] = None,
        dry_run: bool = True,
    ) -> Optional[dict]:
        """
        Place order. Uses price_to_precision for tick size. No native market orders;
        use limit with slippage if simulating market.
        """
        sym = normalize_symbol(symbol)
        if dry_run:
            return {"dry_run": True, "symbol": sym, "side": side, "amount": amount}
        try:
            if price is not None:
                price = float(self.exchange.price_to_precision(sym, price))
            return self.exchange.create_order(
                symbol=sym,
                type=order_type,
                side=side,
                amount=amount,
                price=price,
            )
        except Exception:
            return None
