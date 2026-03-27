"""Alpaca paper trading broker implementation.

Uses the alpaca-py SDK to submit, monitor, and cancel orders against
Alpaca's paper trading environment.

TODO: Implement each method using alpaca.trading.TradingClient.
"""

from __future__ import annotations

from typing import Any

from .base import Broker, Order, OrderSide, OrderStatus, OrderType


class AlpacaBroker(Broker):
    """Broker implementation backed by Alpaca paper trading.

    Args:
        api_key: Alpaca paper trading API key.
        secret_key: Alpaca paper trading secret key.
        paper: If True (default), targets the paper trading endpoint.
    """

    def __init__(self, api_key: str, secret_key: str, paper: bool = True) -> None:
        self.api_key = api_key
        self.secret_key = secret_key
        self.paper = paper
        self._client = None  # Initialised lazily in _get_client()

    def _get_client(self):
        """Lazily initialise and return the alpaca-py TradingClient."""
        if self._client is None:
            from alpaca.trading.client import TradingClient

            self._client = TradingClient(
                api_key=self.api_key,
                secret_key=self.secret_key,
                paper=self.paper,
            )
        return self._client

    def submit_order(self, order: Order) -> Order:
        """Submit *order* to Alpaca and return updated Order with broker ID.

        TODO: Map Order fields to alpaca.trading.requests.MarketOrderRequest
        (or LimitOrderRequest etc.) and call client.submit_order().
        """
        raise NotImplementedError

    def cancel_order(self, broker_order_id: str) -> bool:
        """Cancel order by Alpaca UUID.

        TODO: Call client.cancel_order_by_id(broker_order_id).
        """
        raise NotImplementedError

    def get_order(self, broker_order_id: str) -> Order:
        """Fetch latest order state from Alpaca.

        TODO: Call client.get_order_by_id() and map to Order dataclass.
        """
        raise NotImplementedError

    def get_open_orders(self) -> list[Order]:
        """Return all open Alpaca orders.

        TODO: Call client.get_orders(filter=GetOrdersRequest(status="open"))
        and map to Order list.
        """
        raise NotImplementedError

    def get_account_info(self) -> dict[str, Any]:
        """Return Alpaca account details.

        TODO: Call client.get_account() and return as a plain dict.
        """
        raise NotImplementedError
