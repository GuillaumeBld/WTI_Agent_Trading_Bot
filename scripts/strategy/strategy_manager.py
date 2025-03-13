#!/usr/bin/env python
"""
Strategy Manager Module

This module dynamically adjusts the trading strategy based on performance metrics
and past trade outcomes. It monitors key metrics to determine when to switch from
Adaptive Mode to Self-Optimizing Mode and adjusts indicator weighting accordingly.

Performance Metrics:
  - Sharpe Ratio (target ≥ 1.0)
  - Win Rate (target ≥ 55%)
  - Max Drawdown (should not exceed 10%)
  - Trade Count Threshold (switch modes after 30 trades)
  - Operation Days Threshold (switch modes after 7 trading days)

When any of these conditions are met consistently, the manager transitions
to Self-Optimizing Mode and rebalances indicator weights.
"""

import sqlite3
import logging
from datetime import datetime, timedelta

import json
import ta
CONFIG_PATH = "config.json"
with open(CONFIG_PATH, "r") as f:
    config = json.load(f)

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def compute_ta_indicators(df):
    """Compute technical indicators on market data DataFrame."""
    if df.empty:
        logging.warning("Empty DataFrame passed to compute_ta_indicators")
        return df
        
    try:
        # Momentum indicators
        df['RSI'] = ta.momentum.RSIIndicator(close=df['Close'], window=14).rsi()
        
        # Trend indicators
        df['EMA50'] = ta.trend.EMAIndicator(close=df['Close'], window=50).ema_indicator()
        df['EMA200'] = ta.trend.EMAIndicator(close=df['Close'], window=200).ema_indicator()
        
        # ADX with length check
        window = 14
        if len(df) >= window:
            df['ADX'] = ta.trend.ADXIndicator(high=df['High'], low=df['Low'], close=df['Close'], window=window).adx()
        else:
            df['ADX'] = float('nan')
            logging.warning(f"Insufficient data ({len(df)} rows) for ADX calculation")
        
        # MACD
        macd = ta.trend.MACD(close=df['Close'])
        df['MACD'] = macd.macd()
        df['MACD_Signal'] = macd.macd_signal()
        
        # Volatility
        df['ATR'] = ta.volatility.AverageTrueRange(
            high=df['High'], low=df['Low'], close=df['Close'], window=14
        ).average_true_range()
        
        logging.info("Successfully computed TA indicators")
        return df
        
    except Exception as e:
        logging.error(f"Error computing TA indicators: {e}")
        # Return DataFrame with NaN values for indicators if calculation fails
        for col in ['RSI', 'EMA50', 'EMA200', 'ADX', 'MACD', 'MACD_Signal', 'ATR']:
            df[col] = float('nan')
        return df

def validate_trade_with_ta(df, signal):
    """Validate trade signal with TA indicators."""
    if df.empty:
        return False
        
    latest = df.iloc[-1]
    confirmations = 0
    
    if signal["Signal"] == "BUY":
        if latest["RSI"] < 30:
            confirmations += 1
        if latest["MACD"] > latest["MACD_Signal"]:
            confirmations += 1
        if latest["Close"] > latest["EMA50"]:
            confirmations += 1
        # ADX is optional for BUY signals
    elif signal["Signal"] == "SELL":
        if latest["RSI"] > 70:
            confirmations += 1
        if latest["MACD"] < latest["MACD_Signal"]:
            confirmations += 1
        if latest["Close"] < latest["EMA200"]:
            confirmations += 1
        # ADX is optional for SELL signals
            
    # Require at least 2 indicators to confirm, ignoring ADX if NaN
    return confirmations >= 2

# Define the absolute path to your SQLite database (adjust as needed)
DB_PATH = "/Users/guillaumebolivard/Documents/School/Loyola_U/Classes/Capstone_MS_Finance/Trading_challenge/trading_bot/data/market_data.db"

class StrategyManager:
    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path
        self.mode = "Adaptive"  # Initial mode
        # Thresholds for mode transition
        self.sharpe_ratio_threshold = 1.0
        self.win_rate_threshold = 55.0  # Percentage
        self.max_drawdown_threshold = 10.0  # Percentage
        self.trade_count_threshold = 30
        self.operation_days_threshold = 7
        # Initial indicator weights (for example purposes)
        self.indicator_weights = {
            'RSI': 1.0,
            'MACD': 1.0,
            'ADX': 1.0,
            'EMA': 1.0,
            'Sentiment': 1.0
        }
        self.consecutive_improvement_count = 0
        
        # New: Load fine-tuning parameters from configuration (if available)
        self.fine_tune_window = config.get("fine_tune_window", 7)
        self.fine_tune_scale = config.get("fine_tune_scale", 10.0)
        self.smoothing_factor = config.get("smoothing_factor", 0.3) 

    def get_performance_metrics(self):
        """
        Retrieve performance metrics from the trade_history table in SQLite.
        Returns a dictionary with:
        - sharpe_ratio: Risk-adjusted return (dummy calculation based on win rate).
        - win_rate: Percentage of winning trades.
        - max_drawdown: Maximum drawdown in percent (dummy value based on trade count).
        - trade_count: Total number of trades executed.
        - operation_days: Number of days between the first and last trade.
        Assumes the trade_history table has an 'execution_time' column in "%Y-%m-%d %H:%M:%S" format
        and a 'status' column indicating 'win' or 'loss'.
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            # Get total trade count.
            cursor.execute("SELECT COUNT(*) FROM trade_history")
            trade_count = cursor.fetchone()[0]
            # Get win count.
            cursor.execute("SELECT COUNT(*) FROM trade_history WHERE status = 'win'")
            wins = cursor.fetchone()[0]
            win_rate = (wins / trade_count * 100) if trade_count > 0 else 0.0
            
            # Determine operation days based on execution_time.
            cursor.execute("SELECT MIN(execution_time), MAX(execution_time) FROM trade_history")
            min_time, max_time = cursor.fetchone()
            if min_time and max_time:
                d1 = datetime.strptime(min_time, "%Y-%m-%d %H:%M:%S")
                d2 = datetime.strptime(max_time, "%Y-%m-%d %H:%M:%S")
                operation_days = (d2 - d1).days + 1
            else:
                operation_days = 0

            # Dummy calculation for Sharpe Ratio and Max Drawdown.
            sharpe_ratio = 1.0 if win_rate >= self.win_rate_threshold else 0.9
            max_drawdown = 8.0 if trade_count < self.trade_count_threshold else 12.0

            metrics = {
                'sharpe_ratio': sharpe_ratio,
                'win_rate': win_rate,
                'max_drawdown': max_drawdown,
                'trade_count': trade_count,
                'operation_days': operation_days
            }
            conn.close()
            return metrics
        except Exception as e:
            logging.error(f"Error retrieving performance metrics: {e}")
            return {
                'sharpe_ratio': 0.0,
                'win_rate': 0.0,
                'max_drawdown': 100.0,
                'trade_count': 0,
                'operation_days': 0
            }

    def check_mode_transition(self):
        """
        Check performance metrics and determine whether to transition between Adaptive
        and Self-Optimizing Mode.
        Returns:
            tuple: (current mode, performance metrics dictionary)
        """
        metrics = self.get_performance_metrics()
        transition = False
        reasons = []
        if metrics["sharpe_ratio"] < self.sharpe_ratio_threshold:
            reasons.append("Sharpe Ratio below threshold")
            transition = True
        if metrics["win_rate"] < self.win_rate_threshold:
            reasons.append("Win Rate below threshold")
            transition = True
        if metrics["max_drawdown"] > self.max_drawdown_threshold:
            reasons.append("Max Drawdown exceeds threshold")
            transition = True
        if metrics["trade_count"] > self.trade_count_threshold:
            reasons.append("Trade count exceeds threshold")
            transition = True
        if metrics["operation_days"] > self.operation_days_threshold:
            reasons.append("Operation days exceed threshold")
            transition = True

        # If in Adaptive mode and performance is poor, switch to Self-Optimizing
        if self.mode == "Adaptive" and transition:
            logging.info("Transitioning from Adaptive to Self-Optimizing Mode due to: " + ", ".join(reasons))
            self.mode = "Self-Optimizing"
            self.consecutive_improvement_count = 0
        # If in Self-Optimizing mode and performance is good (no issues), count consecutive improvements
        elif self.mode == "Self-Optimizing" and not transition:
            self.consecutive_improvement_count += 1
            logging.info(f"Performance improved for {self.consecutive_improvement_count} consecutive periods.")
            if self.consecutive_improvement_count >= 3:
                logging.info("Reverting from Self-Optimizing to Adaptive Mode due to sustained improvements.")
                self.mode = "Adaptive"
                self.consecutive_improvement_count = 0
        # If in Self-Optimizing mode but performance is still poor, reset the improvement counter
        elif self.mode == "Self-Optimizing" and transition:
            logging.info("Performance still below thresholds; remaining in Self-Optimizing Mode.")
            self.consecutive_improvement_count = 0
        else:
            logging.info("No mode transition. Current mode: " + self.mode)
        return self.mode, metrics

    def adjust_indicator_weights_basic(self):
        """
        Dynamically adjust indicator weights based on historical trade outcomes.
        This implementation queries the trade_history table to calculate the average contribution
        of each indicator from the 'indicator_contributions' column (stored as a JSON string).
        For winning trades, contributions are taken as positive; for losing trades, as negative.
        The function then adjusts each indicator's weight accordingly:
        - If an indicator's average contribution is positive, its weight is increased.
        - If negative, its weight is decreased.
        We then clip weights between 0.5 and 2.0.
        
        Returns:
            dict: Updated indicator weights.
        """
        import json
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            # Query all trades that have indicator contributions.
            cursor.execute("SELECT indicator_contributions, status FROM trade_history WHERE indicator_contributions IS NOT NULL")
            rows = cursor.fetchall()
            conn.close()
            
            if not rows:
                logging.info("No trade history with indicator contributions found. Indicator weights remain unchanged.")
                return self.indicator_weights
            
            # Initialize a dictionary to collect contributions for each indicator.
            contributions = {key: [] for key in self.indicator_weights.keys()}
            
            for contrib_json, status in rows:
                try:
                    contribs = json.loads(contrib_json)
                    for indicator in self.indicator_weights.keys():
                        if indicator in contribs:
                            # For winning trades, contribution is positive; for losses, it's negative.
                            value = contribs[indicator] if status.lower() == 'win' else -contribs[indicator]
                            contributions[indicator].append(value)
                except Exception as e:
                    logging.error(f"Error parsing indicator contributions: {e}")
            
            # Calculate average contribution for each indicator.
            avg_contrib = {}
            for indicator, values in contributions.items():
                if values:
                    avg = sum(values) / len(values)
                else:
                    avg = 0.0
                avg_contrib[indicator] = avg
            
            logging.info("Average indicator contributions from trade history: " + str(avg_contrib))
            
            # Adjust weights based on average contributions.
            for indicator in self.indicator_weights.keys():
                # Determine an adjustment factor. Here we scale the average contribution by dividing by 10.
                # You can tweak the divisor to make the adjustments more or less sensitive.
                adjustment_factor = 1.0 + (avg_contrib[indicator] / 10)
                self.indicator_weights[indicator] *= adjustment_factor
                # Ensure weights remain within a reasonable range.
                self.indicator_weights[indicator] = min(max(self.indicator_weights[indicator], 0.5), 2.0)
            
            logging.info("Adjusted indicator weights based on trade history: " + str(self.indicator_weights))
            return self.indicator_weights
        except Exception as e:
            logging.error(f"Error adjusting indicator weights: {e}")
            return self.indicator_weights
    
    def fine_tune_indicator_weights(self):
        """
        Fine-tune adaptive indicator weighting adjustments over multiple trade cycles.
        
        This function retrieves trade history from the past 'window' days (configurable via self.fine_tune_window),
        computes the median indicator contribution from the 'indicator_contributions' column (stored as a JSON string),
        and then adjusts the indicator weights incrementally. Positive median contributions increase the weight,
        while negative contributions decrease the weight. The new weights are clipped between 0.5 and 2.0.
        The updated weights are also persisted to a JSON file.
        
        Returns:
            dict: Updated indicator weights.
        """
        import json
        import numpy as np
        try:
            window = self.fine_tune_window
            scale = self.fine_tune_scale
            cutoff_date = (datetime.now() - timedelta(days=window)).strftime("%Y-%m-%d %H:%M:%S")
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT indicator_contributions, status 
                FROM trade_history 
                WHERE indicator_contributions IS NOT NULL AND execution_time >= ?
            """, (cutoff_date,))
            rows = cursor.fetchall()
            conn.close()

            if not rows:
                logging.info("No trade history found in the past {} days. Indicator weights remain unchanged.".format(window))
                return self.indicator_weights

            # Collect contributions for each indicator into a dictionary
            contributions = {key: [] for key in self.indicator_weights.keys()}
            for contrib_json, status in rows:
                try:
                    contribs = json.loads(contrib_json)
                    for indicator in self.indicator_weights.keys():
                        if indicator in contribs:
                            # For wins, use the contribution as positive; for losses, negative.
                            value = contribs[indicator] if status.lower() == 'win' else -contribs[indicator]
                            contributions[indicator].append(value)
                except Exception as e:
                    logging.error(f"Error parsing indicator contributions: {e}")

            # Compute median contribution for each indicator
            median_contrib = {}
            for indicator, values in contributions.items():
                median_contrib[indicator] = np.median(values) if values else 0.0

            logging.info("Median indicator contributions over the last {} days: {}".format(window, median_contrib))
            # Adjust weights gradually using the median contribution and scale factor
            for indicator in self.indicator_weights.keys():
                adjustment = median_contrib[indicator] / scale  # small incremental change
                self.indicator_weights[indicator] *= (1.0 + adjustment)
                self.indicator_weights[indicator] = min(max(self.indicator_weights[indicator], 0.5), 2.0)

            logging.info("Fine-tuned indicator weights: " + str(self.indicator_weights))
            
            # Persist the updated weights to a JSON file for future reference
            weights_file = "data/indicator_weights.json"
            try:
                with open(weights_file, "w") as wf:
                    json.dump(self.indicator_weights, wf, indent=2)
                logging.info(f"Indicator weights persisted to {weights_file}")
            except Exception as pe:
                logging.error(f"Error persisting indicator weights: {pe}")
                
            return self.indicator_weights
        except Exception as e:
            logging.error(f"Error fine-tuning indicator weights: {e}")
            return self.indicator_weights

if __name__ == "__main__":
    manager = StrategyManager()
    mode, metrics = manager.check_mode_transition()
    logging.info("Current Mode: " + mode)
    logging.info("Performance Metrics: " + str(metrics))
    
    basic_weights = manager.adjust_indicator_weights_basic()
    logging.info("Basic Indicator Weights: " + str(basic_weights))
    
    fine_tuned_weights = manager.fine_tune_indicator_weights()
    logging.info("Fine-tuned Indicator Weights: " + str(fine_tuned_weights))
