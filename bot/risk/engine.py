"""Portfolio risk management utilities."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

import numpy as np


@dataclass
class RiskConfig:
    capital: float
    confidence_level: float = 0.95
    max_drawdown: float = 0.2


def kelly_position_size(edge: float, win_prob: float, capital: float) -> float:
    """Compute the Kelly fraction for position sizing."""
    if win_prob in {0, 1}:
        return 0.0
    b = edge / (1 - win_prob)
    fraction = (win_prob * (b + 1) - 1) / b if b != 0 else 0.0
    return max(0.0, min(fraction, 1.0)) * capital


def conditional_var(returns: np.ndarray, confidence_level: float = 0.95) -> float:
    """Calculate conditional value at risk (CVaR)."""
    if returns.size == 0:
        return 0.0
    sorted_returns = np.sort(returns)
    index = int((1 - confidence_level) * len(sorted_returns))
    tail = sorted_returns[: max(index, 1)]
    return float(tail.mean())


def compute_risk_budget(signal_strength: float, config: RiskConfig) -> Dict[str, float]:
    """Determine position sizing and expected loss budget."""
    edge = max(signal_strength, 0)
    win_prob = 0.5 + edge / 2
    allocation = kelly_position_size(edge=edge, win_prob=win_prob, capital=config.capital)
    return {
        "allocation": allocation,
        "max_loss": allocation * config.max_drawdown,
    }


__all__ = ["RiskConfig", "kelly_position_size", "conditional_var", "compute_risk_budget"]
