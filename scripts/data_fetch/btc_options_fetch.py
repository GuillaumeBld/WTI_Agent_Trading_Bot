"""BTC options data ingestion utilities backed by Deribit."""
from __future__ import annotations

from typing import List, Sequence

from agent_interfaces import OptionsChainData
from bot.data import DeribitMarketDataClient


def _parse_api_key(api_key: str | None) -> tuple[str | None, str | None]:
    if not api_key:
        return None, None
    if ":" in api_key:
        client_id, client_secret = api_key.split(":", 1)
        return client_id.strip() or None, client_secret.strip() or None
    return api_key, None


def fetch_btc_options_data(api_key: str | None, symbol: str, expiries: Sequence[str]) -> List[OptionsChainData]:
    """Fetch BTC options data from Deribit and map it into pydantic models."""

    client_id, client_secret = _parse_api_key(api_key)
    client = DeribitMarketDataClient(client_id=client_id, client_secret=client_secret)
    return client.fetch_options_chain(expiries=expiries, currency=symbol)


__all__ = ["fetch_btc_options_data"]
