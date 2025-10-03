"""Utilities for fetching BTC options data from Deribit."""
from __future__ import annotations

import hashlib
import json
import logging
import os
import threading
import time
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence

import requests

from agent_interfaces import OptionsChainData, OptionsContractData

logger = logging.getLogger(__name__)


class DeribitAPIError(RuntimeError):
    """Raised when the Deribit API returns an error response."""


@dataclass
class _CacheEntry:
    payload: List[Dict[str, Any]]
    stored_at: float


class OnDiskCache:
    """Simple JSON cache with TTL semantics."""

    def __init__(self, cache_dir: Path, ttl: int) -> None:
        self._cache_dir = cache_dir
        self._ttl = ttl
        self._lock = threading.Lock()
        self._cache_dir.mkdir(parents=True, exist_ok=True)

    def _path_for(self, key: str) -> Path:
        digest = hashlib.sha1(key.encode("utf-8")).hexdigest()
        return self._cache_dir / f"{digest}.json"

    def load(self, key: str) -> Optional[_CacheEntry]:
        path = self._path_for(key)
        if not path.exists():
            return None
        try:
            with path.open("r", encoding="utf-8") as handle:
                raw = json.load(handle)
        except (OSError, json.JSONDecodeError):
            logger.warning("Failed to read cache file at %s", path)
            return None
        if time.time() - raw.get("stored_at", 0) > self._ttl:
            return None
        payload = raw.get("payload")
        if not isinstance(payload, list):
            return None
        return _CacheEntry(payload=payload, stored_at=raw["stored_at"])

    def store(self, key: str, payload: List[Dict[str, Any]]) -> None:
        path = self._path_for(key)
        envelope = {"stored_at": time.time(), "payload": payload}
        tmp_path = path.with_suffix(".tmp")
        with self._lock:
            try:
                with tmp_path.open("w", encoding="utf-8") as handle:
                    json.dump(envelope, handle)
                tmp_path.replace(path)
            except OSError:
                logger.warning("Failed to persist cache file at %s", path)


class DeribitMarketDataClient:
    """Client for Deribit's public market data endpoints."""

    BASE_URL = "https://www.deribit.com/api/v2"

    def __init__(
        self,
        *,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        cache_dir: Optional[Path] = None,
        cache_ttl: int = 300,
        rate_limit_per_sec: Optional[float] = 10.0,
        timeout: int = 10,
        session: Optional[requests.Session] = None,
    ) -> None:
        self.client_id = client_id or os.getenv("DERIBIT_CLIENT_ID")
        self.client_secret = client_secret or os.getenv("DERIBIT_CLIENT_SECRET")
        self._session = session or requests.Session()
        self._timeout = timeout
        self._rate_limit_per_sec = rate_limit_per_sec
        self._last_request_ts = 0.0
        cache_dir = cache_dir or Path(".cache") / "deribit"
        self._cache = OnDiskCache(cache_dir, cache_ttl)
        self._token: Optional[str] = None
        self._token_expiry: float = 0.0

    # ------------------------------------------------------------------
    # Public methods
    # ------------------------------------------------------------------
    def fetch_options_chain(
        self,
        *,
        expiries: Sequence[str],
        currency: str = "BTC",
        kind: str = "option",
        refresh: bool = False,
    ) -> List[OptionsChainData]:
        """Fetch option chain data for the requested expiries."""

        normalized_requests = self._normalize_expiries(expiries)
        cache_key = json.dumps(
            {
                "currency": currency,
                "kind": kind,
                "expiries": [dt.isoformat() for dt in normalized_requests],
            },
            sort_keys=True,
        )

        if not refresh:
            cached = self._cache.load(cache_key)
            if cached:
                logger.debug("Serving Deribit options chain from cache")
                return [self._parse_options_chain(item) for item in cached.payload]

        instruments = self._get_instruments(currency=currency, kind=kind)
        grouped = self._group_instruments_by_expiry(instruments)

        result: List[OptionsChainData] = []
        for requested_expiry in normalized_requests:
            bucket = self._select_instruments_for_expiry(grouped, requested_expiry)
            if not bucket:
                logger.warning("No Deribit instruments found for expiry %s", requested_expiry.date())
                continue
            contracts: List[OptionsContractData] = []
            spot_price: Optional[float] = None
            for instrument in sorted(bucket, key=lambda item: item["strike"]):
                summary = self._get_book_summary(instrument["instrument_name"])
                payload = summary[0] if summary else {}
                spot_price = payload.get("underlying_price") or spot_price
                contracts.append(
                    OptionsContractData(
                        strike_price=instrument["strike"],
                        contract_type=instrument["option_type"],
                        implied_volatility=payload.get("mark_iv"),
                        volume=payload.get("volume"),
                        open_interest=payload.get("open_interest"),
                        delta=payload.get("delta"),
                        gamma=payload.get("gamma"),
                        theta=payload.get("theta"),
                        vega=payload.get("vega"),
                        last_traded_price=payload.get("last_price"),
                    )
                )
            if not spot_price:
                spot_price = bucket[0].get("underlying_index_price") or 0.0
            chain = OptionsChainData(
                underlying_symbol=currency,
                spot_price=spot_price or 0.0,
                expiry_date=requested_expiry,
                contracts=contracts,
            )
            result.append(chain)

        if result:
            serialized = [self._to_serializable(chain) for chain in result]
            self._cache.store(cache_key, serialized)
        return result

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _normalize_expiries(self, expiries: Sequence[str]) -> List[datetime]:
        normalized: List[datetime] = []
        now = datetime.now(UTC)
        for expiry in expiries:
            expiry_dt: Optional[datetime] = None
            if isinstance(expiry, str):
                trimmed = expiry.strip()
                if trimmed.endswith(("D", "W", "M", "Y")) and trimmed[:-1].isdigit():
                    amount = int(trimmed[:-1])
                    unit = trimmed[-1].upper()
                    if unit == "D":
                        expiry_dt = now + timedelta(days=amount)
                    elif unit == "W":
                        expiry_dt = now + timedelta(weeks=amount)
                    elif unit == "M":
                        expiry_dt = now + timedelta(days=30 * amount)
                    elif unit == "Y":
                        expiry_dt = now + timedelta(days=365 * amount)
                else:
                    for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%S%z"):
                        try:
                            expiry_dt = datetime.strptime(trimmed, fmt)
                            break
                        except ValueError:
                            continue
            if expiry_dt is None:
                raise ValueError(f"Unsupported expiry format: {expiry}")
            if expiry_dt.tzinfo is None:
                expiry_dt = expiry_dt.replace(tzinfo=UTC)
            else:
                expiry_dt = expiry_dt.astimezone(UTC)
            normalized.append(expiry_dt)
        normalized.sort()
        return normalized

    def _group_instruments_by_expiry(self, instruments: Iterable[Dict[str, Any]]) -> Dict[datetime, List[Dict[str, Any]]]:
        grouped: Dict[datetime, List[Dict[str, Any]]] = {}
        for instrument in instruments:
            expiry_dt = datetime.fromtimestamp(instrument["expiration_timestamp"] / 1000, tz=UTC)
            grouped.setdefault(expiry_dt, []).append(instrument)
        return grouped

    def _select_instruments_for_expiry(
        self,
        grouped: Dict[datetime, List[Dict[str, Any]]],
        requested_expiry: datetime,
    ) -> List[Dict[str, Any]]:
        if requested_expiry in grouped:
            return grouped[requested_expiry]
        closest_expiry = min(
            grouped.keys(),
            key=lambda candidate: abs((candidate - requested_expiry).total_seconds()),
            default=None,
        )
        if closest_expiry is None:
            return []
        return grouped[closest_expiry]

    def _get_instruments(self, *, currency: str, kind: str) -> List[Dict[str, Any]]:
        params = {"currency": currency, "kind": kind, "expired": False}
        result = self._request("public/get_instruments", params=params, method="GET")
        if not isinstance(result, list):
            raise DeribitAPIError("Unexpected response for get_instruments")
        return result

    def _get_book_summary(self, instrument_name: str) -> List[Dict[str, Any]]:
        params = {"instrument_name": instrument_name}
        result = self._request("public/get_book_summary_by_instrument", params=params, method="GET")
        if not isinstance(result, list):
            raise DeribitAPIError("Unexpected response for get_book_summary_by_instrument")
        return result

    def _respect_rate_limit(self) -> None:
        if not self._rate_limit_per_sec:
            return
        min_interval = 1.0 / self._rate_limit_per_sec
        elapsed = time.time() - self._last_request_ts
        if elapsed < min_interval:
            time.sleep(min_interval - elapsed)
        self._last_request_ts = time.time()

    def _ensure_token(self) -> Optional[str]:
        if not self.client_id or not self.client_secret:
            return None
        if self._token and time.time() < self._token_expiry:
            return self._token
        payload = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "grant_type": "client_credentials",
        }
        response = self._request("public/auth", params=payload, method="GET", attach_auth=False)
        access_token = response.get("access_token")
        expires_in = response.get("expires_in", 0)
        if not access_token:
            raise DeribitAPIError("Authentication failed")
        self._token = access_token
        self._token_expiry = time.time() + max(expires_in - 60, 0)
        return self._token

    def _request(
        self,
        endpoint: str,
        *,
        params: Optional[Dict[str, Any]] = None,
        method: str = "GET",
        attach_auth: bool = True,
    ) -> Any:
        self._respect_rate_limit()
        url = f"{self.BASE_URL}/{endpoint}"
        request_kwargs: Dict[str, Any] = {"timeout": self._timeout}
        params = params or {}
        headers: Dict[str, str] = {}
        if endpoint.startswith("private/") and attach_auth:
            token = self._ensure_token()
            if not token:
                raise DeribitAPIError("Private endpoint requested without credentials")
            headers["Authorization"] = f"Bearer {token}"
        request_kwargs["headers"] = headers
        if method.upper() == "GET":
            request_kwargs["params"] = params
        else:
            request_kwargs["json"] = params
        response = self._session.request(method.upper(), url, **request_kwargs)
        response.raise_for_status()
        data = response.json()
        if "error" in data and data["error"]:
            raise DeribitAPIError(str(data["error"]))
        return data.get("result")

    def _to_serializable(self, chain: OptionsChainData) -> Dict[str, Any]:
        if hasattr(chain, "model_dump"):
            payload: Dict[str, Any] = chain.model_dump()
        else:  # pragma: no cover - exercised under pydantic v1
            payload = chain.dict()
        payload["expiry_date"] = chain.expiry_date.isoformat()
        serialized_contracts = []
        for contract in chain.contracts:
            if hasattr(contract, "model_dump"):
                contract_payload = contract.model_dump()
            else:  # pragma: no cover - exercised under pydantic v1
                contract_payload = contract.dict()
            serialized_contracts.append(contract_payload)
        payload["contracts"] = serialized_contracts
        return payload

    def _parse_options_chain(self, payload: Dict[str, Any]) -> OptionsChainData:
        parser = getattr(OptionsChainData, "model_validate", OptionsChainData.parse_obj)
        return parser(payload)


__all__ = ["DeribitMarketDataClient", "DeribitAPIError"]
