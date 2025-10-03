"""Modular strategy engine combining multiple alpha sources."""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Protocol

import numpy as np

logger = logging.getLogger(__name__)


class FeatureProvider(Protocol):
    """Protocol for feature provider plug-ins."""

    def compute(self) -> Dict[str, float]:
        ...


@dataclass
class StrategyConfig:
    risk_aversion: float = 0.5
    min_signal_strength: float = 0.1
    ensemble_weights: Dict[str, float] = field(default_factory=dict)


@dataclass
class StrategyEngine:
    """Combines feature providers and produces trading decisions."""

    providers: Dict[str, FeatureProvider]
    config: StrategyConfig = field(default_factory=StrategyConfig)

    def generate_signal(self) -> Dict[str, float]:
        logger.debug("Generating signal using providers: %s", list(self.providers))
        features: Dict[str, Dict[str, float]] = {}
        for name, provider in self.providers.items():
            try:
                features[name] = provider.compute()
            except Exception as exc:  # noqa: BLE001
                logger.exception("Feature provider %s failed: %s", name, exc)
                features[name] = {}
        combined = self._combine_features(features)
        scored = self._score_combined_features(combined)
        return {"signal": scored, "features": combined}

    def _combine_features(self, features: Dict[str, Dict[str, float]]) -> Dict[str, float]:
        weights = self.config.ensemble_weights or {name: 1.0 for name in features}
        aggregated: Dict[str, float] = {}
        for name, feature_set in features.items():
            weight = weights.get(name, 1.0)
            for key, value in feature_set.items():
                aggregated[key] = aggregated.get(key, 0.0) + weight * value
        return aggregated

    def _score_combined_features(self, combined: Dict[str, float]) -> float:
        values = np.array(list(combined.values()), dtype=float)
        if values.size == 0:
            return 0.0
        normalized = np.tanh(values)
        score = float(normalized.mean())
        adjusted = score * (1.0 - self.config.risk_aversion)
        if abs(adjusted) < self.config.min_signal_strength:
            return 0.0
        return adjusted


__all__ = ["StrategyEngine", "StrategyConfig", "FeatureProvider"]
