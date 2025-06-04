#!/usr/bin/env python3
"""
Trade Execution Module - Enhanced Version

This module loads trading signals from a SQLite database, dynamically calculates
risk parameters (stop-loss and take-profit levels) based on ATR and sentiment adjustments,
determines position sizing based on account balance and risk exposure,
checks for duplicate trades, and executes trades by recording them in the trade_history table.
It also sends alerts via Telegram with robust retry logic.
"""

import os
import sqlite3
import argparse
import requests
import time
import json
from datetime import datetime, timedelta, timezone
import logging
import joblib
import numpy as np
import yfinance as yf
from tenacity import retry, stop_after_attempt, wait_fixed

# -----------------------------
# Global Constants & Configuration
# -----------------------------
RETRY_COUNT = 3
RETRY_DELAY = 5  # seconds
DUPLICATE_WINDOW_HOURS = 1  # Filter duplicates if a similar trade is executed within 1 hour

# For demonstration, we use a fixed account balance.
# In a production system this would be dynamically updated.
ACCOUNT_BALANCE = 100000.0

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Database path (assumed to be in the "data" folder)
DB_PATH = os.path.join("data", "market_data.db")

# -----------------------------
# ATR Calculation with Retry
# -----------------------------
@retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
def fetch_btc_atr():
    """
    Fetch the Average True Range (ATR) for BTC using 30 days of Yahoo Finance data.
    Uses a rolling window equal to the minimum of 14 or the number of valid rows.
    If the ATR calculation results in NaN, a default ATR value of 1.0 is returned.
    """
    try:
        ticker = yf.Ticker("BTC-USD")
        data = ticker.history(period="30d")
        print("Fetched data for ATR calculation:")
        print(f"Data shape: {data.shape}")
        print(f"Columns: {data.columns.tolist()}")
        print("First 5 rows:\n", data.head())
        print("NaN counts:\n", data.isna().sum())
        
        if data.empty or 'High' not in data.columns or 'Low' not in data.columns:
            logging.error("No data or missing columns from Yahoo Finance for ATR calculation.")
            return 1.0  # default value

        data = data.dropna(subset=['High', 'Low'])
        print(f"Data shape after dropping NaNs: {data.shape}")
        if data.empty:
            logging.error("Data became empty after dropping NaNs from High/Low.")
            return 1.0
        
        true_range = data["High"] - data["Low"]
        window_size = min(14, len(data))
        atr = true_range.rolling(window=window_size).mean().iloc[-1]
        if np.isnan(atr):
            logging.error("ATR calculation resulted in NaN. Using default ATR value of 1.0.")
            return 1.0
        logging.info(f"Fetched BTC ATR: {atr:.2f}")
        return atr
    except Exception as e:
        logging.error(f"Error fetching BTC ATR: {e}")
        return 1.0

# -----------------------------
# Sentiment Adjustment Calculation
# -----------------------------
def fetch_sentiment_adjustment(db_path=DB_PATH):
    """
    Fetch the latest sentiment score from the sentiment_analysis table and calculate its adjustment.
    The adjustment is capped between -5% and +5%.
    """
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT sentiment_score FROM sentiment_analysis ORDER BY timestamp DESC LIMIT 1")
        row = cursor.fetchone()
        conn.close()
        score = row[0] if row else 0.5  # neutral default
        adjustment = np.clip((score - 0.5) * 100 * 0.1, -5, 5)
        logging.info(f"Fetched Sentiment Score: {score}, Adjustment: {adjustment:.1f}%")
        return adjustment
    except sqlite3.OperationalError as e:
        logging.error(f"Error fetching sentiment score (likely missing table): {e}")
        return 0.0
    except Exception as e:
        logging.error(f"Error fetching sentiment score: {e}")
        return 0.0

# -----------------------------
# Database Initialization & Duplicate Check
# -----------------------------
def initialize_database(db_path=DB_PATH):
    """
    Ensure required tables exist. Creates the trading_signals and trade_history tables.
    Also ensures that trade_history has the 'note' and 'indicator_contributions' columns.
    """
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        # Create trading_signals table if not exists.
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS trading_signals (
                Date TEXT,
                Price REAL,
                Signal INTEGER,
                Confidence REAL
            )
        """)
        # Create trade_history table if not exists.
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS trade_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                execution_time TEXT,
                trade_type TEXT,
                executed_price REAL,
                message TEXT,
                status TEXT,
                note TEXT,
                indicator_contributions TEXT
            )
        """)
        conn.commit()
    except Exception as e:
        logging.error(f"Error initializing database: {e}")
    finally:
        if 'conn' in locals():
            conn.close()

def is_duplicate_trade(signal, db_path=DB_PATH):
    """
    Check if a similar trade (same trade type and price) was executed within the duplicate window.
    """
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        window_start = (datetime.now() - timedelta(hours=DUPLICATE_WINDOW_HOURS)).strftime('%Y-%m-%d %H:%M:%S')
        trade_type = "BUY" if signal['Signal'] == 1 else "SELL" if signal['Signal'] == -1 else "HOLD"
        query = """
            SELECT COUNT(*) FROM trade_history 
            WHERE trade_type = ? AND executed_price = ? AND execution_time >= ?
        """
        cursor.execute(query, (trade_type, signal['Price'], window_start))
        count = cursor.fetchone()[0]
        return count > 0
    except Exception as e:
        logging.error(f"Error checking duplicate trades: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

def record_trade(trade_type, executed_price, message, indicator_contributions=""):
    """
    Record an executed trade in the trade_history table.
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        execution_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("""
            INSERT INTO trade_history (execution_time, trade_type, executed_price, message, status, note, indicator_contributions)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (execution_time, trade_type, executed_price, message, "executed", "", indicator_contributions))
        conn.commit()
    except Exception as e:
        logging.error(f"Error recording trade: {e}")
    finally:
        if 'conn' in locals():
            conn.close()

# -----------------------------
# Trade Execution Logic
# -----------------------------
def execute_trade(signal):
    """
    Execute a trade based on the trading signal using dynamic risk parameters and position sizing.
    """
    # First, check for duplicate trades; if duplicate, skip execution.
    if is_duplicate_trade(signal):
        logging.info("Duplicate trade detected; skipping execution.")
        return (False, ACCOUNT_BALANCE)

    # For a real system, you might fetch the latest market price. Here we assume the signal price is current.
    current_price = signal['Price']
    
    # Calculate dynamic risk parameters
    atr = fetch_btc_atr()
    sentiment_adj = fetch_sentiment_adjustment()
    
    # Define base risk levels (these numbers can be calibrated)
    base_stop_loss_pct = 2.0  # base stop-loss percentage
    base_take_profit_pct = 4.0  # base take-profit percentage

    # Adjust risk levels using ATR and sentiment (example formulas)
    stop_loss_pct = base_stop_loss_pct + atr + (sentiment_adj * 0.05)  # e.g., ATR plus a fraction of sentiment adjustment
    take_profit_pct = base_take_profit_pct + (atr * 0.5)  # e.g., base plus half ATR

    logging.info(f"Dynamic Risk Levels - Stop-Loss: {stop_loss_pct:.1f}%, Take-Profit: {take_profit_pct:.1f}%")
    
    # Position sizing: risk 1% of account balance per trade.
    risk_per_trade = 0.01 * ACCOUNT_BALANCE
    # Dollar risk per share = current price * (stop_loss_pct / 100)
    dollar_risk_per_share = current_price * (stop_loss_pct / 100.0)
    if dollar_risk_per_share == 0:
        logging.error("Dollar risk per share calculated as 0; aborting trade.")
        return (False, ACCOUNT_BALANCE)
    shares_to_trade = risk_per_trade / dollar_risk_per_share

    trade_type = "BUY" if signal['Signal'] == 1 else "SELL" if signal['Signal'] == -1 else "HOLD"

    # (Real trade execution logic would connect to a broker API here.)
    # For this implementation, we simulate the trade by recording it in the trade_history table.
    trade_message = (f"Executed {trade_type}: {shares_to_trade:.2f} shares at ${current_price:.2f} | "
                     f"Stop-Loss: {stop_loss_pct:.1f}% | Take-Profit: {take_profit_pct:.1f}%")
    logging.info(trade_message)
    record_trade(trade_type, current_price, trade_message)
    
    # Update account balance (simulate deduction for BUY, addition for SELL)
    if trade_type == "BUY":
        new_balance = ACCOUNT_BALANCE - (shares_to_trade * current_price)
    elif trade_type == "SELL":
        new_balance = ACCOUNT_BALANCE + (shares_to_trade * current_price)
    else:
        new_balance = ACCOUNT_BALANCE

    return (True, new_balance)

# -----------------------------
# Main Execution Function
# -----------------------------
def main():
    # Initialize database tables if needed
    initialize_database()

    # Load trading signals from the database
    signals = load_signals()
    if not signals:
        logging.error("No trading signals available. Exiting.")
        return

    # Process each signal (from most recent to oldest)
    for signal in signals:
        logging.info(f"Processing signal dated {signal['Date']}")
        result, updated_balance = execute_trade(signal)
        if result:
            logging.info(f"Trade executed. Updated account balance: ${updated_balance:.2f}")
        else:
            logging.info("Trade skipped.")
        # Sleep between trades to simulate execution delay
        time.sleep(1)

if __name__ == "__main__":
    main()