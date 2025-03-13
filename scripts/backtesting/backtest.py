#!/usr/bin/env python
"""
Backtesting Module for WTI Crude Oil Trading System

This module loads price data from CSV, loads trading signals from SQLite,
executes a backtest simulation with real portfolio updates and risk management,
calculates performance metrics, and saves the results both to SQLite and CSV.
"""

import os
import math
import sqlite3
from datetime import datetime, timedelta
import logging
import csv
import numpy as np
import yfinance as yf
import pandas as pd

# Configure logging for backtesting
logging.basicConfig(
    filename="data/backtest_logs.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

###############################################################################
# 1. Define absolute paths for your CSV and DB
###############################################################################
PRICE_DATA_PATH = "/Users/guillaumebolivard/Documents/School/Loyola_U/Classes/Capstone_MS_Finance/Trading_challenge/trading_bot/data/crude_oil_data.csv"
DB_PATH = "/Users/guillaumebolivard/Documents/School/Loyola_U/Classes/Capstone_MS_Finance/Trading_challenge/trading_bot/data/market_data.db"

###############################################################################
# 2. Load Price Data from CSV (with error handling for non-numeric rows)
###############################################################################
def load_price_data(filepath):
    """
    Load price data from a CSV file.
    Returns a list of dictionaries sorted by Date (ascending).
    """
    data = []
    try:
        with open(filepath, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if not row['Date'].strip():
                    continue
                try:
                    processed_row = {
                        'Date': row['Date'],
                        'Open': float(row['Open']),
                        'High': float(row['High']),
                        'Low': float(row['Low']),
                        'Close': float(row['Close']),
                        'Volume': int(row['Volume'])
                    }
                    data.append(processed_row)
                except Exception as conv_e:
                    logging.error(f"Error converting row {row}: {conv_e}")
                    continue
        data.sort(key=lambda x: datetime.strptime(x['Date'], '%Y-%m-%d'))
        logging.info(f"Loaded {len(data)} price records from {filepath}")
        return data
    except Exception as e:
        logging.error(f"Error loading price data from {filepath}: {e}")
        return []

###############################################################################
# 3. Load Trading Signals from SQLite
###############################################################################
def load_signals_sqlite(db_path=DB_PATH, table_name="trading_signals"):
    """
    Load trading signals from the SQLite database.
    Returns a list of dictionaries sorted by Date (ascending).
    """
    signals = []
    try:
        conn = sqlite3.connect(db_path)
        query = f"SELECT * FROM {table_name} ORDER BY Date ASC"
        cursor = conn.execute(query)
        columns = [desc[0] for desc in cursor.description]
        for row in cursor:
            row_dict = dict(zip(columns, row))
            row_dict['Price'] = float(row_dict['Price'])
            row_dict['Signal'] = int(row_dict['Signal'])
            row_dict['Confidence'] = float(row_dict['Confidence'])
            signals.append(row_dict)
        conn.close()
        logging.info(f"Loaded {len(signals)} trading signals from {db_path} (table: {table_name})")
        return signals
    except Exception as e:
        logging.error(f"Error loading signals from {db_path}: {e}")
        return []

###############################################################################
# 4. Helper Functions for ATR and Sentiment
###############################################################################
def fetch_wti_atr():
    """
    Fetch the Average True Range (ATR) for WTI crude oil using 14 days of Yahoo Finance data.
    """
    try:
        ticker = yf.Ticker("CL=F")
        data = ticker.history(period="14d")
        true_range = np.abs(data["High"] - data["Low"])
        atr = true_range.rolling(window=14).mean().iloc[-1]
        logging.info(f"Fetched WTI ATR: {atr:.2f}")
        return atr
    except Exception as e:
        logging.error(f"Error fetching WTI ATR: {e}")
        return None

def fetch_sentiment_adjustment(db_path=DB_PATH):
    """
    Fetch the latest sentiment score and calculate its adjustment.
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
    except Exception as e:
        logging.error(f"Error fetching sentiment score: {e}")
        return 0.0

###############################################################################
# 5. Backtest Execution Logic
###############################################################################
def run_backtest(price_data, signals, initial_capital=100000.0, commission_rate=0.001, slippage_rate=0.001, stop_loss_pct=0.02, take_profit_pct=0.05):
    """
    Run a backtest simulation with real portfolio updates and risk management.
    
    Args:
        price_data (list): List of dictionaries with daily price data, each having at least 'Date' and 'Close'.
        signals (list): List of dictionaries with trading signals, with keys 'Date', 'Signal', and 'Confidence'.
        initial_capital (float): Starting capital for the simulation.
        commission_rate (float): Commission percentage applied on each trade.
        slippage_rate (float): Slippage percentage applied on each trade.
        stop_loss_pct (float): Stop-loss threshold as a percentage.
        take_profit_pct (float): Take-profit threshold as a percentage.
    
    Returns:
        tuple: (daily_results, portfolio) where daily_results is a list of dictionaries with 'Date' and 'Portfolio_Value',
               and portfolio is the final portfolio state.
    """
    # Ensure price_data is sorted by date (ascending)
    price_data = sorted(price_data, key=lambda x: x['Date'])
    
    # Initialize portfolio with additional fields for backtesting
    portfolio = {
        'cash': initial_capital,
        'position': 0.0,       # Number of shares held
        'entry_price': None,   # Price at which position was opened
        'trades': 0,           # Total number of trades executed
        'wins': 0,
        'losses': 0,
        'open_trades': []      # For more advanced simulation
    }
    daily_results = []
    
    # For simplicity, we'll simulate trades based on daily signals:
    for day in price_data:
        day_date = day['Date']
        close_price = day['Close']
        
        # Find signals for the current day (assume one signal per day)
        daily_signals = [s for s in signals if s['Date'] == day_date]
        if daily_signals:
            signal = daily_signals[0]
            if signal['Signal'] == 1 and portfolio['position'] == 0:
                # BUY: invest all cash
                # Round price to nearest cent and quantity to whole shares
                rounded_price = round(close_price, 2)
                shares = portfolio['cash'] / (rounded_price * (1 + commission_rate + slippage_rate))
                shares = int(shares)  # Round down to whole shares
                cost = rounded_price * shares * (1 + commission_rate + slippage_rate)
                portfolio['cash'] -= cost
                portfolio['position'] = shares
                portfolio['entry_price'] = close_price
                portfolio['trades'] += 1
                logging.info(f"BUY on {day_date}: {shares:.2f} shares at ${close_price:.2f}")
            elif signal['Signal'] == -1 and portfolio['position'] > 0:
                # SELL: liquidate position
                rounded_price = round(close_price, 2)
                revenue = rounded_price * portfolio['position'] * (1 - commission_rate - slippage_rate)
                portfolio['cash'] += revenue
                portfolio['trades'] += 1
                pnl = revenue - (portfolio['position'] * portfolio['entry_price'])
                if pnl > 0:
                    portfolio['wins'] += 1
                else:
                    portfolio['losses'] += 1
                logging.info(f"SELL on {day_date}: Sold {portfolio['position']:.2f} shares at ${close_price:.2f}, PnL: {pnl:.2f}")
                portfolio['position'] = 0.0
                portfolio['entry_price'] = None
        
        # Risk management: if a position is held, check for stop loss or take profit.
        if portfolio['position'] > 0 and portfolio['entry_price'] is not None:
            # Stop loss check
            if close_price <= portfolio['entry_price'] * (1 - stop_loss_pct):
                rounded_price = round(close_price, 2)
                revenue = rounded_price * portfolio['position'] * (1 - commission_rate - slippage_rate)
                portfolio['cash'] += revenue
                portfolio['trades'] += 1
                pnl = revenue - (portfolio['position'] * portfolio['entry_price'])
                portfolio['losses'] += 1
                logging.info(f"STOP LOSS on {day_date}: Sold {portfolio['position']:.2f} shares at ${close_price:.2f}, PnL: {pnl:.2f}")
                portfolio['position'] = 0.0
                portfolio['entry_price'] = None
            # Take profit check
            elif close_price >= portfolio['entry_price'] * (1 + take_profit_pct):
                revenue = close_price * portfolio['position'] * (1 - commission_rate - slippage_rate)
                portfolio['cash'] += revenue
                portfolio['trades'] += 1
                pnl = revenue - (portfolio['position'] * portfolio['entry_price'])
                portfolio['wins'] += 1
                logging.info(f"TAKE PROFIT on {day_date}: Sold {portfolio['position']:.2f} shares at ${close_price:.2f}, PnL: {pnl:.2f}")
                portfolio['position'] = 0.0
                portfolio['entry_price'] = None
        
        # Compute current portfolio value
        current_value = portfolio['cash'] + (portfolio['position'] * close_price)
        daily_results.append({'Date': day_date, 'Portfolio_Value': current_value})
    
    return daily_results, portfolio

###############################################################################
# 6. Performance Metrics
###############################################################################
def calculate_metrics(results, portfolio, initial_capital):
    """
    Calculate performance metrics from the backtest results.
    """
    final_value = results[-1]['Portfolio_Value']
    total_return = (final_value / initial_capital) - 1
    days = len(results)
    annual_return = total_return * (252 / days) if days > 0 else 0
    daily_returns = [ (r['Portfolio_Value'] - initial_capital)/initial_capital for r in results ]
    mean_return = sum(daily_returns) / len(daily_returns) if daily_returns else 0
    std_return = math.sqrt(sum((r - mean_return) ** 2 for r in daily_returns) / len(daily_returns)) if daily_returns else 0
    sharpe_ratio = (annual_return - 0.02) / (std_return * math.sqrt(252)) if std_return > 0 else 0
    max_drawdown = calculate_max_drawdown(results)
    win_rate = portfolio['wins'] / portfolio['trades'] if portfolio['trades'] > 0 else 0
    wins = sum(r['Portfolio_Value'] for r in results if r['Portfolio_Value'] > initial_capital)
    losses = sum(initial_capital - r['Portfolio_Value'] for r in results if r['Portfolio_Value'] < initial_capital)
    profit_factor = (wins / losses) if losses > 0 else None

    metrics = {
        'Total Return': total_return,
        'Annual Return': annual_return,
        'Sharpe Ratio': sharpe_ratio,
        'Max Drawdown': max_drawdown,
        'Win Rate': win_rate,
        'Number of Trades': portfolio['trades'],
        'Profit Factor': profit_factor
    }
    return metrics

def calculate_max_drawdown(results):
    """
    Calculate maximum drawdown from daily portfolio values.
    """
    peak = -float('inf')
    max_dd = 0
    for r in results:
        value = r['Portfolio_Value']
        if value > peak:
            peak = value
        dd = (peak - value) / peak if peak > 0 else 0
        if dd > max_dd:
            max_dd = dd
    return max_dd

###############################################################################
# 7. Saving Backtest Results
###############################################################################
def save_results_to_sqlite(results, db_path=DB_PATH, table_name="backtest_results"):
    """
    Store backtest results in the SQLite database.
    """
    try:
        df = pd.DataFrame(results)
        with sqlite3.connect(db_path) as conn:
            df.to_sql(table_name, conn, if_exists="replace", index=False)
        logging.info(f"Backtest results stored in SQLite database at {db_path} (table: {table_name})")
        return True
    except Exception as e:
        logging.error(f"Error saving backtest results to SQLite: {e}")
        return False

def save_results_to_csv(results, filepath):
    """
    Save backtest results to a CSV file.
    """
    try:
        with open(filepath, 'w', newline='') as f:
            fieldnames = list(results[0].keys())
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for r in results:
                writer.writerow(r)
        logging.info(f"Backtest results saved to CSV at {filepath}")
        return True
    except Exception as e:
        logging.error(f"Error saving backtest results to CSV: {e}")
        return False

###############################################################################
# 8. Main Entry Point
###############################################################################
def main():
    print("WTI Crude Oil Trading System - Backtesting Module")
    print("===================================================")
    
    # 1. Load price data from CSV.
    price_data = load_price_data(PRICE_DATA_PATH)
    if not price_data:
        print("No price data available. Please run data_fetch.py first.")
        return
    
    # 2. Load trading signals from SQLite.
    signals = load_signals_sqlite(db_path=DB_PATH, table_name="trading_signals")
    if not signals:
        print("No trading signals available in the database. Please run strategy.py first.")
        return
    
    # 3. Set backtest parameters.
    initial_capital = 100000.0
    commission = 0.001
    slippage = 0.001
    stop_loss = 0.02   # 2% loss triggers exit
    take_profit = 0.05 # 5% gain triggers exit
    confidence_threshold = 50.0  # This can be adjusted dynamically in live trading
    
    print(f"Running backtest with initial capital: ${initial_capital:.2f}")
    
    # 4. Run backtest.
    results, portfolio = run_backtest(price_data, signals, initial_capital, commission, slippage, stop_loss, take_profit)
    if not results:
        print("Backtest failed.")
        return
    
    # 5. Calculate performance metrics.
    metrics = calculate_metrics(results, portfolio, initial_capital)
    
    # 6. Display results.
    print("\nBacktest Results:")
    print(f"Final Portfolio Value: ${results[-1]['Portfolio_Value']:.2f}")
    print("\nPerformance Metrics:")
    for key, value in metrics.items():
        print(f"{key}: {value:.4f}")
    
    # 7. Save results.
    os.makedirs("../results", exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_filepath = f"../results/backtest_results_{timestamp}.csv"
    save_results_to_csv(results, csv_filepath)
    save_results_to_sqlite(results, db_path=DB_PATH, table_name="backtest_results")
    
    print("\nBacktesting complete! Results have been saved.")

if __name__ == "__main__":
    main()
