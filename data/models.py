"""Canonical data models shared across all system components.

These are the types that flow out of the DataProvider and into the
Signal Generator, Portfolio Manager, and Backtester. Using a shared
model layer keeps every consumer decoupled from the specific broker SDK.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class Timeframe(str, Enum):
    """Bar aggregation timeframes supported by Alpaca's data API."""

    MIN_1 = "1Min"
    MIN_5 = "5Min"
    MIN_15 = "15Min"
    MIN_30 = "30Min"
    HOUR_1 = "1Hour"
    HOUR_4 = "4Hour"
    DAY_1 = "1Day"
    WEEK_1 = "1Week"
    MONTH_1 = "1Month"


class AssetClass(str, Enum):
    """Asset classes available through Alpaca."""

    US_EQUITY = "us_equity"
    CRYPTO = "crypto"


class Bar(BaseModel):
    """A single OHLCV price bar.

    Attributes:
        symbol: Ticker symbol (e.g. "AAPL").
        timestamp: Bar open time in UTC.
        open: Opening price.
        high: Highest price during the bar.
        low: Lowest price during the bar.
        close: Closing price.
        volume: Number of shares/units traded.
        vwap: Volume-weighted average price (None if not provided by feed).
        trade_count: Number of trades during bar (None if not provided).
        timeframe: The bar aggregation period.
    """

    symbol: str
    timestamp: datetime
    open: float = Field(gt=0)
    high: float = Field(gt=0)
    low: float = Field(gt=0)
    close: float = Field(gt=0)
    volume: float = Field(ge=0)
    vwap: Optional[float] = None
    trade_count: Optional[int] = None
    timeframe: Timeframe = Timeframe.DAY_1

    @field_validator("high")
    @classmethod
    def high_gte_low(cls, v: float, info) -> float:
        low = info.data.get("low")
        if low is not None and v < low:
            raise ValueError(f"high ({v}) must be >= low ({low})")
        return v

    @property
    def mid(self) -> float:
        """Midpoint of high and low."""
        return (self.high + self.low) / 2.0

    @property
    def range(self) -> float:
        """Bar range (high - low)."""
        return self.high - self.low

    @property
    def return_(self) -> float:
        """Bar return: (close - open) / open."""
        return (self.close - self.open) / self.open


class Quote(BaseModel):
    """A real-time bid/ask quote.

    Attributes:
        symbol: Ticker symbol.
        timestamp: Quote timestamp in UTC.
        bid_price: Best bid price.
        bid_size: Shares available at bid.
        ask_price: Best ask price.
        ask_size: Shares available at ask.
        conditions: Exchange condition codes (optional).
        tape: Tape identifier ("A", "B", or "C").
    """

    symbol: str
    timestamp: datetime
    bid_price: float = Field(ge=0)
    bid_size: float = Field(ge=0)
    ask_price: float = Field(ge=0)
    ask_size: float = Field(ge=0)
    conditions: list[str] = Field(default_factory=list)
    tape: Optional[str] = None

    @property
    def spread(self) -> float:
        """Bid-ask spread in dollars."""
        return self.ask_price - self.bid_price

    @property
    def mid_price(self) -> float:
        """Midpoint of bid and ask."""
        return (self.bid_price + self.ask_price) / 2.0


class AssetInfo(BaseModel):
    """Static information about a tradable asset.

    Attributes:
        symbol: Ticker symbol.
        name: Full company / asset name.
        asset_class: "us_equity" or "crypto".
        exchange: Primary exchange (e.g. "NASDAQ", "NYSE").
        tradable: Whether Alpaca currently allows trading this asset.
        fractionable: Whether fractional shares are supported.
        shortable: Whether short selling is permitted.
        easy_to_borrow: Whether the stock is easy to borrow for shorting.
        marginable: Whether the asset can be held on margin.
    """

    symbol: str
    name: str = ""
    asset_class: AssetClass = AssetClass.US_EQUITY
    exchange: str = ""
    tradable: bool = True
    fractionable: bool = False
    shortable: bool = False
    easy_to_borrow: bool = False
    marginable: bool = False


class BarSeries(BaseModel):
    """A collection of OHLCV bars for a single symbol, suitable for passing
    between system components."""

    symbol: str
    timeframe: Timeframe
    bars: list[Bar] = Field(default_factory=list)

    def to_dataframe(self):
        """Convert to a pandas DataFrame with DatetimeIndex.

        Returns:
            DataFrame with columns [open, high, low, close, volume, vwap, trade_count]
            and timestamp as index.
        """
        import pandas as pd

        if not self.bars:
            return pd.DataFrame(
                columns=["open", "high", "low", "close", "volume", "vwap", "trade_count"]
            )

        records = [
            {
                "timestamp": b.timestamp,
                "open": b.open,
                "high": b.high,
                "low": b.low,
                "close": b.close,
                "volume": b.volume,
                "vwap": b.vwap,
                "trade_count": b.trade_count,
            }
            for b in self.bars
        ]
        df = pd.DataFrame(records).set_index("timestamp")
        df.index = pd.to_datetime(df.index, utc=True)
        return df
