"""Abstract base classes for the Signal Generator module."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

import pandas as pd


class SignalDirection(str, Enum):
    """Direction of a trade signal."""

    LONG = "long"
    SHORT = "short"
    HOLD = "hold"


@dataclass
class Signal:
    """A single trade recommendation produced by a SignalGenerator.

    Attributes:
        symbol: Ticker symbol (e.g. "AAPL").
        direction: Whether to go long, short, or hold.
        confidence: Probability-like score in [0, 1].
        predicted_return: Expected return over the signal's horizon (fractional).
        horizon_days: Number of trading days the signal is valid for.
        generated_at: UTC timestamp when the signal was created.
        generator_name: Name of the SignalGenerator that produced this signal.
        metadata: Arbitrary extra information (model params, feature values, etc.).
    """

    symbol: str
    direction: SignalDirection
    confidence: float
    predicted_return: float = 0.0
    horizon_days: int = 1
    generated_at: datetime = field(default_factory=datetime.utcnow)
    generator_name: str = "unknown"
    metadata: dict[str, Any] = field(default_factory=dict)


class SignalGenerator(ABC):
    """Abstract base class for all signal generators.

    Every concrete signal generator (time series, neural network, LLM, etc.)
    must implement `generate`. The system can then aggregate signals from
    multiple generators via the EnsembleSignalGenerator.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique name identifying this generator (used in Signal.generator_name)."""
        ...

    @abstractmethod
    def generate(self, symbol: str, data: pd.DataFrame) -> Signal:
        """Produce a trade signal for *symbol* given recent market *data*.

        Args:
            symbol: Ticker to generate a signal for.
            data: OHLCV DataFrame with a DatetimeIndex, as returned by
                  DataProvider.get_bars().

        Returns:
            A Signal instance with direction, confidence, and predicted return.
        """
        raise NotImplementedError

    @abstractmethod
    def fit(self, symbol: str, data: pd.DataFrame) -> None:
        """Train / update the model on historical *data*.

        Args:
            symbol: Ticker being fitted.
            data: Full historical OHLCV DataFrame for training.
        """
        raise NotImplementedError
