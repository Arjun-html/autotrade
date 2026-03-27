"""Portfolio and Risk Manager package.

Responsibilities:
- Track and display current holdings (synced from Alpaca paper account)
- Optimise portfolio weights using MPT, Black-Litterman, and factor models
- Measure and monitor risk (VaR, CVaR, Sharpe ratio, max drawdown)
- Approve or reject trade ideas proposed by the Signal Generator
"""

from .base import PortfolioManager

__all__ = ["PortfolioManager"]
