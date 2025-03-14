# WTI Agent Trading Bot Improvements

This document outlines the improvements made to the WTI Agent Trading Bot to enhance its robustness, portability, and deployability.

## 1. Fixed Hardcoded File Paths

### Problem
The strategy module contained hardcoded absolute file paths that were specific to a particular user's environment:

```python
# Absolute path to your CSV file with indicators:
INDICATORS_DATA_PATH = "/Users/guillaumebolivard/Documents/School/Loyola_U/Classes/Capstone_MS_Finance/Trading_challenge/trading_bot/data/crude_oil_with_indicators.csv"

# Absolute path to the SQLite database (where signals will be stored)
DB_PATH = "/Users/guillaumebolivard/Documents/School/Loyola_U/Classes/Capstone_MS_Finance/Trading_challenge/trading_bot/data/market_data.db"
```

These hardcoded paths would prevent the code from running on different machines or in containerized environments.

### Solution
Replaced hardcoded paths with relative paths using utility functions:

```python
# Import utility functions
from utils import get_data_directory, get_db_connection, setup_logger
import os

# Use relative paths with utility functions
INDICATORS_DATA_PATH = os.path.join(get_data_directory(), "crude_oil_with_indicators.csv")

# Use relative path for SQLite database
DB_PATH = os.path.join(get_data_directory(), "market_data.db")
```

This change makes the code more portable and allows it to run in different environments, including Docker containers.

## 2. Improved Error Handling with Retry Mechanisms

### Problem
The original code had basic error handling but lacked robust mechanisms for handling transient errors, particularly in network operations like fetching market data.

### Solution
Created a new utility module (`utils/retry.py`) that provides retry functionality with exponential backoff:

```python
@retry(max_tries=3, delay=2.0, backoff=2.0, exceptions=[Exception], logger_name="fetch_historical_data")
def fetch_and_save_data(symbol: str = "CL=F", period: str = "1y", interval: str = "1h", data_path: Optional[str] = None) -> bool:
    # Function implementation with improved error handling
```

The retry utility includes:
- Configurable retry attempts, delay, and backoff
- Support for specific exception types
- Random jitter to prevent thundering herd problems
- Comprehensive logging of retry attempts
- Two decorators: `retry` for exception-based retries and `retry_with_result` for result validation-based retries

This improvement makes the data fetching process more resilient to transient network errors and API failures.

## 3. Added Docker Support

### Problem
The original codebase lacked containerization support, making it difficult to deploy consistently across different environments.

### Solution
Added Docker support with the following files:

1. **Dockerfile**: Defines the container image with all necessary dependencies:
   - Python 3.9 base image
   - Installation of all Python dependencies
   - Installation of TA-Lib with its system dependencies
   - Proper directory structure and environment setup

2. **docker-compose.yml**: Provides easy deployment with two service configurations:
   - `trading-bot`: For running the bot in paper or live trading mode
   - `backtesting`: For running backtests with specific date ranges

3. **.dockerignore**: Optimizes Docker builds by excluding unnecessary files:
   - Git files
   - Python cache files
   - Logs and data directories
   - Development environment files

Benefits of Docker support:
- Consistent environment across development and production
- Easy deployment with simple commands
- Isolation of the application and its dependencies
- Support for different operational modes (trading vs. backtesting)
- Volume mounting for persistent data and logs

## Testing

All improvements have been tested with dedicated test modules:

1. **test_file_paths.py**: Verifies that hardcoded paths have been properly replaced
2. **test_retry.py**: Tests the retry functionality with various scenarios
3. **test_docker.py**: Validates the Docker configuration files

## Next Steps

While these improvements address critical issues in the codebase, further enhancements could include:

1. **Performance Optimization**: Implement caching and asynchronous processing
2. **Code Organization**: Apply dependency injection and further modularization
3. **Testing**: Add more comprehensive unit and integration tests
4. **Documentation**: Enhance API documentation and usage examples
5. **Feature Enhancements**: Add real-time data processing and advanced analytics
6. **Security Improvements**: Implement secure configuration handling

## Usage

### Running with Docker

To run the trading bot using Docker:

```bash
# Start the trading bot in paper trading mode
docker-compose up trading-bot

# Run backtesting
docker-compose --profile backtest up backtesting

# Build and start with fresh containers
docker-compose up --build trading-bot
```

### Running Tests

To run the tests:

```bash
# Install required dependencies
pip install -r requirements.txt

# Run all tests
python -m unittest discover -s tests

# Run specific test module
python -m unittest tests.test_retry
```
