#!/usr/bin/env python3
"""
Investment Tracker

This module allows manual input and confirmation of executed trades, integrating with AI-suggested trades
from trading_agent.py. It updates the portfolio (account balance and open positions), records trades
in an SQLite database (market_data.db), and supports real-time balance tracking and trade confirmation.
"""

import os
import sqlite3
import time
import logging
from datetime import datetime, timedelta
import sys

# -----------------------------
# Global Constants & Configuration
# -----------------------------
DB_PATH = os.path.join("data", "market_data.db")  # Shared with trading_agent.py
INITIAL_BALANCE = 100000.0  # Starting account balance (can be overridden by DB)

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# -----------------------------
# Database Functions
# -----------------------------
def initialize_database(db_path=DB_PATH):
    """
    Ensure that the trade_history and account tables exist with the required columns.
    """
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        # Trade history table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS trade_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                execution_time TEXT,
                trade_type TEXT,
                executed_price REAL,
                shares REAL,
                cost REAL,
                note TEXT
            )
        """)
        # Account table (hardcode default balance)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS account (
                id INTEGER PRIMARY KEY,
                balance REAL DEFAULT 100000.0
            )
        """)
        # Trades table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                signal TEXT,
                entry_price REAL,
                stop_loss REAL,
                take_profit REAL,
                size REAL,
                confidence REAL,
                timestamp TEXT,
                confirmed INTEGER DEFAULT 0
            )
        """)
        # Ensure account exists with initial balance
        cursor.execute("INSERT OR IGNORE INTO account (id, balance) VALUES (1, 100000.0)")
        conn.commit()
        logging.info("Database initialized.")
    except Exception as e:
        logging.error(f"Error initializing database: {e}")
    finally:
        if 'conn' in locals():
            conn.close()

def get_account_balance(db_path=DB_PATH):
    """
    Fetch the current account balance from the database.
    """
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT balance FROM account WHERE id = 1")
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else INITIAL_BALANCE
    except Exception as e:
        logging.error(f"Error fetching balance: {e}")
        return INITIAL_BALANCE

def update_account_balance(new_balance, db_path=DB_PATH):
    """
    Update the account balance in the database.
    """
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("UPDATE account SET balance = ? WHERE id = 1", (new_balance,))
        conn.commit()
        logging.info(f"Updated account balance to ${new_balance:.2f}")
    except Exception as e:
        logging.error(f"Error updating balance: {e}")
    finally:
        if 'conn' in locals():
            conn.close()

def record_trade(trade_type, executed_price, shares, cost, note="", db_path=DB_PATH):
    """
    Record an executed trade in the trade_history table.
    """
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        execution_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("""
            INSERT INTO trade_history (execution_time, trade_type, executed_price, shares, cost, note)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (execution_time, trade_type, executed_price, shares, cost, note))
        conn.commit()
        logging.info(f"Recorded trade: {trade_type} {shares} shares at ${executed_price:.2f} for ${cost:.2f}")
    except Exception as e:
        logging.error(f"Error recording trade: {e}")
    finally:
        if 'conn' in locals():
            conn.close()

def confirm_trade(trade_id, db_path=DB_PATH):
    """
    Mark an AI-suggested trade as confirmed in the trades table and update balance.
    """
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT signal, entry_price, size FROM trades WHERE id = ?", (trade_id,))
        trade = cursor.fetchone()
        if not trade:
            logging.error(f"Trade ID {trade_id} not found.")
            return False

        signal, entry_price, size = trade
        balance = get_account_balance()
        cost = entry_price * size

        if signal == "BUY":
            if cost > balance:
                logging.error("Insufficient funds to confirm BUY trade.")
                return False
            balance -= cost
        else:  # SELL
            balance += cost  # Simplified: assume SELL closes at entry price

        cursor.execute("UPDATE trades SET confirmed = 1 WHERE id = ?", (trade_id,))
        update_account_balance(balance)
        # Record in trade_history for historical tracking
        record_trade(signal, entry_price, size, cost, note=f"Confirmed AI trade ID {trade_id}")
        conn.commit()
        logging.info(f"Trade ID {trade_id} confirmed. Updated balance: ${balance:.2f}")
        return True
    except Exception as e:
        logging.error(f"Error confirming trade: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

def get_unconfirmed_trades(db_path=DB_PATH):
    """
    Fetch all unconfirmed AI-suggested trades from the trades table.
    """
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT id, signal, entry_price, size, timestamp FROM trades WHERE confirmed = 0")
        unconfirmed_trades = cursor.fetchall()
        conn.close()
        return unconfirmed_trades
    except Exception as e:
        logging.error(f"Error fetching unconfirmed trades: {e}")
        return []

# -----------------------------
# Investment Tracker Logic
# -----------------------------
class InvestmentTracker:
    def __init__(self):
        self.balance = get_account_balance()  # Load real-time balance from DB
        self.open_trades = []  # List to track open positions (if needed)

    def display_portfolio(self):
        """Display current account balance and open trades."""
        print(f"Current Account Balance: ${self.balance:.2f}")
        if self.open_trades:
            print("Open Trades:")
            for trade in self.open_trades:
                print(f"  {trade}")
        else:
            print("No open trades.")
        # Display unconfirmed AI trades
        unconfirmed = get_unconfirmed_trades()
        if unconfirmed:
            print("\nUnconfirmed AI Trade Suggestions:")
            for trade in unconfirmed:
                print(f"  ID: {trade[0]}, Signal: {trade[1]}, Price: ${trade[2]:.2f}, Size: {trade[3]}, Time: {trade[4]}")

    def process_manual_trade(self):
        """
        Manually input trade details and update the portfolio.
        """
        trade_type = input("Enter trade type (BUY/SELL): ").strip().upper()
        if trade_type not in ["BUY", "SELL"]:
            print("Invalid trade type. Must be BUY or SELL.")
            return

        try:
            executed_price = float(input("Enter executed price: ").strip())
            shares = float(input("Enter number of shares: ").strip())
        except ValueError:
            print("Invalid number entered.")
            return

        cost = executed_price * shares
        note = input("Enter any note for this trade (optional): ").strip()

        # Update balance and open trades
        if trade_type == "BUY":
            if cost > self.balance:
                print("Insufficient funds for this trade.")
                return
            self.balance -= cost
            self.open_trades.append({
                "Date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "Entry_Price": executed_price,
                "Shares": shares
            })
        else:  # SELL
            self.balance += cost
            # Clear open trades on SELL (simplified)
            self.open_trades = []

        # Record the trade
        record_trade(trade_type, executed_price, shares, cost, note)
        update_account_balance(self.balance)
        print(f"Trade executed: {trade_type} {shares} shares at ${executed_price:.2f}.")
        print(f"Updated balance: ${self.balance:.2f}")

    def confirm_ai_trade(self):
        """Manually confirm an AI-suggested trade by ID."""
        unconfirmed = get_unconfirmed_trades()
        if not unconfirmed:
            print("No unconfirmed trades to confirm.")
            return

        print("\nUnconfirmed AI Trades:")
        for trade in unconfirmed:
            print(f"  ID: {trade[0]}, Signal: {trade[1]}, Price: ${trade[2]:.2f}, Size: {trade[3]}, Time: {trade[4]}")

        try:
            trade_id = int(input("Enter the ID of the trade to confirm (or 0 to cancel): ").strip())
            if trade_id == 0:
                return
            if confirm_trade(trade_id):
                self.balance = get_account_balance()  # Refresh balance
                print(f"Trade ID {trade_id} confirmed successfully.")
            else:
                print(f"Failed to confirm trade ID {trade_id}.")
        except ValueError:
            print("Invalid trade ID entered.")

def main():
    # Initialize database
    initialize_database(DB_PATH)

    tracker = InvestmentTracker()
    print("Welcome to the Investment Tracker.")
    tracker.display_portfolio()

    while True:
        print("\nOptions:")
        print("1. Input a new manual trade")
        print("2. Confirm an AI-suggested trade")
        print("3. Display portfolio and unconfirmed trades")
        print("4. Exit")
        choice = input("Enter your choice: ").strip()
        if choice == "1":
            tracker.process_manual_trade()
        elif choice == "2":
            tracker.confirm_ai_trade()
        elif choice == "3":
            tracker.display_portfolio()
        elif choice == "4":
            print("Exiting Investment Tracker.")
            break
        else:
            print("Invalid choice. Please try again.")
        # Add a short pause between operations
        time.sleep(1)

if __name__ == "__main__":
    main()