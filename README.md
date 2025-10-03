# BTC Volatility Smirk Trading Bot

## Overview

This project is a Python-based trading bot designed to trade Bitcoin (BTC) by analyzing the volatility smirk in the BTC options market. The volatility smirk—a pattern where implied volatility (IV) differs across strike prices for the same expiry—can provide insights into market sentiment and potential future price movements.

The bot aims to:
1.  Fetch BTC options market data (chain data including strike prices, IVs, volume, open interest, and greeks) and the current BTC spot price using the Deribit API.
2.  Analyze the fetched options data to identify and quantify the volatility smirk.
3.  Generate trading signals (BUY/SELL/HOLD BTC) based on the interpretation of the smirk.
4.  Execute trades through an exchange API (integration for execution is currently basic and records trades locally).

## Original Project

This project was originally a trading bot for WTI Crude Oil, using sentiment analysis from NewsAPI and DistilBERT. It has been repurposed and significantly refactored for BTC trading based on options data.

## Core Components

*   **Institutional Data Pipeline**: Deribit client (`bot/data`) with optional authentication, request throttling, and on-disk caching surfaced through the `MarketDataPipeline` facade.
*   **Volatility Smirk Analysis**: Research-grade analytics in `bot/analytics` capture skew, kurtosis, volatility surface fitting, and regime detection to inform trading signals.
*   **Strategy Engine**: Modular feature ensemble in `bot/strategy` combines multiple alpha sources with configurable risk aversion and explainable outputs.
*   **Risk & Portfolio Management**: `bot/risk` implements Kelly sizing, CVaR utilities, and Markdown risk reports for institutional-style governance.
*   **Execution & Simulation**: Execution adapters in `bot/execution` and walk-forward backtesting helpers in `bot/backtesting` provide both live and research workflows.
*   **Observability**: Lightweight metrics registry (`bot/observability`) and docs in `docs/` support operational visibility and interview-ready storytelling.

## Setup & Configuration

1.  **Clone the repository.**
2.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
3.  **Configuration:**
    *   Copy `config.example.json` to `config.json`.
    *   Update `config.json` with your settings:
        *   Set the appropriate trading symbol (e.g., "BTC-USD").
        *   Configure the `volatility_analysis` section, including the expiries you would like to monitor.
        *   Set up other trading parameters like mode (paper, live), risk parameters, etc.
4.  **Set API Keys:**
    *   Set `DERIBIT_CLIENT_ID` / `DERIBIT_CLIENT_SECRET` in your environment if you want to use authenticated Deribit endpoints. Public data works without credentials.

## Running the Bot

```bash
python main.py --mode paper --symbol BTC-USD
```

See `main.py --help` for more options.

## Disclaimer

This is a trading bot project. Trading financial markets involves significant risk. This software is provided "as is", without warranty of any kind. Use at your own risk. Ensure you understand the mechanisms and risks before deploying it with real capital. Paper trading is strongly recommended for testing.
