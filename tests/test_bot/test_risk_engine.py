import numpy as np

from bot.risk.engine import RiskConfig, conditional_var, compute_risk_budget, kelly_position_size


def test_kelly_position_size_bounds():
    size = kelly_position_size(edge=0.1, win_prob=0.55, capital=100000)
    assert 0 <= size <= 100000


def test_conditional_var_handles_empty():
    assert conditional_var(np.array([])) == 0


def test_risk_budget_uses_config():
    config = RiskConfig(capital=50000)
    budget = compute_risk_budget(signal_strength=0.2, config=config)
    assert budget["allocation"] <= config.capital
    assert budget["max_loss"] == budget["allocation"] * config.max_drawdown
