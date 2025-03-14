"""
Trading Strategy Module - Machine Learning Version with Sentiment Analysis

This module implements a trading strategy using machine learning and sentiment analysis
to predict price movements and generate trading signals.
"""

import os
import csv
import math
import json
import random
import sqlite3
from datetime import datetime
from typing import List, Dict, Any, Optional, Union

# Import the TradingSignal interface
from agent_interfaces import TradingSignal

# Import utility functions
from utils import get_data_directory, get_db_connection, setup_logger
import os

# Use relative paths with utility functions
INDICATORS_DATA_PATH = os.path.join(get_data_directory(), "crude_oil_with_indicators.csv")

# Use relative path for SQLite database
DB_PATH = os.path.join(get_data_directory(), "market_data.db")

# Import sentiment analysis
try:
    from sentiment_analysis import SentimentAnalyzer
except ImportError:
    # If not in path, try relative import
    import sys
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    try:
        from sentiment_analysis import SentimentAnalyzer
    except ImportError:
        print("Warning: Sentiment analysis module not found. Proceeding without sentiment analysis.")
        SentimentAnalyzer = None

class TradingStrategy:
    """
    TradingStrategy class for generating trading signals using machine learning and sentiment analysis.
    This dummy implementation is for testing purposes.
    """
    def __init__(self):
        self.model = None

    def load_model(self):
        # Simulate loading a machine learning model
        print("Loading dummy trading strategy model...")
        self.model = "DummyModel"

    def generate_signals(self, data) -> List[TradingSignal]:
        """
        Generate trading signals based on the input data.
        Args:
            data (list or DataFrame): Market data records.
        Returns:
            list: A list of TradingSignal objects.
        """
        signals = []
        for record in data:
            # If record is a dict, use .get(); if it's a tuple, assume column order: Date, Open, High, Low, Close, Volume.
            if isinstance(record, dict):
                date_str = record.get('Date', '2025-03-01')
                close = record.get('Close', 70.0)
            else:
                date_str = record[0] if len(record) > 0 else '2025-03-01'
                close = record[4] if len(record) > 4 else 70.0
            
            # Convert date string to datetime object
            try:
                date = datetime.strptime(date_str, '%Y-%m-%d')
            except ValueError:
                # If date format is different, try another common format
                try:
                    date = datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
                except ValueError:
                    # If all else fails, use current date
                    date = datetime.now()
            
            # Create a TradingSignal object
            signal = TradingSignal(
                date=date,
                price=round(close, 2),  # Round to nearest cent
                signal=1,       # BUY signal for demonstration
                confidence=0.75,
                source="strategy"
            )
            signals.append(signal)
        return signals

def train_test_split(X, y, test_size=0.2, random_state=None):
    """
    Simulate scikit-learn's train_test_split function.
    """
    if random_state is not None:
        random.seed(random_state)
    
    indices = list(range(len(X)))
    random.shuffle(indices)
    
    test_count = int(len(X) * test_size)
    test_indices = indices[:test_count]
    train_indices = indices[test_count:]
    
    X_train = [X[i] for i in train_indices]
    X_test = [X[i] for i in test_indices]
    y_train = [y[i] for i in train_indices]
    y_test = [y[i] for i in test_indices]
    
    return X_train, X_test, y_train, y_test

class SimpleDecisionTree:
    """
    A simple decision tree classifier implementation.
    """
    def __init__(self, max_depth=3):
        self.max_depth = max_depth
        self.tree = None
    
    def fit(self, X, y):
        # For simplicity, we create domain-based rules instead of an actual tree
        self.tree = {
            'rsi_threshold': 30,
            'macd_threshold': 0,
            'ema_ratio_threshold': 1.0,
            'adx_threshold': 25
        }
    
    def predict(self, X):
        predictions = []
        for features in X:
            rsi, macd, macd_signal, adx, ema_9, ema_21 = features
            score = 0
            
            # RSI rule
            if rsi < self.tree['rsi_threshold']:
                score += 1
            elif rsi > 70:
                score -= 1
            
            # MACD rule
            if macd > macd_signal:
                score += 1
            else:
                score -= 1
            
            # EMA rule
            if ema_9 > ema_21:
                score += 0.5
            else:
                score -= 0.5
            
            # ADX rule
            if adx > self.tree['adx_threshold']:
                score *= 1.2
            
            # Convert score to prediction
            if score > 0.5:
                predictions.append(1)   # Buy
            elif score < -0.5:
                predictions.append(-1)  # Sell
            else:
                predictions.append(0)   # Hold
        
        return predictions
    
    def predict_proba(self, X):
        predictions = self.predict(X)
        probabilities = []
        
        for pred in predictions:
            if pred == 1:
                probabilities.append(0.7)  # 70% confidence for buy
            elif pred == -1:
                probabilities.append(0.3)  # 30% confidence for sell
            else:
                probabilities.append(0.5)  # 50% for hold
        return probabilities

def load_data_with_indicators(filepath):
    """
    Load data with indicators from a CSV file.
    
    Args:
        filepath (str): Path to the CSV file
        
    Returns:
        list: List of dictionaries with the data
    """
    data = []
    try:
        with open(filepath, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                processed_row = {
                    'Date': row['Date'],
                    'Open': float(row['Open']) if row['Open'] else None,
                    'High': float(row['High']) if row['High'] else None,
                    'Low': float(row['Low']) if row['Low'] else None,
                    'Close': float(row['Close']) if row['Close'] else None,
                    'Volume': int(float(row['Volume'])) if row['Volume'] else None,
                    'RSI': float(row['RSI']) if row['RSI'] else None,
                    'MACD': float(row['MACD']) if row['MACD'] else None,
                    'MACD_Signal': float(row['MACD_Signal']) if row['MACD_Signal'] else None,
                    'MACD_Hist': float(row['MACD_Hist']) if row['MACD_Hist'] else None,
                    'ADX': float(row['ADX']) if row['ADX'] else None,
                    'EMA_9': float(row['EMA_9']) if row['EMA_9'] else None,
                    'EMA_21': float(row['EMA_21']) if row['EMA_21'] else None
                }
                data.append(processed_row)
        print(f"Loaded {len(data)} records from {filepath}")
        return data
    except Exception as e:
        print(f"Error loading data from {filepath}: {e}")
        return []

def prepare_features_and_target(data):
    """
    Prepare features (indicators) and target (future price movement).
    """
    features = []
    target = []
    dates = []
    prices = []
    
    # We need at least 2 days to measure next-day price change
    for i in range(len(data) - 1):
        # Skip if any indicators are missing
        if (data[i]['RSI'] is None or data[i]['MACD'] is None or 
            data[i]['MACD_Signal'] is None or data[i]['ADX'] is None or 
            data[i]['EMA_9'] is None or data[i]['EMA_21'] is None):
            continue
        
        current_price = data[i]['Close']
        next_price = data[i+1]['Close']
        if current_price is None or next_price is None:
            continue
        
        price_change = (next_price - current_price) / current_price
        
        # Feature vector
        feature = [
            data[i]['RSI'],
            data[i]['MACD'],
            data[i]['MACD_Signal'],
            data[i]['ADX'],
            data[i]['EMA_9'],
            data[i]['EMA_21']
        ]
        
        # Target labels
        if price_change > 0.005:
            label = 1  # Buy
        elif price_change < -0.005:
            label = -1 # Sell
        else:
            label = 0  # Hold
        
        features.append(feature)
        target.append(label)
        dates.append(data[i]['Date'])
        prices.append(current_price)
    
    return features, target, dates, prices

def train_model(features, target):
    """
    Train a machine learning model (simple decision tree).
    """
    X_train, X_test, y_train, y_test = train_test_split(features, target, test_size=0.2, random_state=42)
    model = SimpleDecisionTree(max_depth=3)
    model.fit(X_train, y_train)
    
    # Evaluate
    y_pred = model.predict(X_test)
    accuracy = sum(1 for i in range(len(y_pred)) if y_pred[i] == y_test[i]) / len(y_pred)
    print(f"Model trained with accuracy: {accuracy:.4f}")
    return model

def generate_signals_with_ml(data, model=None, use_sentiment=True) -> List[TradingSignal]:
    """
    Generate trading signals using ML and optional sentiment analysis.
    """
    features, target, dates, prices = prepare_features_and_target(data)
    
    # Train if no model provided
    if model is None:
        model = train_model(features, target)
    
    # Predict
    predictions = model.predict(features)
    probabilities = model.predict_proba(features)
    
    # Build signals
    signals = []
    for i in range(len(predictions)):
        # Convert date string to datetime object if needed
        if isinstance(dates[i], str):
            try:
                date = datetime.strptime(dates[i], '%Y-%m-%d')
            except ValueError:
                try:
                    date = datetime.strptime(dates[i], '%Y-%m-%d %H:%M:%S')
                except ValueError:
                    date = datetime.now()
        else:
            date = dates[i]
        
        # Create a TradingSignal object
        signal = TradingSignal(
            date=date,
            price=prices[i],
            signal=predictions[i],
            confidence=probabilities[i],
            source="ml_strategy"
        )
        signals.append(signal)
    
    # Optionally integrate sentiment
    if use_sentiment and SentimentAnalyzer is not None:
        try:
            analyzer = SentimentAnalyzer()
            sentiment_file = "data/sentiment_analysis_latest.json"
            sentiment_data = None
            
            # Attempt to find a sentiment file
            if not os.path.exists(sentiment_file):
                data_dir = "data"
                sentiment_files = [f for f in os.listdir(data_dir) if f.startswith("sentiment_analysis_") and f.endswith(".json")]
                if sentiment_files:
                    sentiment_files.sort(reverse=True)
                    sentiment_file = os.path.join(data_dir, sentiment_files[0])
            
            # Load or generate sentiment
            if os.path.exists(sentiment_file):
                with open(sentiment_file, 'r') as f:
                    sentiment_data = json.load(f)
                print(f"Loaded sentiment data from {sentiment_file}")
            else:
                print("No sentiment data found. Generating new sentiment analysis...")
                news = analyzer.fetch_crude_oil_news()
                sentiment_results = analyzer.analyze_news_sentiment(news)
                trading_signal = analyzer.get_trading_signal_from_sentiment(sentiment_results)
                sentiment_data = {
                    "sentiment_results": sentiment_results,
                    "trading_signal": trading_signal
                }
                print("Sentiment analysis generated.")
            
            # Adjust signals if sentiment data is available
            if sentiment_data:
                sentiment_score = sentiment_data["trading_signal"]["sentiment_score"]
                sentiment_signal = sentiment_data["trading_signal"]["signal"]
                sentiment_confidence = sentiment_data["trading_signal"]["confidence"]
                
                print(f"Incorporating sentiment analysis: Score={sentiment_score:.2f}, Signal={sentiment_signal}, Confidence={sentiment_confidence:.2f}")
                
                # Modify the last 5 signals
                for i in range(max(0, len(signals) - 5), len(signals)):
                    orig_signal = signals[i].signal
                    orig_conf = signals[i].confidence
                    
                    if (orig_signal > 0 and sentiment_signal > 0) or (orig_signal < 0 and sentiment_signal < 0):
                        # Sentiment agrees, boost confidence
                        new_conf = min(0.95, orig_conf + 0.1 * sentiment_confidence)
                        signals[i].confidence = new_conf
                    elif abs(sentiment_signal) > 0.7 and sentiment_confidence > 0.7:
                        # Strongly disagree, flip
                        signals[i].signal = sentiment_signal
                        signals[i].confidence = sentiment_confidence
                    elif sentiment_signal != 0:
                        # Mild disagreement, reduce confidence
                        new_conf = max(0.5, orig_conf - 0.1 * sentiment_confidence)
                        signals[i].confidence = new_conf
                    
                    # Update source to indicate sentiment was used
                    signals[i].source = "ml_strategy_with_sentiment"
        except Exception as e:
            print(f"Error incorporating sentiment analysis: {e}")
    
    return signals

def save_signals_to_csv(signals: List[TradingSignal], filepath: str) -> bool:
    """
    Save trading signals to a CSV file.
    """
    try:
        with open(filepath, 'w', newline='') as f:
            fieldnames = ['Date', 'Price', 'Signal', 'Confidence', 'Source']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for s in signals:
                # Convert TradingSignal to dict for CSV writing
                writer.writerow({
                    'Date': s.date.strftime('%Y-%m-%d %H:%M:%S'),
                    'Price': s.price,
                    'Signal': s.signal,
                    'Confidence': s.confidence,
                    'Source': s.source
                })
        print(f"Trading signals saved to {filepath}")
        return True
    except Exception as e:
        print(f"Error saving signals to {filepath}: {e}")
        return False

def save_signals_to_sqlite(signals: List[TradingSignal], db_path: str, table_name: str = "trading_signals") -> bool:
    """
    Save trading signals to an SQLite database.
    """
    try:
        import pandas as pd
        # Convert TradingSignal objects to dictionaries
        signals_dicts = []
        for s in signals:
            signals_dicts.append({
                'Date': s.date.strftime('%Y-%m-%d %H:%M:%S'),
                'Price': s.price,
                'Signal': s.signal,
                'Confidence': s.confidence,
                'Source': s.source,
                'LimitPrice': s.limit_price
            })
        
        df_signals = pd.DataFrame(signals_dicts)
        conn = sqlite3.connect(db_path)
        df_signals.to_sql(table_name, conn, if_exists="replace", index=False)
        conn.close()
        print(f"Trading signals stored in SQLite database at {db_path} in table '{table_name}'")
        return True
    except Exception as e:
        print(f"Error saving signals to SQLite: {e}")
        return False

def main():
    import argparse
    parser = argparse.ArgumentParser(description='Generate trading signals using machine learning')
    parser.add_argument('--sentiment', action='store_true', help='Use sentiment analysis')
    parser.add_argument('--no-sentiment', dest='sentiment', action='store_false', help='Do not use sentiment analysis')
    parser.add_argument('--output', type=str, default='data/trading_signals_ml.csv', help='Output CSV file path')
    parser.set_defaults(sentiment=True)
    args = parser.parse_args()
    
    print("WTI Crude Oil Trading System - ML Strategy")
    print("==========================================")
    
    # Use the absolute path for the CSV with indicators
    data_path = INDICATORS_DATA_PATH
    
    data = load_data_with_indicators(data_path)
    if not data:
        print("No data available. Please run indicators.py first (to generate the indicators CSV).")
        return
    
    print(f"Generating ML-based trading signals for {len(data)} records...")
    
    signals = generate_signals_with_ml(data, use_sentiment=args.sentiment)
    if not signals:
        print("Failed to generate signals.")
        return
    
    print(f"Generated {len(signals)} trading signals.")
    print("\nLast 5 trading signals:")
    for s in signals[-5:]:
        s_type = "BUY" if s.signal == 1 else "SELL" if s.signal == -1 else "HOLD"
        print(f"Date: {s.date}, Price: ${s.price:.2f}, Signal: {s_type}, Confidence: {s.confidence:.2f}, Source: {s.source}")
    
    output_path = args.output
    save_signals_to_csv(signals, output_path)
    # Also save signals to the database
    save_signals_to_sqlite(signals, DB_PATH, table_name="trading_signals")
    
    print("\nML trading strategy execution complete!")
    print(f"Sentiment analysis: {'Enabled' if args.sentiment else 'Disabled'}")
    print("You can now proceed with backtesting the ML strategy.")

if __name__ == "__main__":
    main()
