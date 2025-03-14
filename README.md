# Agentic Trading Bot

An advanced trading bot system that uses multiple specialized agents to analyze market data, sentiment, satellite imagery, and execute trades for WTI Crude Oil.

## Overview

The Agentic Trading Bot is a sophisticated trading system that leverages multiple specialized agents to make informed trading decisions. Each agent is responsible for a specific aspect of the trading process, such as data fetching, sentiment analysis, technical analysis, strategy formulation, risk management, and trade execution.

The system is designed to be modular, extensible, and configurable, allowing for easy customization and enhancement.

## Architecture

The system is composed of the following components:

### Agent Interfaces

The `agent_interfaces.py` file defines the interfaces for each agent using Pydantic models. These interfaces ensure that data is properly structured and validated as it flows between agents.

### Utility Functions

The `utils.py` file contains common utility functions used throughout the system, such as logging, configuration loading, and database connections.

### Agents

1. **Data Fetching Agent**: Fetches market data from various sources.
2. **Sentiment Analysis Agent**: Analyzes news sentiment to gauge market sentiment.
3. **Technical Analysis Agent**: Calculates technical indicators for market analysis.
4. **Satellite Data Agent**: Analyzes satellite imagery for oil storage and shipping insights.
5. **Strategy Agent**: Generates trading signals based on market data and analysis.
6. **Risk Management Agent**: Manages risk and position sizing.
7. **Trade Execution Agent**: Executes trades based on trading signals.

### Agent Manager

The `agent_manager.py` file coordinates the different agents, manages data flow between them, and handles the overall trading process.

## Features

- **Multi-Agent Architecture**: Each agent specializes in a specific aspect of the trading process.
- **Sentiment Analysis**: Analyzes news sentiment to gauge market sentiment.
- **Technical Analysis**: Calculates technical indicators for market analysis.
- **Satellite Data Analysis**: Analyzes satellite imagery for oil storage and shipping insights.
- **Machine Learning**: Uses machine learning for signal generation.
- **Risk Management**: Manages risk and position sizing.
- **Backtesting**: Allows for backtesting of trading strategies.
- **Paper Trading**: Allows for paper trading to test strategies without real money.
- **Live Trading**: Supports live trading with real money.
- **Error Handling**: Robust error handling with retry mechanisms for network operations.
- **Docker Support**: Easy deployment with Docker and docker-compose.
- **Portable File Paths**: Uses relative paths for better portability across environments.

## Installation

### Standard Installation

1. Clone the repository:
```bash
git clone https://github.com/GuillaumeBld/WTI_Agent_Trading_Bot.git
cd WTI_Agent_Trading_Bot
```

2. Install the required dependencies:
```bash
pip install -r requirements.txt
```

3. Set up the configuration file:
```bash
cp config.example.json config.json
```

4. Edit the configuration file to suit your needs.

### Docker Installation

1. Clone the repository:
```bash
git clone https://github.com/GuillaumeBld/WTI_Agent_Trading_Bot.git
cd WTI_Agent_Trading_Bot
```

2. Set up the configuration file:
```bash
cp config.example.json config.json
```

3. Edit the configuration file to suit your needs.

4. Build and run with Docker Compose:
```bash
docker-compose up --build trading-bot
```

## Usage

### Running the Bot

To run the bot, use the following command:

```bash
python main.py [--mode MODE] [--interval INTERVAL] [--symbol SYMBOL]
```

Options:
- `--mode MODE`: Trading mode: 'live', 'backtest', or 'paper' (default: 'paper')
- `--interval INTERVAL`: Trading interval in seconds (default: 3600)
- `--symbol SYMBOL`: Trading symbol (default: 'CL=F' for WTI Crude Oil)
- `--config CONFIG`: Path to configuration file (default: 'config.json')
- `--backtest-start START_DATE`: Start date for backtest (format: YYYY-MM-DD)
- `--backtest-end END_DATE`: End date for backtest (format: YYYY-MM-DD)

### Examples

Run in paper trading mode:
```bash
python main.py --mode paper
```

Run in backtest mode:
```bash
python main.py --mode backtest --backtest-start 2023-01-01 --backtest-end 2023-12-31
```

Run in live trading mode:
```bash
python main.py --mode live --interval 1800 --symbol CL=F
```

## Configuration

The configuration file (`config.json`) allows you to customize various aspects of the trading bot:

```json
{
    "trading": {
        "mode": "paper",
        "interval": 3600,
        "symbol": "CL=F",
        "initial_balance": 100000.0,
        "max_open_trades": 10,
        "risk_per_trade": 0.05
    },
    "data_fetch": {
        "days": 365,
        "interval": "1h"
    },
    "sentiment": {
        "use_sentiment": true,
        "news_days": 7
    },
    "satellite": {
        "use_satellite": true,
        "locations": [
            "cushing_oklahoma",
            "strait_of_hormuz",
            "houston_ship_channel",
            "saudi_aramco_abqaiq"
        ]
    },
    "strategy": {
        "use_ml": true,
        "use_sentiment": true,
        "use_satellite": true
    },
    "risk": {
        "max_position_size": 0.05,
        "max_portfolio_risk": 0.2,
        "stop_loss_percent": 0.02,
        "take_profit_percent": 0.05
    },
    "backtest": {
        "start_date": "2023-01-01",
        "end_date": "2023-12-31"
    }
}
```

## Directory Structure

```
agentic-trading-bot/
├── agent_interfaces.py     # Interfaces for each agent
├── utils.py                # Common utility functions
├── main.py                 # Main entry point
├── config.json             # Configuration file
├── data/                   # Data directory
├── logs/                   # Logs directory
└── scripts/                # Agent scripts
    ├── data_fetch/         # Data fetching agent
    ├── sentiment/          # Sentiment analysis agent
    ├── indicators/         # Technical analysis agent
    ├── satellite/          # Satellite data agent
    ├── strategy/           # Strategy agent
    ├── risk/               # Risk management agent
    └── manager/            # Agent manager
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Disclaimer

This software is for educational purposes only. Do not use it to trade with real money without understanding the risks involved. The authors are not responsible for any financial losses incurred from using this software.
# WTI_Agent_Trading_Bot
