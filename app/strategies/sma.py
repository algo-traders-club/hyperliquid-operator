"""SimpleStrategy: SMA-20 crossover — reference implementation."""

from typing import Any, Dict, List

from app.strategies import register
from app.strategies.base import BaseStrategy, Signal, SignalType


@register
class SimpleStrategy(BaseStrategy):
    """SMA-20 crossover: buy above, sell below."""

    name = "simple_sma"
    description = "SMA-20 crossover: buy above, sell below"
    required_candles = 21  # 20 for SMA + 1 for previous comparison

    def __init__(self, period: int = 20) -> None:
        self.period = period
        self.symbol: str = ""

    def configure(self, params: Dict[str, Any]) -> None:
        super().configure(params)
        if "symbol" in params:
            self.symbol = params["symbol"]
        if "period" in params:
            self.period = int(params["period"])

    def generate_signal(self, candles: List[Dict[str, Any]]) -> Signal:
        closes = [c["close"] for c in candles]
        sma = sum(closes[-self.period :]) / self.period
        prev_sma = sum(closes[-(self.period + 1) : -1]) / self.period

        curr_price = closes[-1]
        prev_price = closes[-2]

        curr_above = curr_price > sma
        prev_above = prev_price > prev_sma

        if curr_above and not prev_above:
            spread = (curr_price - sma) / sma if sma else 0
            return Signal(
                type=SignalType.BUY,
                symbol=self.symbol,
                strength=min(abs(spread) * 10, 1.0),
                reason=f"Price crossed above SMA-{self.period}",
                stop_loss=sma * 0.98,
                take_profit=curr_price * 1.04,
            )
        elif not curr_above and prev_above:
            spread = (sma - curr_price) / sma if sma else 0
            return Signal(
                type=SignalType.SELL,
                symbol=self.symbol,
                strength=min(abs(spread) * 10, 1.0),
                reason=f"Price crossed below SMA-{self.period}",
                stop_loss=sma * 1.02,
                take_profit=curr_price * 0.96,
            )
        else:
            return Signal(
                type=SignalType.HOLD,
                symbol=self.symbol,
                strength=0.0,
                reason="No crossover detected",
            )
