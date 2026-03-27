"""Abstract base classes for trade execution."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class OrderSide(str, Enum):
    BUY = "buy"
    SELL = "sell"


class OrderType(str, Enum):
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"


class OrderStatus(str, Enum):
    PENDING = "pending"
    SUBMITTED = "submitted"
    FILLED = "filled"
    PARTIALLY_FILLED = "partially_filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"


@dataclass
class Order:
    """Represents a broker order.

    Attributes:
        symbol: Ticker symbol.
        side: Buy or sell.
        qty: Number of shares.
        order_type: Market, limit, stop, etc.
        limit_price: Required for LIMIT and STOP_LIMIT orders.
        stop_price: Required for STOP and STOP_LIMIT orders.
        status: Current order lifecycle status.
        broker_order_id: ID returned by the broker after submission.
        submitted_at: UTC timestamp of submission.
        filled_at: UTC timestamp of fill (None if not filled).
        filled_price: Average fill price (None if not filled).
        metadata: Additional order metadata.
    """

    symbol: str
    side: OrderSide
    qty: float
    order_type: OrderType = OrderType.MARKET
    limit_price: float | None = None
    stop_price: float | None = None
    status: OrderStatus = OrderStatus.PENDING
    broker_order_id: str | None = None
    submitted_at: datetime | None = None
    filled_at: datetime | None = None
    filled_price: float | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class Broker(ABC):
    """Abstract interface for a brokerage connection.

    All broker-specific logic (Alpaca, Interactive Brokers, etc.) lives in
    concrete subclasses so the rest of the system never depends on a
    specific broker's API.
    """

    @abstractmethod
    def submit_order(self, order: Order) -> Order:
        """Submit an order to the broker and return the updated Order with broker_order_id.

        Args:
            order: The order to submit.

        Returns:
            Updated Order with status SUBMITTED and broker_order_id set.
        """
        raise NotImplementedError

    @abstractmethod
    def cancel_order(self, broker_order_id: str) -> bool:
        """Cancel an open order by its broker ID.

        Returns:
            True if successfully cancelled, False otherwise.
        """
        raise NotImplementedError

    @abstractmethod
    def get_order(self, broker_order_id: str) -> Order:
        """Fetch the current state of an order from the broker.

        Args:
            broker_order_id: The broker-assigned order ID.

        Returns:
            Updated Order reflecting current status and fill details.
        """
        raise NotImplementedError

    @abstractmethod
    def get_open_orders(self) -> list[Order]:
        """Return all currently open (unfilled) orders."""
        raise NotImplementedError

    @abstractmethod
    def get_account_info(self) -> dict[str, Any]:
        """Return account information including cash, buying power, and equity."""
        raise NotImplementedError
