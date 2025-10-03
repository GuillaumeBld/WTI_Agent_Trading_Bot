import pandas as pd
import pytest

from bot.analytics.smirk import SmirkAnalyzer, compute_smirk_features


def sample_records():
    return [
        {"instrument_name": "BTC-30JUN23-30000-C", "expiry": "2023-06-30", "strike": 30000, "iv": 0.5, "delta": 0.4, "gamma": 0.1},
        {"instrument_name": "BTC-30JUN23-32000-C", "expiry": "2023-06-30", "strike": 32000, "iv": 0.55, "delta": 0.35, "gamma": 0.09},
        {"instrument_name": "BTC-30JUN23-34000-C", "expiry": "2023-06-30", "strike": 34000, "iv": 0.6, "delta": 0.3, "gamma": 0.08},
    ]


def test_moments_are_computed():
    analyzer = SmirkAnalyzer(sample_records())
    expiry = pd.Timestamp("2023-06-30")
    moments = analyzer.calculate_moments(expiry)
    assert moments["mean"] > 0
    assert moments["skew"] == pytest.approx(0, abs=1)


def test_feature_helper_returns_values():
    features = compute_smirk_features(sample_records())
    assert any(key.endswith("_mean") for key in features)
