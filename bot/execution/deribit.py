"""Order execution adapter for Deribit."""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Dict, Optional

import requests

logger = logging.getLogger(__name__)


@dataclass
class Order:
    instrument_name: str
    side: str
    amount: float
    price: Optional[float] = None
    order_type: str = "limit"


class DeribitExecutionClient:
    """Small wrapper around Deribit order placement endpoints."""

    BASE_URL = "https://www.deribit.com/api/v2"

    def __init__(self, token: Optional[str] = None) -> None:
        self.session = requests.Session()
        self.token = token

    def _request(self, endpoint: str, params: Dict) -> Dict:
        headers = {"Authorization": f"Bearer {self.token}"} if self.token else {}
        response = self.session.post(f"{self.BASE_URL}{endpoint}", json=params, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()

    def place_order(self, order: Order) -> Dict:
        params = {
            "instrument_name": order.instrument_name,
            "amount": order.amount,
            "type": order.order_type,
            "side": order.side,
        }
        if order.price is not None:
            params["price"] = order.price
        logger.info("Placing Deribit order: %s", params)
        return self._request("/private/buy" if order.side == "buy" else "/private/sell", params)


__all__ = ["DeribitExecutionClient", "Order"]
