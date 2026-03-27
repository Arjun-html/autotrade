"""Portfolio risk metrics.

Planned implementations:
- Value at Risk (VaR) — historical simulation and parametric
- Conditional VaR / Expected Shortfall
- Sharpe and Sortino ratios
- Maximum drawdown
- Beta and correlation to benchmark
- Volatility (rolling and annualised)
"""

from __future__ import annotations

import numpy as np
import pandas as pd


class RiskAnalyser:
    """Computes portfolio risk metrics from a returns series.

    TODO: Implement each metric below. Metrics are consumed by
    PortfolioManager.get_risk_metrics() and displayed in the dashboard.
    """

    def __init__(self, risk_free_rate: float = 0.05) -> None:
        self.risk_free_rate = risk_free_rate

    def sharpe_ratio(self, returns: pd.Series, periods_per_year: int = 252) -> float:
        """Annualised Sharpe ratio.

        Args:
            returns: Daily portfolio return series.
            periods_per_year: Trading days per year (252 for equities).

        Returns:
            Annualised Sharpe ratio.
        """
        raise NotImplementedError

    def var(self, returns: pd.Series, confidence: float = 0.95) -> float:
        """Historical Value at Risk (loss expressed as a positive number).

        Args:
            returns: Daily return series.
            confidence: Confidence level (e.g. 0.95 for 95% VaR).

        Returns:
            VaR as a positive fraction of portfolio value.
        """
        raise NotImplementedError

    def cvar(self, returns: pd.Series, confidence: float = 0.95) -> float:
        """Conditional VaR (Expected Shortfall).

        Args:
            returns: Daily return series.
            confidence: Confidence level.

        Returns:
            CVaR as a positive fraction of portfolio value.
        """
        raise NotImplementedError

    def max_drawdown(self, equity_curve: pd.Series) -> float:
        """Maximum peak-to-trough drawdown.

        Args:
            equity_curve: Cumulative portfolio value series.

        Returns:
            Max drawdown as a positive fraction (e.g. 0.15 = 15% drawdown).
        """
        raise NotImplementedError

    def beta(self, portfolio_returns: pd.Series, benchmark_returns: pd.Series) -> float:
        """Portfolio beta relative to a benchmark.

        Args:
            portfolio_returns: Daily portfolio returns.
            benchmark_returns: Daily benchmark returns (e.g. SPY).

        Returns:
            Beta coefficient.
        """
        raise NotImplementedError
