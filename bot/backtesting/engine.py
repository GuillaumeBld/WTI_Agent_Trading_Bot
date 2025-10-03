"""Lightweight walk-forward backtesting utilities."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Callable, Iterable, List

import numpy as np
import pandas as pd


@dataclass
class BacktestWindow:
    start: datetime
    end: datetime


def walk_forward_windows(history: pd.DataFrame, train_days: int, test_days: int) -> List[BacktestWindow]:
    windows: List[BacktestWindow] = []
    current_start = history.index.min()
    while current_start + pd.Timedelta(days=train_days + test_days) <= history.index.max():
        train_end = current_start + pd.Timedelta(days=train_days)
        test_end = train_end + pd.Timedelta(days=test_days)
        windows.append(BacktestWindow(start=current_start.to_pydatetime(), end=test_end.to_pydatetime()))
        current_start += pd.Timedelta(days=test_days)
    return windows


def evaluate_strategy(history: pd.DataFrame, signal_fn: Callable[[pd.Series], float]) -> pd.DataFrame:
    equity_curve = [1.0]
    returns = []
    for _, row in history.iterrows():
        signal = signal_fn(row)
        daily_return = signal * row.get("return", 0.0)
        returns.append(daily_return)
        equity_curve.append(equity_curve[-1] * (1 + daily_return))
    return pd.DataFrame({"equity": equity_curve[1:], "return": returns}, index=history.index)


def performance_summary(equity: pd.Series) -> dict:
    total_return = equity.iloc[-1] - 1
    drawdowns = equity / equity.cummax() - 1
    sharpe = (equity.pct_change().mean() / (equity.pct_change().std() + 1e-9)) * np.sqrt(252)
    return {
        "total_return": float(total_return),
        "max_drawdown": float(drawdowns.min()),
        "sharpe": float(sharpe),
    }


__all__ = ["BacktestWindow", "walk_forward_windows", "evaluate_strategy", "performance_summary"]
