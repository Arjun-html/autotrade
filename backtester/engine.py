"""Event-driven backtesting engine.

Design:
  - Iterates through historical bars in chronological order (bar-by-bar).
  - At each bar, calls the SignalGenerator to produce signals.
  - Passes signals through a simplified PortfolioManager for sizing/approval.
  - Simulates fills at the next bar's open price with configurable slippage
    and commission.
  - Tracks equity curve, trade log, and performance metrics.

TODO: Implement the full event loop in BacktestEngine.run().
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING

import pandas as pd

if TYPE_CHECKING:
    from data.base import DataProvider
    from signals.base import SignalGenerator


@dataclass
class Trade:
    """A single simulated executed trade.

    Attributes:
        symbol: Ticker.
        entry_time: Bar timestamp when position was opened.
        exit_time: Bar timestamp when position was closed.
        side: "long" or "short".
        qty: Number of shares.
        entry_price: Simulated fill price at entry.
        exit_price: Simulated fill price at exit.
        pnl: Realised profit/loss after commission.
        commission: Total commission paid.
    """

    symbol: str
    entry_time: datetime
    exit_time: datetime | None
    side: str
    qty: float
    entry_price: float
    exit_price: float | None = None
    pnl: float = 0.0
    commission: float = 0.0


@dataclass
class BacktestResult:
    """Output of a completed backtest run.

    Attributes:
        equity_curve: Series of portfolio value over time.
        trades: List of all simulated trades.
        metrics: Dict of performance metrics (Sharpe, CAGR, max drawdown, etc.).
        start: Backtest start date.
        end: Backtest end date.
        initial_capital: Starting capital in USD.
    """

    equity_curve: pd.Series
    trades: list[Trade] = field(default_factory=list)
    metrics: dict[str, float] = field(default_factory=dict)
    start: datetime | None = None
    end: datetime | None = None
    initial_capital: float = 100_000.0


class BacktestEngine:
    """Event-driven backtesting engine.

    Args:
        data_provider: Source of historical market data.
        initial_capital: Starting portfolio value in USD.
        commission_rate: Fractional commission per trade (e.g. 0.001 = 0.1%).
        slippage_bps: Slippage in basis points applied to fill prices.
    """

    def __init__(
        self,
        data_provider: "DataProvider",
        initial_capital: float = 100_000.0,
        commission_rate: float = 0.001,
        slippage_bps: float = 5.0,
    ) -> None:
        self.data_provider = data_provider
        self.initial_capital = initial_capital
        self.commission_rate = commission_rate
        self.slippage_bps = slippage_bps

    def run(
        self,
        signal_generator: "SignalGenerator",
        symbols: list[str],
        start: datetime,
        end: datetime,
        timeframe: str = "1Day",
    ) -> BacktestResult:
        """Run a backtest for *signal_generator* over the given period.

        Args:
            signal_generator: The strategy to test.
            symbols: Tickers to trade.
            start: Backtest start date (UTC).
            end: Backtest end date (UTC).
            timeframe: Bar timeframe string ("1Min", "1Hour", "1Day", etc.).

        Returns:
            BacktestResult with equity curve, trade log, and metrics.
        """
        raise NotImplementedError
