"""Thin CCXT wrapper for Hyperliquid — auth, retries, precision, symbol normalization."""

import time
from typing import Any, List, Optional

import ccxt

from app.config import get_settings


def normalize_symbol(symbol: str) -> str:
    """Normalize to Hyperliquid perp format: BASE/USDC:USDC."""
    s = symbol.strip().upper()
    if s.endswith(":USDC"):
        return s
    base = s.split("/")[0].split(":")[0]
    return f"{base}/USDC:USDC"


class HyperliquidClient:
    """Thin wrapper around CCXT's Hyperliquid implementation. Exceptions propagate."""

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
        """Fetch total USDC balance (convenience). Exceptions propagate."""
        b = self.get_balance_breakdown()
        return b.get("total", 0.0)

    def get_balance_breakdown(self) -> dict:
        """Fetch balance with total, free, used. Exceptions propagate."""
        balance = self.exchange.fetch_balance()
        total = float(balance.get("total", {}).get("USDC", 0) or 0)
        free = float(balance.get("free", {}).get("USDC", 0) or 0)
        used = float(balance.get("used", {}).get("USDC", 0) or 0)
        return {"total": total, "free": free, "used": used}

    def get_positions(self, symbol: Optional[str] = None) -> List[dict]:
        """Fetch open positions. CCXT returns side as 'long'/'short' string. Exceptions propagate."""
        positions = self.exchange.fetch_positions(symbols=[symbol] if symbol else None)
        out = []
        for p in positions:
            contracts = float(p.get("contracts", 0) or 0)
            if contracts == 0:
                continue
            sym = p.get("symbol") or ""
            side = p.get("side", "long")
            if isinstance(side, str):
                side = side.lower()
            else:
                side = "long" if side and float(side) > 0 else "short"
            out.append({
                "symbol": normalize_symbol(sym),
                "side": side,
                "size": abs(contracts),
                "entry_price": float(p.get("entryPrice") or 0),
                "unrealized_pnl": float(p.get("unrealizedPnl") or 0),
                "leverage": float(p.get("leverage") or 1),
            })
        return out

    def fetch_ohlcv(
        self,
        symbol: str,
        timeframe: str = "1m",
        limit: int = 100,
        since: Optional[int] = None,
    ) -> List[dict]:
        """
        Fetch OHLCV candles. Always pass since to avoid slow default (startTime=0).
        parse_timeframe returns seconds; convert to ms only for the final since.
        """
        sym = normalize_symbol(symbol)
        if since is None and limit > 0:
            tf_seconds = self.exchange.parse_timeframe(timeframe)
            since = int((time.time() - limit * tf_seconds) * 1000)
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

    def create_order(
        self,
        symbol: str,
        side: str,
        amount: float,
        order_type: str = "limit",
        price: Optional[float] = None,
        dry_run: bool = True,
    ) -> dict:
        """
        Place order. Uses price_to_precision for tick size. Exceptions propagate.
        """
        sym = normalize_symbol(symbol)
        if dry_run:
            return {"dry_run": True, "symbol": sym, "side": side, "amount": amount}
        if price is not None:
            price = float(self.exchange.price_to_precision(sym, price))
        return self.exchange.create_order(
            symbol=sym,
            type=order_type,
            side=side,
            amount=amount,
            price=price,
        )
