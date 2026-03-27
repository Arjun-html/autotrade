"""Backtester package.

Provides an event-driven backtesting engine that simulates strategy
performance on historical data fetched from the DataProvider. Results
include standard performance metrics (Sharpe, CAGR, max drawdown, etc.)
and are surfaced in the Streamlit dashboard.
"""

from .engine import BacktestEngine, BacktestResult

__all__ = ["BacktestEngine", "BacktestResult"]
