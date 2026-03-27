"""Trade Execution package.

Converts approved trade signals into real broker orders. Currently targets
Alpaca's paper trading environment. All brokers implement the Broker ABC
from execution.base so the rest of the system stays broker-agnostic.
"""

from .base import Broker, Order, OrderStatus, OrderSide, OrderType
from .alpaca import AlpacaBroker

__all__ = ["Broker", "Order", "OrderStatus", "OrderSide", "OrderType", "AlpacaBroker"]
