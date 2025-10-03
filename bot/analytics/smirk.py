"""Advanced volatility smirk analytics utilities."""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Dict, Iterable, List, Tuple

import numpy as np
import pandas as pd
from scipy.interpolate import griddata

logger = logging.getLogger(__name__)


@dataclass
class OptionRecord:
    instrument_name: str
    expiry: pd.Timestamp
    strike: float
    iv: float
    delta: float
    gamma: float


class SmirkAnalyzer:
    """Compute higher-order statistics for the volatility smirk."""

    def __init__(self, records: Iterable[Dict]) -> None:
        self.df = pd.DataFrame(list(records))
        if self.df.empty:
            logger.warning("SmirkAnalyzer initialised with no records")
            return
        for column in ("expiry",):
            if column in self.df:
                self.df[column] = pd.to_datetime(self.df[column])

    def surface_slice(self, expiry: pd.Timestamp) -> pd.DataFrame:
        """Return all instruments for the given expiry."""
        if self.df.empty:
            return self.df
        mask = self.df["expiry"] == pd.Timestamp(expiry)
        return self.df.loc[mask].sort_values("strike")

    def calculate_moments(self, expiry: pd.Timestamp) -> Dict[str, float]:
        """Calculate statistical moments of IV distribution for an expiry."""
        data = self.surface_slice(expiry)
        if data.empty:
            return {"mean": np.nan, "skew": np.nan, "kurtosis": np.nan}
        iv = data["iv"].astype(float)
        return {
            "mean": float(iv.mean()),
            "skew": float(iv.skew()),
            "kurtosis": float(iv.kurtosis()),
        }

    def fit_vol_surface(self) -> pd.DataFrame:
        """Fit a smooth surface of implied vol vs strike/tenor."""
        if self.df.empty:
            return self.df
        expiries = (self.df["expiry"] - self.df["expiry"].min()).dt.days.astype(float)
        strikes = self.df["strike"].astype(float)
        iv = self.df["iv"].astype(float)
        grid_x, grid_y = np.mgrid[strikes.min():strikes.max():100j, expiries.min():expiries.max():100j]
        surface = griddata((strikes, expiries), iv, (grid_x, grid_y), method="cubic")
        return pd.DataFrame({"strike": grid_x.flatten(), "tenor_days": grid_y.flatten(), "iv": surface.flatten()})

    def detect_regimes(self, window: int = 5) -> pd.DataFrame:
        """Detect IV regime changes based on rolling z-scores."""
        if self.df.empty:
            return self.df
        df = self.df.copy()
        df = df.sort_values(["expiry", "strike"])
        df["rolling_mean"] = df.groupby("expiry")["iv"].transform(lambda s: s.rolling(window, min_periods=1).mean())
        df["rolling_std"] = df.groupby("expiry")["iv"].transform(lambda s: s.rolling(window, min_periods=1).std())
        df["z_score"] = (df["iv"] - df["rolling_mean"]) / df["rolling_std"].replace(0, np.nan)
        df["regime"] = pd.cut(df["z_score"], bins=[-np.inf, -1.5, 1.5, np.inf], labels=["bearish", "neutral", "bullish"])
        return df


def compute_smirk_features(records: Iterable[Dict]) -> Dict[str, float]:
    """Convenience helper returning aggregated analytics for pipelines."""
    analyzer = SmirkAnalyzer(records)
    results: Dict[str, float] = {}
    for expiry in analyzer.df.get("expiry", pd.Series(dtype="datetime64[ns]")).unique():
        if pd.isna(expiry):
            continue
        moments = analyzer.calculate_moments(expiry)
        results[f"{pd.Timestamp(expiry).date()}_mean"] = moments["mean"]
        results[f"{pd.Timestamp(expiry).date()}_skew"] = moments["skew"]
        results[f"{pd.Timestamp(expiry).date()}_kurtosis"] = moments["kurtosis"]
    return results


__all__ = ["SmirkAnalyzer", "OptionRecord", "compute_smirk_features"]
