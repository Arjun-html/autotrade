"""Signal Generator package.

Generates trade ideas by combining multiple signal sources:
- Time series models (ARIMA, SARIMA, Holt-Winters)
- Neural networks (LSTM, Transformer)
- LLM-based sentiment analysis

All signal generators implement the SignalGenerator ABC from signals.base.
"""

from .base import Signal, SignalDirection, SignalGenerator

__all__ = ["Signal", "SignalDirection", "SignalGenerator"]
