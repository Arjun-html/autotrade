"""Alpaca market data provider.

Implements the DataProvider ABC using the official alpaca-py SDK.

Historical data (REST):
  - alpaca.data.historical.StockHistoricalDataClient
  - alpaca.data.historical.CryptoHistoricalDataClient

Live data (WebSocket):
  - alpaca.data.live.StockDataStream
  - alpaca.data.live.CryptoDataStream

Asset listings:
  - alpaca.trading.TradingClient (reuses the trading client already needed for
    the execution module — no extra credentials required)

Free-tier note: The IEX feed is used by default and covers US equities with a
~15-minute delay outside market hours. Switch to 'sip' (paid) for real-time.
"""

from __future__ import annotations

import logging
import threading
from datetime import datetime, timezone
from typing import Callable

import pandas as pd

from data.base import DataProvider
from data.models import AssetClass, AssetInfo, Bar, Quote, Timeframe

logger = logging.getLogger(__name__)

# ----------------------------------------------------------------- timeframe map

_ALPACA_TIMEFRAME_MAP: dict[Timeframe, object] = {}  # built lazily after import


def _get_alpaca_timeframe(tf: Timeframe):
    """Map our Timeframe enum to an alpaca-py TimeFrame object."""
    global _ALPACA_TIMEFRAME_MAP
    if not _ALPACA_TIMEFRAME_MAP:
        from alpaca.data.timeframe import TimeFrame, TimeFrameUnit

        _ALPACA_TIMEFRAME_MAP = {
            Timeframe.MIN_1: TimeFrame(1, TimeFrameUnit.Minute),
            Timeframe.MIN_5: TimeFrame(5, TimeFrameUnit.Minute),
            Timeframe.MIN_15: TimeFrame(15, TimeFrameUnit.Minute),
            Timeframe.MIN_30: TimeFrame(30, TimeFrameUnit.Minute),
            Timeframe.HOUR_1: TimeFrame(1, TimeFrameUnit.Hour),
            Timeframe.HOUR_4: TimeFrame(4, TimeFrameUnit.Hour),
            Timeframe.DAY_1: TimeFrame(1, TimeFrameUnit.Day),
            Timeframe.WEEK_1: TimeFrame(1, TimeFrameUnit.Week),
            Timeframe.MONTH_1: TimeFrame(1, TimeFrameUnit.Month),
        }
    return _ALPACA_TIMEFRAME_MAP[tf]


# ------------------------------------------------------------------ converters

def _bars_response_to_df(bars_dict: dict, symbol: str) -> pd.DataFrame:
    """Convert an alpaca-py bars response dict to a normalised DataFrame."""
    if not bars_dict or symbol not in bars_dict:
        return pd.DataFrame(
            columns=["open", "high", "low", "close", "volume", "vwap", "trade_count"]
        )

    records = []
    for bar in bars_dict[symbol]:
        records.append(
            {
                "timestamp": bar.timestamp,
                "open": float(bar.open),
                "high": float(bar.high),
                "low": float(bar.low),
                "close": float(bar.close),
                "volume": float(bar.volume),
                "vwap": float(bar.vwap) if hasattr(bar, "vwap") and bar.vwap else None,
                "trade_count": int(bar.trade_count)
                if hasattr(bar, "trade_count") and bar.trade_count
                else None,
            }
        )

    if not records:
        return pd.DataFrame(
            columns=["open", "high", "low", "close", "volume", "vwap", "trade_count"]
        )

    df = pd.DataFrame(records).set_index("timestamp")
    df.index = pd.to_datetime(df.index, utc=True)
    return df.sort_index()


def _alpaca_bar_to_model(bar, symbol: str, timeframe: Timeframe) -> Bar:
    """Convert an alpaca-py Bar object to our Bar model."""
    return Bar(
        symbol=symbol,
        timestamp=bar.timestamp,
        open=float(bar.open),
        high=float(bar.high),
        low=float(bar.low),
        close=float(bar.close),
        volume=float(bar.volume),
        vwap=float(bar.vwap) if hasattr(bar, "vwap") and bar.vwap else None,
        trade_count=int(bar.trade_count)
        if hasattr(bar, "trade_count") and bar.trade_count
        else None,
        timeframe=timeframe,
    )


def _alpaca_quote_to_model(quote, symbol: str) -> Quote:
    """Convert an alpaca-py Quote object to our Quote model."""
    return Quote(
        symbol=symbol,
        timestamp=quote.timestamp,
        bid_price=float(quote.bid_price),
        bid_size=float(quote.bid_size),
        ask_price=float(quote.ask_price),
        ask_size=float(quote.ask_size),
        conditions=list(quote.conditions) if hasattr(quote, "conditions") and quote.conditions else [],
        tape=str(quote.tape) if hasattr(quote, "tape") and quote.tape else None,
    )


def _alpaca_asset_to_model(asset) -> AssetInfo:
    """Convert an alpaca-py Asset object to our AssetInfo model."""
    return AssetInfo(
        symbol=asset.symbol,
        name=asset.name or "",
        asset_class=AssetClass.US_EQUITY
        if str(asset.asset_class) in ("us_equity", "AssetClass.US_EQUITY")
        else AssetClass.CRYPTO,
        exchange=str(asset.exchange) if asset.exchange else "",
        tradable=bool(asset.tradable),
        fractionable=bool(asset.fractionable) if hasattr(asset, "fractionable") else False,
        shortable=bool(asset.shortable) if hasattr(asset, "shortable") else False,
        easy_to_borrow=bool(asset.easy_to_borrow) if hasattr(asset, "easy_to_borrow") else False,
        marginable=bool(asset.marginable) if hasattr(asset, "marginable") else False,
    )


# ------------------------------------------------------------------ main class

class AlpacaDataProvider(DataProvider):
    """Market data provider backed by Alpaca's data API.

    Args:
        api_key: Alpaca API key (paper or live key both work for data).
        secret_key: Alpaca secret key.
        feed: Data feed — "iex" (free, ~15 min delay) or "sip" (paid, real-time).
        paper: Whether to use paper trading credentials for account/asset queries.
    """

    def __init__(
        self,
        api_key: str,
        secret_key: str,
        feed: str = "iex",
        paper: bool = True,
    ) -> None:
        self.api_key = api_key
        self.secret_key = secret_key
        self.feed = feed
        self.paper = paper

        # Lazily initialised clients
        self._stock_client = None
        self._trading_client = None
        self._stock_stream = None
        self._stream_thread: threading.Thread | None = None

    # ----------------------------------------------------------------- clients

    def _get_stock_client(self):
        if self._stock_client is None:
            from alpaca.data.historical import StockHistoricalDataClient

            self._stock_client = StockHistoricalDataClient(
                api_key=self.api_key,
                secret_key=self.secret_key,
            )
        return self._stock_client

    def _get_trading_client(self):
        if self._trading_client is None:
            from alpaca.trading.client import TradingClient

            self._trading_client = TradingClient(
                api_key=self.api_key,
                secret_key=self.secret_key,
                paper=self.paper,
            )
        return self._trading_client

    # -------------------------------------------------------------- historical

    def get_bars(
        self,
        symbol: str,
        start: datetime,
        end: datetime,
        timeframe: Timeframe = Timeframe.DAY_1,
        limit: int | None = None,
    ) -> pd.DataFrame:
        """Fetch historical OHLCV bars from Alpaca REST API."""
        from alpaca.data.requests import StockBarsRequest

        request = StockBarsRequest(
            symbol_or_symbols=symbol,
            start=start,
            end=end,
            timeframe=_get_alpaca_timeframe(timeframe),
            feed=self.feed,
            limit=limit,
        )
        try:
            response = self._get_stock_client().get_stock_bars(request)
            df = _bars_response_to_df(response.data, symbol)
            logger.debug("Fetched %d bars for %s (%s)", len(df), symbol, timeframe.value)
            return df
        except Exception:
            logger.error("Failed to fetch bars for %s", symbol, exc_info=True)
            return pd.DataFrame(
                columns=["open", "high", "low", "close", "volume", "vwap", "trade_count"]
            )

    def get_multi_bars(
        self,
        symbols: list[str],
        start: datetime,
        end: datetime,
        timeframe: Timeframe = Timeframe.DAY_1,
    ) -> dict[str, pd.DataFrame]:
        """Fetch bars for multiple symbols in one API call."""
        from alpaca.data.requests import StockBarsRequest

        request = StockBarsRequest(
            symbol_or_symbols=symbols,
            start=start,
            end=end,
            timeframe=_get_alpaca_timeframe(timeframe),
            feed=self.feed,
        )
        result: dict[str, pd.DataFrame] = {}
        try:
            response = self._get_stock_client().get_stock_bars(request)
            for sym in symbols:
                result[sym] = _bars_response_to_df(response.data, sym)
        except Exception:
            logger.error("Failed to fetch multi-bars", exc_info=True)
            empty = pd.DataFrame(
                columns=["open", "high", "low", "close", "volume", "vwap", "trade_count"]
            )
            result = {sym: empty.copy() for sym in symbols}
        return result

    def get_latest_bar(self, symbol: str) -> Bar | None:
        """Fetch the most recent completed bar."""
        from alpaca.data.requests import StockLatestBarRequest

        request = StockLatestBarRequest(
            symbol_or_symbols=symbol,
            feed=self.feed,
        )
        try:
            response = self._get_stock_client().get_stock_latest_bar(request)
            bar_data = response.get(symbol)
            if bar_data is None:
                return None
            return _alpaca_bar_to_model(bar_data, symbol, Timeframe.DAY_1)
        except Exception:
            logger.error("Failed to fetch latest bar for %s", symbol, exc_info=True)
            return None

    def get_latest_bars(self, symbols: list[str]) -> dict[str, Bar | None]:
        """Fetch latest bars for multiple symbols."""
        from alpaca.data.requests import StockLatestBarRequest

        request = StockLatestBarRequest(
            symbol_or_symbols=symbols,
            feed=self.feed,
        )
        result: dict[str, Bar | None] = {sym: None for sym in symbols}
        try:
            response = self._get_stock_client().get_stock_latest_bar(request)
            for sym in symbols:
                bar_data = response.get(sym)
                if bar_data is not None:
                    result[sym] = _alpaca_bar_to_model(bar_data, sym, Timeframe.DAY_1)
        except Exception:
            logger.error("Failed to fetch latest bars", exc_info=True)
        return result

    # --------------------------------------------------------------- quotes

    def get_latest_quote(self, symbol: str) -> Quote | None:
        """Fetch the latest bid/ask quote."""
        from alpaca.data.requests import StockLatestQuoteRequest

        request = StockLatestQuoteRequest(
            symbol_or_symbols=symbol,
            feed=self.feed,
        )
        try:
            response = self._get_stock_client().get_stock_latest_quote(request)
            quote_data = response.get(symbol)
            if quote_data is None:
                return None
            return _alpaca_quote_to_model(quote_data, symbol)
        except Exception:
            logger.error("Failed to fetch quote for %s", symbol, exc_info=True)
            return None

    # --------------------------------------------------------------- assets

    def get_assets(
        self,
        asset_class: AssetClass = AssetClass.US_EQUITY,
        tradable_only: bool = True,
    ) -> list[AssetInfo]:
        """Return a list of available tradable assets from Alpaca."""
        from alpaca.trading.requests import GetAssetsRequest
        from alpaca.trading.enums import AssetClass as AlpacaAssetClass, AssetStatus

        alpaca_class = (
            AlpacaAssetClass.US_EQUITY
            if asset_class == AssetClass.US_EQUITY
            else AlpacaAssetClass.CRYPTO
        )
        request = GetAssetsRequest(
            asset_class=alpaca_class,
            status=AssetStatus.ACTIVE,
        )
        try:
            assets = self._get_trading_client().get_all_assets(request)
            result = [_alpaca_asset_to_model(a) for a in assets]
            if tradable_only:
                result = [a for a in result if a.tradable]
            logger.info("Fetched %d assets (tradable_only=%s)", len(result), tradable_only)
            return result
        except Exception:
            logger.error("Failed to fetch assets", exc_info=True)
            return []

    def get_asset(self, symbol: str) -> AssetInfo | None:
        """Return metadata for a single asset."""
        try:
            asset = self._get_trading_client().get_asset(symbol)
            return _alpaca_asset_to_model(asset)
        except Exception:
            logger.error("Failed to fetch asset info for %s", symbol, exc_info=True)
            return None

    # --------------------------------------------------------------- streaming

    def _get_stock_stream(self):
        if self._stock_stream is None:
            from alpaca.data.live import StockDataStream

            self._stock_stream = StockDataStream(
                api_key=self.api_key,
                secret_key=self.secret_key,
                feed=self.feed,
            )
        return self._stock_stream

    def subscribe_bars(
        self,
        symbols: list[str],
        callback: Callable[[Bar], None],
    ) -> None:
        """Subscribe to real-time minute bars via WebSocket.

        The WebSocket run loop is started in a daemon thread so it does
        not block the main Streamlit process.
        """
        stream = self._get_stock_stream()

        async def _on_bar(bar):
            model = _alpaca_bar_to_model(bar, bar.symbol, Timeframe.MIN_1)
            callback(model)

        stream.subscribe_bars(_on_bar, *symbols)
        self._ensure_stream_running()
        logger.info("Subscribed to bars for: %s", symbols)

    def subscribe_quotes(
        self,
        symbols: list[str],
        callback: Callable[[Quote], None],
    ) -> None:
        """Subscribe to real-time quotes via WebSocket."""
        stream = self._get_stock_stream()

        async def _on_quote(quote):
            model = _alpaca_quote_to_model(quote, quote.symbol)
            callback(model)

        stream.subscribe_quotes(_on_quote, *symbols)
        self._ensure_stream_running()
        logger.info("Subscribed to quotes for: %s", symbols)

    def _ensure_stream_running(self) -> None:
        """Start the WebSocket event loop in a background daemon thread if not running."""
        if self._stream_thread is not None and self._stream_thread.is_alive():
            return

        def _run():
            try:
                self._get_stock_stream().run()
            except Exception:
                logger.error("Stock data stream crashed", exc_info=True)

        self._stream_thread = threading.Thread(target=_run, daemon=True, name="alpaca-stream")
        self._stream_thread.start()
        logger.info("Started Alpaca WebSocket stream thread")

    def unsubscribe_all(self) -> None:
        """Stop the WebSocket stream and close the connection."""
        if self._stock_stream is not None:
            try:
                self._stock_stream.stop()
            except Exception:
                logger.warning("Error stopping stock stream", exc_info=True)
            self._stock_stream = None
        self._stream_thread = None
        logger.info("Unsubscribed from all streams")
