"""Backtest performance metrics.

All metrics are computed from a BacktestResult and surfaced in the dashboard.

TODO: Implement each function below.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from .engine import BacktestResult


def compute_metrics(result: BacktestResult, risk_free_rate: float = 0.05) -> dict[str, float]:
    """Compute a standard set of performance metrics for a backtest result.

    Args:
        result: Completed BacktestResult.
        risk_free_rate: Annual risk-free rate used in Sharpe computation.

    Returns:
        Dict with keys: 'cagr', 'sharpe', 'sortino', 'max_drawdown',
        'win_rate', 'profit_factor', 'total_trades', 'total_return'.
    """
    raise NotImplementedError


def cagr(equity_curve: pd.Series) -> float:
    """Compound Annual Growth Rate.

    Args:
        equity_curve: Portfolio value indexed by datetime.

    Returns:
        CAGR as a fraction (e.g. 0.12 = 12% per year).
    """
    raise NotImplementedError


def sharpe(returns: pd.Series, risk_free_rate: float = 0.05, periods: int = 252) -> float:
    """Annualised Sharpe ratio.

    Args:
        returns: Daily return series.
        risk_free_rate: Annual risk-free rate.
        periods: Trading days per year.

    Returns:
        Sharpe ratio.
    """
    raise NotImplementedError


def max_drawdown(equity_curve: pd.Series) -> float:
    """Maximum peak-to-trough drawdown fraction.

    Args:
        equity_curve: Portfolio value indexed by datetime.

    Returns:
        Max drawdown as a positive fraction.
    """
    raise NotImplementedError
