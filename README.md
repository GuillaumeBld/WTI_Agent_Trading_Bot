# BTC Volatility Smirk Trading Bot

## Overview

This project is a Python-based trading bot designed to trade Bitcoin (BTC) by analyzing the volatility smirk in the BTC options market. The volatility smirk—a pattern where implied volatility (IV) differs across strike prices for the same expiry—can provide insights into market sentiment and potential future price movements.

The bot aims to:
1.  Fetch BTC options market data (chain data including strike prices, IVs, volume, open interest, and greeks) and the current BTC spot price, intended for use with data providers like Refinitiv API.
2.  Analyze the fetched options data to identify and quantify the volatility smirk.
3.  Generate trading signals (BUY/SELL/HOLD BTC) based on the interpretation of the smirk.
4.  Execute trades through an exchange API (integration for execution is currently basic and records trades locally).

## Original Project

This project was originally a trading bot for WTI Crude Oil, using sentiment analysis from NewsAPI and DistilBERT. It has been repurposed and significantly refactored for BTC trading based on options data.

## Core Components

*   **Data Fetching**: Scripts to obtain options chain data for BTC. Currently uses a mock data generator but is designed for integration with APIs like Refinitiv.
*   **Volatility Smirk Analysis**: Modules to calculate and interpret the volatility smirk from the options data.
*   **Strategy**: Implements trading logic based on signals derived from the smirk analysis.
*   **Agent Manager**: Orchestrates the various components of the bot.
*   **Trade Execution**: Basic module for recording trades (not fully integrated with live exchanges).

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
        *   Configure the `volatility_analysis` section, including your API key environment variable name for the options data provider (e.g., Refinitiv) and the API endpoint.
        *   Set up other trading parameters like mode (paper, live), risk parameters, etc.
4.  **Set API Keys:**
    *   Ensure the environment variable for your options data API key (e.g., `REFINITIV_API_KEY`) is set in your environment.

## Running the Bot

```bash
python main.py --mode paper --symbol BTC-USD
```

See `main.py --help` for more options.

## Disclaimer

This is a trading bot project. Trading financial markets involves significant risk. This software is provided "as is", without warranty of any kind. Use at your own risk. Ensure you understand the mechanisms and risks before deploying it with real capital. Paper trading is strongly recommended for testing.
