from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Dict, Tuple

import pytest

from bot.data.deribit_client import DeribitMarketDataClient


class FakeResponse:
    def __init__(self, payload: Dict):
        self._payload = payload

    def raise_for_status(self) -> None:  # pragma: no cover - no errors triggered in tests
        return None

    def json(self) -> Dict:
        return self._payload


class FakeSession:
    def __init__(self, responses: Dict[Tuple[str, str, Tuple[Tuple[str, object], ...]], Dict]):
        self._responses = responses
        self.calls: list[Tuple[str, str, Tuple[Tuple[str, object], ...]]] = []

    def request(self, method: str, url: str, **kwargs) -> FakeResponse:
        params = kwargs.get("params") or {}
        key = (method.upper(), url, tuple(sorted(params.items())))
        self.calls.append(key)
        if key not in self._responses:
            raise AssertionError(f"Unexpected request {key}")
        return FakeResponse(self._responses[key])


class FailSession(FakeSession):
    def __init__(self) -> None:
        super().__init__({})

    def request(self, method: str, url: str, **kwargs) -> FakeResponse:  # pragma: no cover - cache prevents call
        raise AssertionError("HTTP request should not be executed when cache is warm")


@pytest.fixture
def sample_responses() -> Dict[Tuple[str, str, Tuple[Tuple[str, object], ...]], Dict]:
    base_url = "https://www.deribit.com/api/v2"
    expiry = datetime(2024, 5, 24, 8, 0, 0, tzinfo=UTC)
    instrument_call = {
        "instrument_name": "BTC-24MAY24-60000-C",
        "expiration_timestamp": int(expiry.timestamp() * 1000),
        "strike": 60000.0,
        "option_type": "call",
    }
    instrument_put = {
        "instrument_name": "BTC-24MAY24-60000-P",
        "expiration_timestamp": int(expiry.timestamp() * 1000),
        "strike": 60000.0,
        "option_type": "put",
    }
    return {
        ("GET", f"{base_url}/public/get_instruments", (
            ("currency", "BTC"),
            ("expired", False),
            ("kind", "option"),
        )): {"result": [instrument_call, instrument_put]},
        ("GET", f"{base_url}/public/get_book_summary_by_instrument", (
            ("instrument_name", "BTC-24MAY24-60000-C"),
        )): {"result": [{
            "underlying_price": 61234.5,
            "mark_iv": 0.65,
            "volume": 123,
            "open_interest": 456,
            "delta": 0.42,
            "gamma": 0.001,
            "theta": -0.5,
            "vega": 25.0,
            "last_price": 950.0,
        }]},
        ("GET", f"{base_url}/public/get_book_summary_by_instrument", (
            ("instrument_name", "BTC-24MAY24-60000-P"),
        )): {"result": [{
            "underlying_price": 61234.5,
            "mark_iv": 0.72,
            "volume": 45,
            "open_interest": 890,
            "delta": -0.58,
            "gamma": 0.002,
            "theta": -0.4,
            "vega": 30.0,
            "last_price": 1020.0,
        }]},
    }


def test_fetch_options_chain_parses_deribit_payload(tmp_path: Path, sample_responses) -> None:
    session = FakeSession(sample_responses)
    client = DeribitMarketDataClient(session=session, cache_dir=tmp_path)

    chains = client.fetch_options_chain(expiries=["2024-05-24T08:00:00Z"], currency="BTC")

    assert len(chains) == 1
    chain = chains[0]
    assert chain.underlying_symbol == "BTC"
    assert chain.expiry_date == datetime(2024, 5, 24, 8, 0, 0, tzinfo=UTC)
    assert chain.spot_price == pytest.approx(61234.5)
    strikes = sorted(contract.strike_price for contract in chain.contracts)
    assert strikes == [60000.0, 60000.0]
    call = next(c for c in chain.contracts if c.contract_type == "call")
    assert call.implied_volatility == pytest.approx(0.65)
    assert call.delta == pytest.approx(0.42)
    assert session.calls  # network was invoked


def test_fetch_options_chain_uses_cache(tmp_path: Path, sample_responses) -> None:
    cache_dir = tmp_path / "cache"
    session = FakeSession(sample_responses)
    client = DeribitMarketDataClient(session=session, cache_dir=cache_dir)
    _ = client.fetch_options_chain(expiries=["2024-05-24T08:00:00Z"], currency="BTC")
    assert session.calls  # ensure HTTP was used

    cached_client = DeribitMarketDataClient(session=FailSession(), cache_dir=cache_dir)
    chains = cached_client.fetch_options_chain(expiries=["2024-05-24T08:00:00Z"], currency="BTC")
    assert len(chains) == 1
