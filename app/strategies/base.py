"""Base strategy ABC and Signal dataclass."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class SignalType(str, Enum):
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"


@dataclass
class Signal:
    """Trading signal produced by a strategy."""

    type: SignalType
    symbol: str
    strength: float  # 0.0 to 1.0
    reason: str
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = field(default_factory=dict)


class BaseStrategy(ABC):
    """All strategies must implement this interface. Set name, description, required_candles as class attributes."""

    name: str = ""
    description: str = ""
    required_candles: int = 0

    @abstractmethod
    def generate_signal(self, candles: List[Dict[str, Any]]) -> Signal:
        """
        Given OHLCV candle data, return a trading signal.

        Args:
            candles: List of dicts with keys: timestamp, open, high, low, close, volume
                     Ordered oldest-first. Length >= self.required_candles.

        Returns:
            Signal with type (BUY/SELL/HOLD), strength, reason, and optional SL/TP.
        """

    def configure(self, params: Dict[str, Any]) -> None:
        """Optional: accept runtime parameters (e.g. symbol) for tuning."""
        pass
