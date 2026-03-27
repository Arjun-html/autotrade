"""Market Data Collector package.

Provides a unified interface for fetching historical and live market data
from multiple providers (currently Alpaca). All consumers (signal generator,
portfolio manager, backtester) use the DataProvider abstraction defined here.
"""

from .base import DataProvider
from .models import Bar, Quote, AssetInfo, Timeframe

__all__ = ["DataProvider", "Bar", "Quote", "AssetInfo", "Timeframe"]
