"""Lightweight metrics registry for the trading bot."""
from __future__ import annotations

import logging
from collections import defaultdict
from contextlib import contextmanager
from dataclasses import dataclass
from time import perf_counter
from typing import Dict, Iterator

logger = logging.getLogger(__name__)


@dataclass
class MetricsRegistry:
    counters: Dict[str, float]
    gauges: Dict[str, float]
    histograms: Dict[str, list[float]]

    @classmethod
    def create(cls) -> "MetricsRegistry":
        return cls(defaultdict(float), defaultdict(float), defaultdict(list))

    def inc(self, name: str, value: float = 1.0) -> None:
        self.counters[name] += value

    def gauge(self, name: str, value: float) -> None:
        self.gauges[name] = value

    @contextmanager
    def time(self, name: str) -> Iterator[None]:
        start = perf_counter()
        try:
            yield
        finally:
            elapsed = perf_counter() - start
            self.histograms[name].append(elapsed)
            logger.debug("Metric %s recorded %.4fs", name, elapsed)

    def snapshot(self) -> Dict[str, Dict[str, float]]:
        hist = {k: sum(v) / len(v) if v else 0.0 for k, v in self.histograms.items()}
        return {"counters": dict(self.counters), "gauges": dict(self.gauges), "timers": hist}


__all__ = ["MetricsRegistry"]
