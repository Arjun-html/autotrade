"""Abstract DataProvider interface.

Every component that needs market data — Signal Generator, Portfolio Manager,
and Backtester — depends only on this abstraction. Concrete implementations
(AlpacaDataProvider, etc.) live in data/providers/.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Callable

import pandas as pd

from .models import AssetClass, AssetInfo, Bar, Quote, Timeframe


class DataProvider(ABC):
    """Abstract base class for market data providers.

    Concrete subclasses must implement every abstract method.
    The DataCache in data.cache is an optional transparent layer on top of
    any DataProvider — it wraps a provider and serves cached data when fresh.

    All DataFrames returned by `get_bars` share a common schema:
        Index : DatetimeIndex (UTC)
        Columns: open, high, low, close, volume [, vwap, trade_count]
    """

    # -------------------------------------------------------------- Historical

    @abstractmethod
    def get_bars(
        self,
        symbol: str,
        start: datetime,
        end: datetime,
        timeframe: Timeframe = Timeframe.DAY_1,
        limit: int | None = None,
    ) -> pd.DataFrame:
        """Fetch OHLCV bars for a single symbol.

        Args:
            symbol: Ticker symbol (e.g. "AAPL").
            start: Start of the requested time range (UTC-aware).
            end: End of the requested time range (UTC-aware).
            timeframe: Bar aggregation period.
            limit: Maximum number of bars to return (None = no limit).

        Returns:
            DataFrame with DatetimeIndex (UTC) and columns
            [open, high, low, close, volume, vwap, trade_count].
            Sorted ascending by timestamp. Empty DataFrame if no data.
        """
        raise NotImplementedError

    @abstractmethod
    def get_multi_bars(
        self,
        symbols: list[str],
        start: datetime,
        end: datetime,
        timeframe: Timeframe = Timeframe.DAY_1,
    ) -> dict[str, pd.DataFrame]:
        """Fetch OHLCV bars for multiple symbols in one call.

        Args:
            symbols: List of ticker symbols.
            start: Start of the requested time range (UTC-aware).
            end: End of the requested time range (UTC-aware).
            timeframe: Bar aggregation period.

        Returns:
            Mapping of symbol → DataFrame (same schema as get_bars).
            Missing symbols return an empty DataFrame.
        """
        raise NotImplementedError

    @abstractmethod
    def get_latest_bar(self, symbol: str) -> Bar | None:
        """Fetch the most recent completed bar for *symbol*.

        Args:
            symbol: Ticker symbol.

        Returns:
            Most recent Bar, or None if unavailable.
        """
        raise NotImplementedError

    @abstractmethod
    def get_latest_bars(self, symbols: list[str]) -> dict[str, Bar | None]:
        """Fetch the most recent completed bar for each symbol.

        Args:
            symbols: List of tickers.

        Returns:
            Mapping of symbol → Bar (or None if unavailable).
        """
        raise NotImplementedError

    # ------------------------------------------------------------------- Quote

    @abstractmethod
    def get_latest_quote(self, symbol: str) -> Quote | None:
        """Fetch the latest bid/ask quote for *symbol*.

        Args:
            symbol: Ticker symbol.

        Returns:
            Most recent Quote, or None if unavailable.
        """
        raise NotImplementedError

    # ------------------------------------------------------------------ Assets

    @abstractmethod
    def get_assets(
        self,
        asset_class: AssetClass = AssetClass.US_EQUITY,
        tradable_only: bool = True,
    ) -> list[AssetInfo]:
        """List available assets.

        Args:
            asset_class: Filter by asset class.
            tradable_only: If True, only return assets currently tradable on Alpaca.

        Returns:
            List of AssetInfo objects.
        """
        raise NotImplementedError

    @abstractmethod
    def get_asset(self, symbol: str) -> AssetInfo | None:
        """Return metadata for a single asset.

        Args:
            symbol: Ticker symbol.

        Returns:
            AssetInfo, or None if the symbol is not found.
        """
        raise NotImplementedError

    # ------------------------------------------------------------- Live stream

    @abstractmethod
    def subscribe_bars(
        self,
        symbols: list[str],
        callback: Callable[[Bar], None],
    ) -> None:
        """Subscribe to real-time bar updates for *symbols*.

        The *callback* is invoked on every new bar received from the
        WebSocket stream. This method is non-blocking — the stream runs
        in a background thread.

        Args:
            symbols: Tickers to subscribe to.
            callback: Async or sync function called with each new Bar.
        """
        raise NotImplementedError

    @abstractmethod
    def subscribe_quotes(
        self,
        symbols: list[str],
        callback: Callable[[Quote], None],
    ) -> None:
        """Subscribe to real-time quote (bid/ask) updates.

        Args:
            symbols: Tickers to subscribe to.
            callback: Function called with each new Quote.
        """
        raise NotImplementedError

    @abstractmethod
    def unsubscribe_all(self) -> None:
        """Cancel all active WebSocket subscriptions and close the connection."""
        raise NotImplementedError

    # ----------------------------------------------------------- Utility helpers

    def get_close_prices(
        self,
        symbols: list[str],
        start: datetime,
        end: datetime,
        timeframe: Timeframe = Timeframe.DAY_1,
    ) -> pd.DataFrame:
        """Return a wide DataFrame of closing prices, one column per symbol.

        Useful for constructing the return matrix needed by the portfolio
        optimiser and risk analyser.

        Args:
            symbols: List of tickers.
            start: Start of date range (UTC-aware).
            end: End of date range (UTC-aware).
            timeframe: Bar timeframe.

        Returns:
            DataFrame with DatetimeIndex, columns = symbols, values = close price.
            Missing dates are forward-filled.
        """
        bars = self.get_multi_bars(symbols, start, end, timeframe)
        frames = {sym: df["close"].rename(sym) for sym, df in bars.items() if not df.empty}
        if not frames:
            return pd.DataFrame()
        result = pd.concat(frames.values(), axis=1)
        return result.ffill()

    def get_returns(
        self,
        symbols: list[str],
        start: datetime,
        end: datetime,
        timeframe: Timeframe = Timeframe.DAY_1,
    ) -> pd.DataFrame:
        """Return a wide DataFrame of daily log returns, one column per symbol.

        Args:
            symbols: List of tickers.
            start: Start of date range (UTC-aware).
            end: End of date range (UTC-aware).
            timeframe: Bar timeframe.

        Returns:
            DataFrame with DatetimeIndex, columns = symbols, values = log return.
            NaN for the first row.
        """
        import numpy as np

        prices = self.get_close_prices(symbols, start, end, timeframe)
        return np.log(prices / prices.shift(1))
