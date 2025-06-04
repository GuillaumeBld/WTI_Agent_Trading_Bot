# utils.py
import json
import os
import logging
import sqlite3
from typing import Dict, Any, Optional

# Set up basic logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

def load_config(config_path="config.json") -> Dict[str, Any]:
    """
    Load configuration from a JSON file.
    
    Args:
        config_path (str): Path to the configuration file.
        
    Returns:
        dict: Configuration dictionary.
    """
    try:
        with open(config_path, "r") as f:
            config = json.load(f)
        logger.info(f"Configuration loaded from {config_path}")
        return config
    except FileNotFoundError:
        logger.warning(f"Configuration file {config_path} not found. Using default configuration.")
        return {}
    except json.JSONDecodeError:
        logger.error(f"Error parsing configuration file {config_path}. Using default configuration.")
        return {}
    except Exception as e:
        logger.error(f"Error loading configuration: {e}. Using default configuration.")
        return {}

def get_db_connection(db_path: str) -> Optional[sqlite3.Connection]:
    """
    Get a connection to the SQLite database.
    
    Args:
        db_path (str): Path to the SQLite database.
        
    Returns:
        sqlite3.Connection: Connection to the database, or None if connection failed.
    """
    try:
        conn = sqlite3.connect(db_path)
        logger.info(f"Connected to database at {db_path}")
        return conn
    except Exception as e:
        logger.error(f"Error connecting to database: {e}")
        return None

def get_data_directory() -> str:
    """
    Get the path to the data directory, creating it if it doesn't exist.
    
    Returns:
        str: Path to the data directory.
    """
    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(base_dir, "data")
    os.makedirs(data_dir, exist_ok=True)
    return data_dir

def get_logs_directory() -> str:
    """
    Get the path to the logs directory, creating it if it doesn't exist.
    
    Returns:
        str: Path to the logs directory.
    """
    base_dir = os.path.dirname(os.path.abspath(__file__))
    logs_dir = os.path.join(base_dir, "logs")
    os.makedirs(logs_dir, exist_ok=True)
    return logs_dir

def setup_logger(name: str, log_file: Optional[str] = None, level=logging.INFO) -> logging.Logger:
    """
    Set up a logger with the specified name and log file.
    
    Args:
        name (str): Name of the logger.
        log_file (str, optional): Path to the log file. If None, logs will only be output to the console.
        level (int, optional): Logging level. Defaults to logging.INFO.
        
    Returns:
        logging.Logger: Configured logger.
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Create formatter
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    
    # Create console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # Create file handler if log_file is specified
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger
