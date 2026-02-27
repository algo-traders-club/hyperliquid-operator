"""Tests for strategy registry and SimpleStrategy."""

import pytest

from app.strategies import get_strategy, list_strategies
from app.strategies.base import SignalType


def test_list_strategies_includes_simple_sma() -> None:
    names = list_strategies()
    assert "simple_sma" in names


def test_get_strategy_returns_instance() -> None:
    s = get_strategy("simple_sma")
    assert s.name == "simple_sma"
    assert s.description
    assert s.required_candles == 21


def test_simple_sma_hold_when_no_crossover() -> None:
    s = get_strategy("simple_sma")
    s.configure({"symbol": "BTC/USDC:USDC"})
    # Flat prices: no crossover
    candles = [{"close": 100.0} for _ in range(25)]
    signal = s.generate_signal(candles)
    assert signal.type == SignalType.HOLD
    assert signal.symbol == "BTC/USDC:USDC"


def test_simple_sma_buy_on_crossover_above() -> None:
    s = get_strategy("simple_sma")
    s.configure({"symbol": "BTC/USDC:USDC"})
    # 19 at 100, then 98, then 102: SMA(20)=100, prev_sma~99.9, prev=98<prev_sma, curr=102>sma -> BUY
    candles = [{"close": 100.0} for _ in range(19)] + [{"close": 98.0}, {"close": 102.0}]
    signal = s.generate_signal(candles)
    assert signal.type == SignalType.BUY
    assert signal.reason


def test_get_strategy_unknown_raises() -> None:
    with pytest.raises(ValueError, match="Unknown strategy"):
        get_strategy("nonexistent")
