"""Tests for RiskManager."""

import pytest

from app.config import Settings
from app.core.risk import RiskManager
from app.strategies.base import Signal, SignalType


@pytest.fixture
def settings() -> Settings:
    return Settings(
        max_position_size_usd=500.0,
        max_open_positions=3,
        max_daily_loss=0.05,
        max_drawdown=0.15,
    )


@pytest.fixture
def risk(settings: Settings) -> RiskManager:
    return RiskManager(settings)


def test_hold_always_approved(risk: RiskManager) -> None:
    signal = Signal(SignalType.HOLD, "BTC/USDC:USDC", 0.0, "no crossover")
    approved, reason = risk.approve_trade(signal, 1000.0, [])
    assert approved is True
    assert reason == "approved"


def test_position_size_rejected(risk: RiskManager) -> None:
    signal = Signal(SignalType.BUY, "BTC/USDC:USDC", 0.5, "manual")
    approved, reason = risk.approve_trade(
        signal, 1000.0, [], estimated_notional=600.0
    )
    assert approved is False
    assert "500" in reason


def test_max_positions_rejected(risk: RiskManager) -> None:
    signal = Signal(SignalType.BUY, "BTC/USDC:USDC", 0.5, "manual")
    positions = [{"symbol": "A"}, {"symbol": "B"}, {"symbol": "C"}]
    approved, reason = risk.approve_trade(
        signal, 1000.0, positions, estimated_notional=100.0
    )
    assert approved is False
    assert "Max open positions" in reason or "3" in reason


def test_approved_when_under_limits(risk: RiskManager) -> None:
    signal = Signal(SignalType.BUY, "BTC/USDC:USDC", 0.5, "manual")
    approved, reason = risk.approve_trade(
        signal, 1000.0, [], estimated_notional=100.0
    )
    assert approved is True
    assert reason == "approved"
