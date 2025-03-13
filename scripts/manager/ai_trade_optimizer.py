#!/usr/bin/env python3
"""
AI Trade Optimizer

This module analyzes historical trade data from the trade_history table,
calculates performance metrics (win rate, average slippage, max drawdown),
and outputs optimized execution parameters such as stop-loss, take-profit,
position sizing multiplier, and recommended order type.
"""

import os
import sqlite3
import numpy as np
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Define the database path (assumed to be in the "data" folder)
DB_PATH = os.path.join("data", "market_data.db")

def load_trade_history(db_path=DB_PATH):
    """
    Load historical trade data from the trade_history table.
    Returns a list of tuples containing (execution_time, trade_type, executed_price, note).
    """
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT execution_time, trade_type, executed_price, note FROM trade_history")
        trades = cursor.fetchall()
        conn.close()
        logging.info(f"Loaded {len(trades)} trades from history.")
        return trades
    except Exception as e:
        logging.error(f"Error loading trade history: {e}")
        return []

def calculate_performance_metrics(trades):
    """
    Calculate performance metrics based on historical trades.
    Returns a dictionary with:
      - win_rate: Percentage of winning trades.
      - avg_slippage: Average slippage (dummy value for demonstration).
      - max_drawdown: Maximum drawdown (dummy value for demonstration).
    """
    wins = 0
    losses = 0
    for trade in trades:
        note = trade[3].lower() if trade[3] else ""
        if "win" in note:
            wins += 1
        elif "loss" in note:
            losses += 1
    total = wins + losses if (wins + losses) > 0 else 1
    win_rate = wins / total * 100
    avg_slippage = 0.01  # Dummy value; replace with actual calculation if available
    max_drawdown = 0.05  # Dummy value; replace with actual calculation if available
    logging.info(f"Performance Metrics: Win Rate = {win_rate:.2f}%, Avg Slippage = {avg_slippage}, Max Drawdown = {max_drawdown}")
    return {
        "win_rate": win_rate,
        "avg_slippage": avg_slippage,
        "max_drawdown": max_drawdown
    }

def optimize_execution_parameters(metrics):
    """
    Optimize execution parameters based on performance metrics.
    Adjusts stop-loss, take-profit, and position sizing multiplier.
    """
    base_stop_loss = 0.02  # Base stop loss: 2%
    base_take_profit = 0.05  # Base take profit: 5%
    
    if metrics["win_rate"] > 60:
        optimized_stop_loss = base_stop_loss * 1.1
        optimized_take_profit = base_take_profit * 0.9
    elif metrics["win_rate"] < 40:
        optimized_stop_loss = base_stop_loss * 0.9
        optimized_take_profit = base_take_profit * 1.1
    else:
        optimized_stop_loss = base_stop_loss
        optimized_take_profit = base_take_profit
    
    # Adjust position sizing: if win rate is below 50, reduce position size.
    position_multiplier = 1.0 if metrics["win_rate"] >= 50 else 0.8
    order_type = "MKT"  # Default order type; could be optimized further.
    
    optimized_params = {
        "stop_loss": optimized_stop_loss,
        "take_profit": optimized_take_profit,
        "position_multiplier": position_multiplier,
        "order_type": order_type
    }
    
    logging.info("Optimized Execution Parameters:")
    for key, value in optimized_params.items():
        logging.info(f"{key}: {value}")
    
    return optimized_params

def run_optimizer(db_path=DB_PATH):
    """
    Run the optimizer by loading historical trade data, calculating performance metrics,
    and generating optimized execution parameters.
    """
    trades = load_trade_history(db_path)
    metrics = calculate_performance_metrics(trades)
    optimized_params = optimize_execution_parameters(metrics)
    return optimized_params

def main():
    optimized = run_optimizer()
    print("Optimized Execution Parameters:")
    for key, value in optimized.items():
        print(f"{key}: {value}")

if __name__ == "__main__":
    main()