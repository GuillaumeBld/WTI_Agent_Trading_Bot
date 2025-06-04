from scripts.data_fetch.fetch_historical_data import fetch_and_save_data
import os
import pandas as pd
import sqlite3
from datetime import datetime
from typing import List, Dict, Any, Optional, Union

# Import the MarketData interface
from agent_interfaces import MarketData, OptionsChainData
# Import utility functions
from utils import get_data_directory, get_db_connection, setup_logger
import os
# Import for fetching BTC options data
from .btc_options_fetch import fetch_btc_options_data

# Set up logging
logger = setup_logger("data_fetch", os.path.join("logs", "data_fetch.log"))

# Use the utility function instead
# def get_data_directory():
#     base_dir = os.path.dirname(os.path.abspath(__file__))
#     bot_dir = os.path.dirname(base_dir)
#     data_dir = os.path.join(bot_dir, "data")
#     os.makedirs(data_dir, exist_ok=True)
#     return data_dir

def fetch_market_data(days=365, symbol="BTC-USD") -> Optional[pd.DataFrame]:
    """
    Fetch market data using the robust fetch_historical_data implementation
    
    Args:
        days (int): Number of days of historical data to fetch
        symbol (str): Symbol to fetch data for (default: "BTC-USD")
        
    Returns:
        Optional[pd.DataFrame]: DataFrame with market data or None if fetch failed
    """
    logger.info(f"Attempting to fetch market data for symbol: {symbol}")

    if symbol.upper() == "BTC-USD": # Or whatever BTC symbol is configured
        logger.info("BTC symbol detected. Options data would be fetched by btc_options_fetch.py in a full integration.")
        # In a full integration, you might call fetch_btc_options_data here and process it.
        # For now, we still fetch OHLCV data for BTC to keep the downstream flow working.
        # The AgentManager will be responsible for calling the options fetcher.

    # Convert days to period string
    if days <= 7:
        period = "1wk"
    elif days <= 30:
        period = "1mo"
    elif days <= 365:
        period = "1y"
    else:
        period = "max"
    
    data_path = os.path.join(get_data_directory(), "historical_data.csv")
    
    # Fetch data using the robust implementation
    success = fetch_and_save_data(
        symbol=symbol,
        period=period,
        interval="1h",
        data_path=data_path
    )
    
    if not success:
        logger.error("Failed to fetch market data")
        return None
        
    # Load and return the data
    try:
        df = pd.read_csv(data_path, parse_dates=["Date"])
        logger.info(f"Successfully loaded {len(df)} records of market data")
        return df
    except Exception as e:
        logger.error(f"Error loading fetched data: {e}")
        return None

def convert_to_market_data(df: pd.DataFrame) -> List[MarketData]:
    """
    Convert a DataFrame to a list of MarketData objects
    
    Args:
        df (pd.DataFrame): DataFrame with market data
        
    Returns:
        List[MarketData]: List of MarketData objects
    """
    market_data_list = []
    for _, row in df.iterrows():
        try:
            market_data = MarketData(
                date=row["Date"],
                open=float(row["Open"]),
                high=float(row["High"]),
                low=float(row["Low"]),
                close=float(row["Close"]),
                volume=int(row["Volume"])
            )
            market_data_list.append(market_data)
        except Exception as e:
            logger.warning(f"Error converting row to MarketData: {e}")
    
    logger.info(f"Converted {len(market_data_list)} records to MarketData objects")
    return market_data_list

def save_data_to_csv(df: pd.DataFrame, filename: str = "btc_data.csv") -> bool:
    """
    Save DataFrame to CSV file
    
    Args:
        df (pd.DataFrame): DataFrame to save
        filename (str): Name of the CSV file
        
    Returns:
        bool: True if successful, False otherwise
    """
    data_dir = get_data_directory()
    filepath = os.path.join(data_dir, filename)
    try:
        df.to_csv(filepath, index=False)
        logger.info(f"Data saved to CSV at {filepath}")
        return True
    except Exception as e:
        logger.error(f"Error saving data to CSV: {e}")
        return False

def save_data_to_sqlite(df: pd.DataFrame, db_name: str = "market_data.db", table_name: str = "market_data") -> bool:
    """
    Save DataFrame to SQLite database
    
    Args:
        df (pd.DataFrame): DataFrame to save
        db_name (str): Name of the SQLite database
        table_name (str): Name of the table
        
    Returns:
        bool: True if successful, False otherwise
    """
    data_dir = get_data_directory()
    db_path = os.path.join(data_dir, db_name)
    
    try:
        conn = get_db_connection(db_path)
        if conn is None:
            return False
        
        cursor = conn.cursor()
        cursor.execute(f'''
            CREATE TABLE IF NOT EXISTS {table_name} (
                Date TEXT PRIMARY KEY,
                Open REAL,
                High REAL,
                Low REAL,
                Close REAL,
                Volume INTEGER,
                Sentiment_Score REAL DEFAULT NULL
            )
        ''')
        df.to_sql(table_name, conn, if_exists="replace", index=False)
        conn.close()
        logger.info(f"Data saved to SQLite database at {db_path} in table '{table_name}'")
        return True
    except Exception as e:
        logger.error(f"Error saving data to SQLite: {e}")
        return False

def main():
    logger.info("BTC Trading Bot - Market Data Fetching")
    logger.info("==================================================")
    
    df = fetch_market_data(days=365, symbol="BTC-USD")
    if df is None:
        logger.error("Market data could not be fetched. Exiting.")
        return
    
    # Convert to MarketData objects
    market_data_list = convert_to_market_data(df)
    
    # Save to CSV and SQLite
    save_data_to_csv(df)
    save_data_to_sqlite(df)
    
    logger.info(f"Data fetching and storage complete! Fetched {len(market_data_list)} records.")
    return market_data_list

if __name__ == "__main__":
    main()
