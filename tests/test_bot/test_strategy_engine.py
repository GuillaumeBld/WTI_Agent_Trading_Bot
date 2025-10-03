from dataclasses import dataclass
from typing import Dict

from bot.strategy.engine import StrategyConfig, StrategyEngine


@dataclass
class DummyProvider:
    value: float

    def compute(self) -> Dict[str, float]:
        return {"alpha": self.value}


def test_engine_combines_providers():
    engine = StrategyEngine(
        providers={"smirk": DummyProvider(0.3), "macro": DummyProvider(-0.1)},
        config=StrategyConfig(risk_aversion=0.2, min_signal_strength=0.0),
    )
    result = engine.generate_signal()
    assert "signal" in result
    assert isinstance(result["signal"], float)
    assert result["features"]["alpha"] != 0


def test_signal_is_zero_when_below_threshold():
    engine = StrategyEngine(
        providers={"smirk": DummyProvider(0.01)},
        config=StrategyConfig(risk_aversion=0.0, min_signal_strength=0.5),
    )
    result = engine.generate_signal()
    assert result["signal"] == 0
