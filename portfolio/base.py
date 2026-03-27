"""Abstract base classes for the Portfolio and Risk Manager module."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from signals.base import Signal


@dataclass
class Position:
    """A single holding in the portfolio.

    Attributes:
        symbol: Ticker symbol.
        qty: Number of shares held (negative = short).
        avg_entry_price: Average cost basis per share.
        current_price: Most recent market price.
        unrealised_pnl: Unrealised profit/loss in dollars.
        market_value: Current market value (qty * current_price).
    """

    symbol: str
    qty: float
    avg_entry_price: float
    current_price: float
    unrealised_pnl: float
    market_value: float


@dataclass
class TradeDecision:
    """The output of PortfolioManager.approve_trade().

    Attributes:
        approved: Whether the trade is approved.
        symbol: Ticker.
        suggested_qty: Recommended number of shares to trade (0 if rejected).
        reason: Human-readable explanation.
        risk_metrics: Dict of risk metrics that informed the decision.
    """

    approved: bool
    symbol: str
    suggested_qty: float = 0.0
    reason: str = ""
    risk_metrics: dict[str, Any] = field(default_factory=dict)


class PortfolioManager(ABC):
    """Abstract base class for the portfolio and risk manager.

    Concrete implementations will use different optimisation methods
    (e.g. mean-variance MPT, Black-Litterman, factor models) but must
    all expose this interface so the rest of the system remains decoupled.
    """

    @abstractmethod
    def get_positions(self) -> list[Position]:
        """Return a snapshot of all current open positions.

        Returns:
            List of Position objects (empty list if flat).
        """
        raise NotImplementedError

    @abstractmethod
    def get_portfolio_value(self) -> float:
        """Return the total portfolio market value in USD."""
        raise NotImplementedError

    @abstractmethod
    def approve_trade(self, signal: Signal) -> TradeDecision:
        """Evaluate a Signal and decide whether to execute it.

        The implementation should consider position sizing, concentration
        limits, VaR budgets, and correlation with existing holdings.

        Args:
            signal: A trade idea from the Signal Generator.

        Returns:
            TradeDecision with approval status and suggested quantity.
        """
        raise NotImplementedError

    @abstractmethod
    def optimise(self) -> dict[str, float]:
        """Compute target portfolio weights using the configured optimisation method.

        Returns:
            Mapping of symbol → target weight in [0, 1] summing to 1.
        """
        raise NotImplementedError

    @abstractmethod
    def get_risk_metrics(self) -> dict[str, float]:
        """Compute current portfolio risk metrics.

        Returns:
            Dict containing keys such as 'sharpe', 'var_95', 'cvar_95',
            'max_drawdown', 'beta', 'volatility'.
        """
        raise NotImplementedError
