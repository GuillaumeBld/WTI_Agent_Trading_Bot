"""High level interface for Deribit-backed market data fetching."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import List, Sequence

from agent_interfaces import OptionsChainData

from .deribit_client import DeribitMarketDataClient


@dataclass
class MarketDataPipeline:
    """Small facade exposing Deribit options data to the wider application."""

    client: DeribitMarketDataClient = field(default_factory=DeribitMarketDataClient)
    currency: str = "BTC"

    def fetch_option_chains(self, expiries: Sequence[str], *, refresh: bool = False) -> List[OptionsChainData]:
        return self.client.fetch_options_chain(expiries=expiries, currency=self.currency, refresh=refresh)


def build_pipeline_from_env() -> MarketDataPipeline:
    """Build a :class:`MarketDataPipeline` using environment defaults."""

    currency = os.getenv("DERIBIT_UNDERLYING", "BTC")
    client = DeribitMarketDataClient(
        client_id=os.getenv("DERIBIT_CLIENT_ID"),
        client_secret=os.getenv("DERIBIT_CLIENT_SECRET"),
    )
    return MarketDataPipeline(client=client, currency=currency)


__all__ = ["MarketDataPipeline", "build_pipeline_from_env"]
