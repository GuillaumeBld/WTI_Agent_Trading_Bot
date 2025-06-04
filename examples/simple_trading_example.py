#!/usr/bin/env python3
"""
Simple Trading Example

This script demonstrates how to use the Agentic Trading Bot for a simple trading scenario.
It initializes the agent manager, fetches market data, analyzes sentiment, generates trading signals,
and executes trades.
"""

import os
import sys
import logging
from datetime import datetime, timedelta

# Add the parent directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import agent interfaces
from agent_interfaces import (
    MarketData, SentimentResult, TradingSignal, 
    TradeExecution, Position, Portfolio
)

# Import utility functions
from utils import get_data_directory, setup_logger

# Import agent manager
from scripts.manager.agent_manager import AgentManager

# Set up logging
logger = setup_logger("simple_trading_example", os.path.join("logs", "examples.log"))

def run_simple_trading_example():
    """
    Run a simple trading example.
    """
    logger.info("Starting Simple Trading Example")
    
    # Create a simple configuration
    config = {
        "trading": {
            "mode": "paper",
            "interval": 3600,
            "symbol": "CL=F",
            "initial_balance": 100000.0,
            "max_open_trades": 10,
            "risk_per_trade": 0.05
        },
        "data_fetch": {
            "days": 30,
            "interval": "1h"
        },
        "sentiment": {
            "use_sentiment": True,
            "news_days": 7
        },
        "strategy": {
            "use_ml": True,
            "use_sentiment": True,
            "use_satellite": False
        }
    }
    
    # Create data directory if it doesn't exist
    data_dir = get_data_directory()
    os.makedirs(data_dir, exist_ok=True)
    
    # Create logs directory if it doesn't exist
    logs_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs")
    os.makedirs(logs_dir, exist_ok=True)
    
    # Initialize agent manager
    manager = AgentManager(config)
    
    # Initialize agents
    manager.initialize_agents()
    
    # Fetch market or options data for the configured symbol
    logger.info("Fetching market data...")
    manager.fetch_data_for_symbol(
        symbol=config["trading"]["symbol"],
        days=config["data_fetch"]["days"],
    )
    logger.info("Market data fetch completed")
    
    # Analyze sentiment
    logger.info("Analyzing sentiment...")
    sentiment_results = manager.analyze_sentiment()
    logger.info(f"Generated {len(sentiment_results)} sentiment results")
    
    # Generate trading signals
    logger.info("Generating trading signals...")
    signals = manager.generate_trading_signals(use_sentiment=config["strategy"]["use_sentiment"])
    logger.info(f"Generated {len(signals)} trading signals")
    
    # Print the top 5 signals
    logger.info("Top 5 trading signals:")
    signals.sort(key=lambda x: x.confidence, reverse=True)
    for i, signal in enumerate(signals[:5]):
        signal_type = "BUY" if signal.signal == 1 else "SELL" if signal.signal == -1 else "HOLD"
        logger.info(f"{i+1}. {signal_type} signal for {config['trading']['symbol']} at ${signal.price:.2f} with confidence {signal.confidence:.2f}")
    
    # Execute trades
    logger.info("Executing trades...")
    executed_trades = manager.execute_trades(max_trades=1)
    logger.info(f"Executed {len(executed_trades)} trades")
    
    # Print executed trades
    for i, trade in enumerate(executed_trades):
        logger.info(f"Trade {i+1}: {trade.order_type} {trade.quantity} {trade.symbol} at ${trade.price:.2f}")
    
    # Display portfolio
    logger.info("Displaying portfolio...")
    if manager.execution_agent:
        manager.execution_agent.display_portfolio()
    
    logger.info("Simple Trading Example completed")

if __name__ == "__main__":
    run_simple_trading_example()
