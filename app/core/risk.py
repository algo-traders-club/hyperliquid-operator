"""Mandatory trade approval gate — all trades must pass before execution."""

from typing import Any, List, Optional, Tuple

from app.config import Settings
from app.strategies.base import Signal


class RiskManager:
    """
    Mandatory trade approval gate.
    Returns (approved: bool, reason: str) for every trade.
    """

    def __init__(self, settings: Optional[Settings] = None) -> None:
        self.settings = settings or Settings()

    def approve_trade(
        self,
        signal: Signal,
        balance: float,
        positions: List[Any],
        equity_peak: Optional[float] = None,
        daily_pnl: Optional[float] = None,
        estimated_notional: Optional[float] = None,
    ) -> Tuple[bool, str]:
        """All checks must pass. Returns (True, 'approved') or (False, 'reason')."""
        if signal.type.value == "hold":
            return True, "approved"

        # Position sizing enforced by _check_position_size (max_position_size_usd).
        # risk_per_trade in PRD is "max equity risked" (e.g. stop-loss); not used for v0.1.
        checks = [
            self._check_position_size(signal, balance, estimated_notional),
            self._check_max_positions(positions),
            self._check_daily_loss_limit(balance, daily_pnl),
            self._check_max_drawdown(balance, equity_peak),
        ]

        for approved, reason in checks:
            if not approved:
                return False, reason

        return True, "approved"

    def _check_position_size(
        self,
        signal: Signal,
        balance: float,
        estimated_notional: Optional[float],
    ) -> Tuple[bool, str]:
        if estimated_notional is not None and estimated_notional > self.settings.max_position_size_usd:
            return False, (
                f"Position size ${estimated_notional:.2f} exceeds maximum "
                f"${self.settings.max_position_size_usd}"
            )
        return True, "approved"

    def _check_max_positions(self, positions: List[Any]) -> Tuple[bool, str]:
        if len(positions) >= self.settings.max_open_positions:
            return False, (
                f"Max open positions ({self.settings.max_open_positions}) reached"
            )
        return True, "approved"

    def _check_daily_loss_limit(
        self, balance: float, daily_pnl: Optional[float]
    ) -> Tuple[bool, str]:
        if daily_pnl is None:
            return True, "approved"
        if balance <= 0:
            return False, "Balance is zero or negative"
        # daily_pnl is typically negative when it's a loss
        loss_ratio = -daily_pnl / balance if daily_pnl < 0 else 0
        if loss_ratio >= self.settings.max_daily_loss:
            return False, (
                f"Daily loss limit ({self.settings.max_daily_loss:.0%}) reached"
            )
        return True, "approved"

    def _check_max_drawdown(
        self, balance: float, equity_peak: Optional[float]
    ) -> Tuple[bool, str]:
        if equity_peak is None or equity_peak <= 0:
            return True, "approved"
        drawdown = (equity_peak - balance) / equity_peak
        if drawdown >= self.settings.max_drawdown:
            return False, (
                f"Max drawdown ({self.settings.max_drawdown:.0%}) exceeded"
            )
        return True, "approved"

