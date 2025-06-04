#!/usr/bin/env python3
"""
BTC Volatility Smirk Trading Bot - Main Module

This is the main entry point for the BTC Volatility Smirk Trading Bot.
It initializes all agents and starts the trading process based on Bitcoin
options market data and volatility smirk analysis.

Usage:
    python main.py [--mode MODE] [--interval INTERVAL] [--symbol SYMBOL]

Options:
    --mode MODE         Trading mode: 'live', 'backtest', or 'paper' (default: 'paper')
    --interval INTERVAL Trading interval in seconds (default: 3600)
    --symbol SYMBOL     Trading symbol (default: 'BTC-USD' for Bitcoin)
"""

import os
import sys
import argparse
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

# Import agent interfaces
from agent_interfaces import (
    MarketData, SentimentResult, TradingSignal, 
    TradeExecution, Position, Portfolio, BacktestResult
)

# Import utility functions
from utils import get_data_directory, get_db_connection, setup_logger, load_config

# Import agent manager
from scripts.manager.agent_manager import AgentManager

# Set up logging
logger = setup_logger("main", os.path.join("logs", "main.log"))

def parse_arguments():
    """
    Parse command line arguments.
    
    Returns:
        argparse.Namespace: Parsed arguments.
    """
    parser = argparse.ArgumentParser(description="Agentic Trading Bot")
    parser.add_argument("--mode", choices=["live", "backtest", "paper"], default="paper",
                        help="Trading mode: 'live', 'backtest', or 'paper' (default: 'paper')")
    parser.add_argument("--interval", type=int, default=3600,
                        help="Trading interval in seconds (default: 3600)")
    parser.add_argument("--symbol", default="BTC-USD",
                        help="Trading symbol (default: 'BTC-USD' for Bitcoin)")
    parser.add_argument("--config", default="config.json",
                        help="Path to configuration file (default: 'config.json')")
    parser.add_argument("--backtest-start", default=None,
                        help="Start date for backtest (format: YYYY-MM-DD)")
    parser.add_argument("--backtest-end", default=None,
                        help="End date for backtest (format: YYYY-MM-DD)")
    
    return parser.parse_args()

def create_default_config(config_path: str) -> Dict[str, Any]:
    """
    Create default configuration file if it doesn't exist.
    
    Args:
        config_path (str): Path to configuration file.
        
    Returns:
        Dict[str, Any]: Configuration dictionary.
    """
    config = {
        "trading": {
            "mode": "paper",
            "interval": 3600,
            "symbol": "BTC-USD",
            "initial_balance": 100000.0,
            "max_open_trades": 10,
            "risk_per_trade": 0.05
        },
        "data_fetch": {
            "days": 365,
            "interval": "1h"
        },
        "sentiment": {
            "use_sentiment": True,
            "news_days": 7
        },
        "satellite": {
            "use_satellite": False,
            "locations": []
        },
        "strategy": {
            "use_ml": True,
            "use_sentiment": True,
            "use_satellite": False
        },
        "risk": {
            "max_position_size": 0.05,
            "max_portfolio_risk": 0.2,
            "stop_loss_percent": 0.02,
            "take_profit_percent": 0.05
        },
        "backtest": {
            "start_date": (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d"),
            "end_date": datetime.now().strftime("%Y-%m-%d")
        }
    }
    
    try:
        with open(config_path, "w") as f:
            json.dump(config, f, indent=4)
        logger.info(f"Created default configuration file at {config_path}")
    except Exception as e:
        logger.error(f"Error creating default configuration file: {e}")
    
    return config

def run_trading_bot(args):
    """
    Run the trading bot with the specified arguments.
    
    Args:
        args (argparse.Namespace): Command line arguments.
    """
    logger.info("Starting Agentic Trading Bot")
    
    # Load configuration
    config = load_config(args.config)
    if not config:
        logger.info("No configuration file found. Creating default configuration.")
        config = create_default_config(args.config)
    
    # Override configuration with command line arguments
    config["trading"]["mode"] = args.mode
    config["trading"]["interval"] = args.interval
    config["trading"]["symbol"] = args.symbol
    
    if args.backtest_start:
        config["backtest"]["start_date"] = args.backtest_start
    if args.backtest_end:
        config["backtest"]["end_date"] = args.backtest_end
    
    # Create data directory if it doesn't exist
    data_dir = get_data_directory()
    os.makedirs(data_dir, exist_ok=True)
    
    # Create logs directory if it doesn't exist
    logs_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
    os.makedirs(logs_dir, exist_ok=True)
    
    # Initialize agent manager
    manager = AgentManager(config)
    
    # Initialize agents
    manager.initialize_agents()
    
    # Run trading bot based on mode
    if args.mode == "backtest":
        logger.info("Running in backtest mode")
        
        # Parse backtest dates
        start_date = datetime.strptime(config["backtest"]["start_date"], "%Y-%m-%d")
        end_date = datetime.strptime(config["backtest"]["end_date"], "%Y-%m-%d")
        
        # Run backtest
        result = manager.run_backtest(start_date, end_date)
        
        # Print backtest results
        logger.info("Backtest Results:")
        logger.info(f"Start Date: {result.start_date}")
        logger.info(f"End Date: {result.end_date}")
        logger.info(f"Initial Capital: ${result.initial_capital:.2f}")
        logger.info(f"Final Capital: ${result.final_capital:.2f}")
        logger.info(f"Profit/Loss: ${result.profit_loss:.2f} ({result.profit_loss_percent:.2f}%)")
        logger.info(f"Total Trades: {result.total_trades}")
        logger.info(f"Winning Trades: {result.winning_trades}")
        logger.info(f"Losing Trades: {result.losing_trades}")
        logger.info(f"Win Rate: {result.win_rate:.2f}")
        logger.info(f"Sharpe Ratio: {result.sharpe_ratio:.2f}")
        logger.info(f"Max Drawdown: {result.max_drawdown:.2f}%")
    
    elif args.mode == "paper" or args.mode == "live":
        logger.info(f"Running in {args.mode} trading mode")
        
        # Start automated trading
        manager.start_automated_trading(interval=args.interval)
        
        try:
            # Keep the main thread alive
            while True:
                # Sleep for a short time to avoid high CPU usage
                import time
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Keyboard interrupt received. Stopping trading.")
            manager.stop_automated_trading()
    
    logger.info("Agentic Trading Bot execution completed")

def main():
    """
    Main function to run the Agentic Trading Bot.
    """
    # Parse command line arguments
    args = parse_arguments()
    
    # Run trading bot
    run_trading_bot(args)

if __name__ == "__main__":
    main()
