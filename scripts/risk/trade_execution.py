#!/usr/bin/env python3
"""
Investment Tracker

This module allows you to manually input the details of executed trades.
It updates the portfolio (account balance and open positions) and records
the trades in an SQLite database.

New Features:
  - Position Sizing: Automatically calculates the number of shares to buy
    based on a fixed risk per trade (e.g., 5% of current balance).
  - Max Open Trades Check: Prevents opening new trades if the number of open
    trades equals or exceeds the maximum allowed.
  - Each trade is recorded with a note column for additional comments.
"""

import os
import sqlite3
import time
import json
from datetime import datetime
from typing import List, Dict, Any, Optional, Union

# Import the interfaces
from agent_interfaces import TradeExecution, Position, Portfolio
# Import utility functions
from utils import get_data_directory, get_db_connection, setup_logger

# -----------------------------
# Global Constants & Configuration
# -----------------------------
INITIAL_BALANCE = 100000.0  # Starting account balance
MAX_OPEN_TRADES = 10        # Maximum number of open trades allowed
RISK_PER_TRADE = 0.05       # Risk 5% of current balance per trade
TRADING_CHECK_INTERVAL = 3600  # Check for new trades every hour (in seconds)

# Set up logging using the utility function
logger = setup_logger("trade_execution", os.path.join("logs", "trade_execution.log"))

# -----------------------------
# Database Initialization
# -----------------------------
def initialize_database(db_path: str):
    """
    Ensure that the trade_history table exists with the required columns.
    
    Args:
        db_path (str): Path to the SQLite database.
    """
    try:
        conn = get_db_connection(db_path)
        if conn is None:
            return
            
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS trade_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                execution_time TEXT,
                symbol TEXT,
                trade_type TEXT,
                executed_price REAL,
                quantity REAL,
                limit_price REAL,
                status TEXT,
                execution_id TEXT,
                note TEXT
            )
        """)
        conn.commit()
        conn.close()
        logger.info("Database initialized.")
    except Exception as e:
        logger.error(f"Error initializing database: {e}")

def record_trade(trade: TradeExecution, note: str = "", db_path: Optional[str] = None) -> Optional[int]:
    """
    Record a trade in the trade_history table including all execution parameters.
    
    Args:
        trade (TradeExecution): Trade execution details.
        note (str, optional): Additional notes about the trade.
        db_path (str, optional): Path to the SQLite database. If None, uses the default path.
        
    Returns:
        Optional[int]: ID of the inserted record, or None if insertion failed.
    """
    if db_path is None:
        db_path = os.path.join(get_data_directory(), "market_data.db")
        
    try:
        conn = get_db_connection(db_path)
        if conn is None:
            return None
            
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO trade_history (
                execution_time, symbol, trade_type, executed_price, quantity, 
                limit_price, status, execution_id, note
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            trade.date.isoformat(),
            trade.symbol,
            trade.order_type,
            trade.price,
            trade.quantity,
            trade.limit_price,
            trade.status,
            trade.execution_id,
            note
        ))
        conn.commit()
        trade_id = cursor.lastrowid
        conn.close()
        
        logger.info(f"Successfully recorded trade: {trade.order_type} order for {trade.symbol}")
        return trade_id
    except Exception as e:
        logger.error(f"Error recording trade: {e}")
        return None

def count_open_trades(db_path: Optional[str] = None) -> int:
    """
    Count the number of open trades recorded in the trade_history.
    For this simple tracker, we assume a BUY trade adds an open trade and a SELL clears all.
    
    Args:
        db_path (str, optional): Path to the SQLite database. If None, uses the default path.
        
    Returns:
        int: Number of open trades.
    """
    if db_path is None:
        db_path = os.path.join(get_data_directory(), "market_data.db")
        
    try:
        conn = get_db_connection(db_path)
        if conn is None:
            return 0
            
        cursor = conn.cursor()
        # Count trades with status "EXECUTED" and trade_type "BUY"
        cursor.execute("""
            SELECT COUNT(*) FROM trade_history 
            WHERE status = 'EXECUTED' AND trade_type = 'BUY'
        """)
        buy_count = cursor.fetchone()[0]
        
        # Count trades with status "EXECUTED" and trade_type "SELL"
        cursor.execute("""
            SELECT COUNT(*) FROM trade_history 
            WHERE status = 'EXECUTED' AND trade_type = 'SELL'
        """)
        sell_count = cursor.fetchone()[0]
        
        conn.close()
        
        # Assuming each SELL closes one BUY
        open_trades = max(0, buy_count - sell_count)
        logger.info(f"Open trades count: {open_trades}")
        return open_trades
    except Exception as e:
        logger.error(f"Error counting open trades: {e}")
        return 0

# -----------------------------
# Investment Tracker Logic
# -----------------------------
class InvestmentTracker:
    def __init__(self, initial_balance: float = INITIAL_BALANCE):
        self.balance = initial_balance
        self.open_trades: List[Position] = []  # List to track open positions
        self.db_path = os.path.join(get_data_directory(), "market_data.db")
        
        # Initialize database
        initialize_database(self.db_path)

    def get_portfolio(self) -> Portfolio:
        """
        Get the current portfolio.
        
        Returns:
            Portfolio: Portfolio object with current balance and positions.
        """
        return Portfolio(
            date=datetime.now(),
            cash=self.balance,
            positions=self.open_trades
        )

    def display_portfolio(self):
        """Log portfolio status."""
        portfolio = self.get_portfolio()
        logger.info(f"Current Account Balance: ${portfolio.cash:.2f}")
        if portfolio.positions:
            logger.info("Open Positions:")
            for position in portfolio.positions:
                logger.info(f"  Symbol: {position.symbol} | Quantity: {position.quantity} | Entry Price: ${position.entry_price:.2f} | Current Price: ${position.current_price:.2f}")
                logger.info(f"  Market Value: ${position.market_value:.2f} | P/L: ${position.profit_loss:.2f} ({position.profit_loss_percent:.2f}%)")
        else:
            logger.info("No open positions.")
        logger.info(f"Total Portfolio Value: ${portfolio.total_value:.2f}")
        logger.info(f"Total P/L: ${portfolio.total_profit_loss:.2f}")

    def process_telegram_signals(self):
        """Process incoming Telegram signals for automated trading."""
        # This method would integrate with your Telegram bot to receive and process signals
        # For now, it's a placeholder that just logs the current portfolio
        self.display_portfolio()

    def process_trade(self, symbol: str = "BTC-USD"):
        """
        Manually input trade details with position sizing and max open trades check.
        For BUY trades, the trade size is automatically calculated as RISK_PER_TRADE * current balance.
        
        Args:
            symbol (str, optional): Symbol to trade. Defaults to "BTC-USD".
        """
        trade_type = input("Enter trade type (BUY/SELL): ").strip().upper()
        if trade_type not in ["BUY", "SELL"]:
            print("Invalid trade type. Must be BUY or SELL.")
            return

        # Check if we already have maximum open trades for BUY orders.
        if trade_type == "BUY" and len(self.open_trades) >= MAX_OPEN_TRADES:
            print(f"Maximum open trades reached ({MAX_OPEN_TRADES}). Cannot open new BUY trade.")
            return

        # For position sizing, for BUY trades, automatically determine the amount to invest:
        if trade_type == "BUY":
            # Calculate trade amount as a fixed percentage of the current balance
            trade_amount = self.balance * RISK_PER_TRADE
            print(f"Calculated trade amount based on {RISK_PER_TRADE*100:.1f}% of balance: ${trade_amount:.2f}")
            try:
                # Ask the user to confirm the executed price
                executed_price = float(input("Enter executed price: ").strip())
            except ValueError:
                print("Invalid price entered.")
                return
            # Calculate the number of shares automatically
            quantity = trade_amount / executed_price
            cost = executed_price * quantity
            note = input("Enter any note for this trade (optional): ").strip()
            
            # Deduct cost from balance
            if cost > self.balance:
                print("Insufficient funds for this trade (should not happen with position sizing).")
                return
            self.balance -= cost
            
            # Create a Position object
            position = Position(
                symbol=symbol,
                quantity=quantity,
                entry_price=executed_price,
                current_price=executed_price
            )
            self.open_trades.append(position)
            
            # Create a TradeExecution object
            trade = TradeExecution(
                date=datetime.now(),
                symbol=symbol,
                order_type=trade_type,
                quantity=quantity,
                price=executed_price,
                status="EXECUTED"
            )
            
            # Record the trade in the database
            record_trade(trade, note, self.db_path)
            print(f"Trade executed: {trade_type} {quantity:.2f} shares of {symbol} at ${executed_price:.2f} costing ${cost:.2f}.")
            print(f"Updated balance: ${self.balance:.2f}")
        else:  # For SELL trades, user inputs the details manually
            try:
                executed_price = float(input("Enter executed price for SELL: ").strip())
                quantity = float(input("Enter number of shares to SELL: ").strip())
            except ValueError:
                print("Invalid number entered.")
                return
            revenue = executed_price * quantity
            note = input("Enter any note for this trade (optional): ").strip()
            
            # Add revenue to balance
            self.balance += revenue
            
            # Create a TradeExecution object
            trade = TradeExecution(
                date=datetime.now(),
                symbol=symbol,
                order_type=trade_type,
                quantity=quantity,
                price=executed_price,
                status="EXECUTED"
            )
            
            # For simplicity, assume SELL clears all open trades
            self.open_trades = []
            
            # Record the trade in the database
            record_trade(trade, note, self.db_path)
            print(f"Trade executed: {trade_type} {quantity} shares of {symbol} at ${executed_price:.2f} generating ${revenue:.2f}.")
            print(f"Updated balance: ${self.balance:.2f}")

def run_automated_trading():
    """Run the trading system in automated mode, listening for Telegram signals."""
    tracker = InvestmentTracker()
    logger.info("Starting automated trading system...")
    
    while True:
        try:
            # Check for new Telegram signals and process trades
            tracker.process_telegram_signals()
            
            # Sleep for the configured interval before checking again
            time.sleep(TRADING_CHECK_INTERVAL)
            
        except KeyboardInterrupt:
            logger.info("Shutting down automated trading system...")
            break
        except Exception as e:
            logger.error(f"Error in automated trading loop: {e}")
            time.sleep(10)  # Wait before retrying after an error

if __name__ == "__main__":
    run_automated_trading()
