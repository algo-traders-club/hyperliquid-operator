"""Position manager — lifecycle tracking of open positions."""

from typing import Any, List

from app.models import Position


class PositionManager:
    """Tracks open positions; can be synced from exchange."""

    def __init__(self) -> None:
        self._positions: List[Position] = []

    def update_from_exchange(self, positions: List[dict]) -> None:
        """Replace internal state with positions from exchange."""
        self._positions = [
            Position(
                symbol=p.get("symbol", ""),
                side=p.get("side", "long"),
                size=float(p.get("size", 0)),
                entry_price=p.get("entry_price"),
                unrealized_pnl=p.get("unrealized_pnl"),
                leverage=p.get("leverage"),
            )
            for p in positions
        ]

    @property
    def positions(self) -> List[Position]:
        return self._positions

    def get_position(self, symbol: str) -> Any:
        """Return position for symbol or None."""
        for p in self._positions:
            if p.symbol == symbol:
                return p
        return None
