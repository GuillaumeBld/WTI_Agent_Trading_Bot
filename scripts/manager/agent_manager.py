"""
Agent Manager Module for BTC Volatility Smirk Trading Bot

This module coordinates the different agents in the trading system:
- Data Fetching Agent (for BTC Options Data)
- Volatility Smirk Analysis Agent
- Strategy Agent (interpreting smirk analysis for trading signals)
- Risk Management Agent (integrated within trade execution)
- Trade Execution Agent

The Agent Manager is responsible for:
1. Initializing all relevant agents.
2. Coordinating data flow between agents (options data -> smirk analysis -> strategy).
3. Scheduling agent execution.
4. Handling errors and retries.
5. Logging agent activities.
"""

import os
import time
import logging
import threading
import queue
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union, Callable

# Import agent interfaces
from agent_interfaces import (
    MarketData, TradingSignal, TradeExecution, Position, Portfolio, BacktestResult,
    OptionsChainData, VolatilitySmirkResult # Added these
)

# Import utility functions
from utils import get_data_directory, get_db_connection, setup_logger

# Import agents
from scripts.data_fetch.data_fetch import fetch_market_data, convert_to_market_data
# fetch_market_data will be kept for non-BTC, convert_to_market_data for OHLCV
from scripts.data_fetch.btc_options_fetch import fetch_btc_options_data # Added
from scripts.volatility_analysis.smirk_analyzer import SmirkAnalyzer # Added
from scripts.strategy.strategy import TradingStrategy # generate_signals_with_ml might be removed later
from scripts.risk.trade_execution import InvestmentTracker, record_trade
from scripts.indicators.indicators import calculate_indicators

# Set up logging
logger = setup_logger("agent_manager", os.path.join("logs", "agent_manager.log"))

class AgentManager:
    """
    Agent Manager class that coordinates all trading agents.
    """
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the Agent Manager with configuration.
        
        Args:
            config (Dict[str, Any], optional): Configuration dictionary.
        """
        self.config = config or {}
        self.data_dir = get_data_directory()
        self.db_path = os.path.join(self.data_dir, "market_data.db")
        
        # Initialize message queues for inter-agent communication
        self.options_data_queue = queue.Queue() # Renamed from market_data_queue
        self.volatility_analysis_queue = queue.Queue() # Renamed from sentiment_queue
        self.signal_queue = queue.Queue()
        self.trade_queue = queue.Queue()
        
        # Initialize agents
        self.data_agent = None # This specific agent might be removed if fetching is done directly
        self.smirk_analyzer_agent = None # Changed from sentiment_agent
        self.strategy_agent = None
        self.risk_agent = None # This specific agent might be removed if risk management is part of execution
        self.execution_agent = None
        
        # Initialize agent threads
        self.threads = {}
        self.running = False
        
        # Initialize portfolio tracker
        self.portfolio_tracker = InvestmentTracker()
        
        logger.info("Agent Manager initialized")
    
    def initialize_agents(self):
        """
        Initialize all trading agents.
        """
        logger.info("Initializing agents...")
        
        # Initialize Smirk Analyzer agent (formerly sentiment agent)
        try:
            self.smirk_analyzer_agent = SmirkAnalyzer()
            logger.info("Smirk Analyzer Agent initialized")
        except Exception as e:
            logger.error(f"Error initializing Smirk Analyzer Agent: {e}")
            self.smirk_analyzer_agent = None
        
        # Initialize strategy agent
        try:
            self.strategy_agent = TradingStrategy()
            logger.info("Strategy Agent initialized")
        except Exception as e:
            logger.error(f"Error initializing Strategy Agent: {e}")
            self.strategy_agent = None
        
        # Initialize execution agent
        try:
            self.execution_agent = self.portfolio_tracker
            logger.info("Execution Agent initialized")
        except Exception as e:
            logger.error(f"Error initializing Execution Agent: {e}")
            self.execution_agent = None
        
        logger.info("All agents initialized")
    
    def fetch_data_for_symbol(self, symbol: str, days: int = 30) -> None:
        """
        Fetches appropriate data (OHLCV or Options) based on the symbol.
        Puts MarketData (for OHLCV) or OptionsChainData into respective queues.
        """
        logger.info(f"Fetching data for {symbol}...")
        if symbol.upper() == "BTC-USD": # Check against configured BTC symbol
            try:
                # Fetch options data using the new fetcher
                # The API key and expiries should come from self.config
                api_key_env_var = self.config.get('volatility_analysis', {}).get('api_key_env_var', 'OPTIONS_API_KEY')
                api_key = os.environ.get(api_key_env_var)
                if not api_key:
                    logger.error(f"API key environment variable {api_key_env_var} not set.")
                    return

                monitored_expiries = self.config.get('volatility_analysis', {}).get('monitored_expiries', ["1D", "7D"])
                
                options_chain_list = fetch_btc_options_data(api_key=api_key, symbol=symbol, expiries=monitored_expiries)
                
                if not options_chain_list:
                    logger.error(f"Failed to fetch BTC options data for {symbol}")
                    return

                for options_chain in options_chain_list:
                    self.options_data_queue.put(options_chain) # Use the renamed queue
                logger.info(f"Fetched and queued {len(options_chain_list)} BTC options chains for {symbol}")

            except Exception as e:
                logger.error(f"Error fetching BTC options data for {symbol}: {e}")
        else: # Existing logic for OHLCV data for non-BTC assets
            try:
                df = fetch_market_data(days=days, symbol=symbol) # Original OHLCV fetcher
                if df is None:
                    logger.error(f"Failed to fetch market data for {symbol}")
                    return
                
                df_with_indicators = calculate_indicators(df) # Keep for non-BTC
                market_data_list = convert_to_market_data(df_with_indicators)
                
                for data_item in market_data_list: # Renamed 'data' to 'data_item' to avoid conflict
                    # OHLCV data still goes to a queue. If AgentManager only handles one type at a time,
                    # this queue might be the same options_data_queue or a different one.
                    # For simplicity, let's assume non-BTC data isn't processed further in this BTC-focused plan.
                    # Or, ensure the old market_data_queue is used for this path if needed.
                    # For this plan, let's put it in a generic queue that won't be picked up by smirk analysis.
                    # To avoid error, we can use self.options_data_queue but it will be mixed type.
                    # A better solution would be separate queues or a flag in the queued item.
                    # For now, let's assume this path (non-BTC) is not the primary focus of the trading cycle.
                    # We'll put it in 'options_data_queue' but the processor needs to be careful.
                    # A cleaner way: have a separate market_data_queue for OHLCV if both are active.
                    # Let's assume for this refactor, if symbol is not BTC, this queue won't be used by new logic.
                    self.options_data_queue.put(data_item) # This will mix types if not careful.

                logger.info(f"Fetched and queued {len(market_data_list)} OHLCV records for {symbol}")
            except Exception as e:
                logger.error(f"Error fetching market data for {symbol}: {e}")

    def perform_volatility_analysis(self) -> List[VolatilitySmirkResult]:
        logger.info("Performing volatility smirk analysis...")
        
        if self.smirk_analyzer_agent is None:
            logger.error("Smirk Analyzer Agent not initialized")
            return []
        
        results = []
        # Process all OptionsChainData items from the queue
        while not self.options_data_queue.empty():
            options_data = self.options_data_queue.get()
            if not isinstance(options_data, OptionsChainData): # Skip if not options data
                logger.warning(f"Skipping item of type {type(options_data)} in options_data_queue during smirk analysis.")
                continue

            try:
                # Pass relevant config to smirk analyzer
                smirk_config = self.config.get('volatility_analysis', {})
                smirk_result = self.smirk_analyzer_agent.analyze_smirk(options_data, config=smirk_config)
                if smirk_result:
                    results.append(smirk_result)
                    self.volatility_analysis_queue.put(smirk_result) # Use renamed queue
            except Exception as e:
                logger.error(f"Error during smirk analysis for {options_data.underlying_symbol} expiry {options_data.expiry_date}: {e}")
        
        logger.info(f"Generated {len(results)} volatility smirk results")
        return results
    
    def generate_trading_signals(self) -> List[TradingSignal]: # Removed use_sentiment argument
        logger.info("Generating trading signals from volatility analysis...")
        
        if self.strategy_agent is None:
            logger.error("Strategy Agent not initialized")
            return []

        signals = []
        # strategy_config = self.config.get('strategy', {}) # Not used directly here, but passed to smirk

        while not self.volatility_analysis_queue.empty():
            smirk_result = self.volatility_analysis_queue.get()
            try:
                # Extract spot price used during smirk analysis (assuming it's in details)
                spot_price = smirk_result.details.get("spot_price_at_analysis")
                if not spot_price:
                    logger.warning(f"Spot price not found in SmirkResult details for {smirk_result.underlying_symbol}. Cannot generate signal.")
                    continue

                # Pass strategy config (entire self.config for simplicity, strategy can pick what it needs)
                signal = self.strategy_agent.generate_signals_from_smirk(spot_price, smirk_result, config=self.config)
                if signal:
                    signals.append(signal)
                    self.signal_queue.put(signal)
            except Exception as e:
                logger.error(f"Error generating trading signal from smirk result for {smirk_result.underlying_symbol}: {e}")
        
        logger.info(f"Generated {len(signals)} trading signals")
        return signals
    
    def execute_trades(self, max_trades: int = 1) -> List[TradeExecution]:
        """
        Execute trades based on trading signals.
        
        Args:
            max_trades (int, optional): Maximum number of trades to execute. Defaults to 1.
            
        Returns:
            List[TradeExecution]: List of TradeExecution objects.
        """
        logger.info(f"Executing up to {max_trades} trades...")
        
        if self.execution_agent is None:
            logger.error("Execution Agent not initialized")
            return []
        
        try:
            # Get signals from queue
            signals = []
            while not self.signal_queue.empty() and len(signals) < max_trades:
                signals.append(self.signal_queue.get())
            
            if not signals:
                logger.warning("No trading signals available for trade execution")
                return []
            
            # Sort signals by confidence
            signals.sort(key=lambda x: x.confidence, reverse=True)
            
            # Execute trades
            executed_trades = []
            for signal in signals[:max_trades]:
                if signal.signal == 1:  # BUY
                    # Create a TradeExecution object
                    trade = TradeExecution(
                        date=datetime.now(),
                        symbol=self.config.get('trading', {}).get('symbol', 'BTC-USD'), # Use configured symbol
                        order_type="BUY",
                        quantity=1.0,  # Will be calculated by the execution agent
                        price=signal.price,
                        status="PENDING"
                    )
                    
                    # Execute the trade
                    # In a real system, this would call a broker API
                    # For now, we just record the trade
                    trade_id = record_trade(trade, f"Signal confidence: {signal.confidence}")
                    
                    if trade_id:
                        trade.status = "EXECUTED"
                        trade.execution_id = str(trade_id)
                        executed_trades.append(trade)
                        logger.info(
                            f"Executed BUY trade for {trade.symbol} at ${signal.price:.2f}"
                        )
                    else:
                        logger.error("Failed to execute BUY trade")
                
                elif signal.signal == -1:  # SELL
                    # Create a TradeExecution object
                    trade = TradeExecution(
                        date=datetime.now(),
                        symbol=self.config.get('trading', {}).get('symbol', 'BTC-USD'), # Use configured symbol
                        order_type="SELL",
                        quantity=1.0,  # Will be calculated by the execution agent
                        price=signal.price,
                        status="PENDING"
                    )
                    
                    # Execute the trade
                    trade_id = record_trade(trade, f"Signal confidence: {signal.confidence}")
                    
                    if trade_id:
                        trade.status = "EXECUTED"
                        trade.execution_id = str(trade_id)
                        executed_trades.append(trade)
                        logger.info(
                            f"Executed SELL trade for {trade.symbol} at ${signal.price:.2f}"
                        )
                    else:
                        logger.error("Failed to execute SELL trade")
            
            # Put executed trades in queue for other agents
            for trade in executed_trades:
                self.trade_queue.put(trade)
            
            return executed_trades
        except Exception as e:
            logger.error(f"Error executing trades: {e}")
            return []
    
    def run_trading_cycle(self):
        """
        Run a complete trading cycle using the configured symbol and data processing path.
        """
        logger.info("Starting trading cycle...")
        
        current_symbol = self.config.get('trading', {}).get('symbol', 'BTC-USD')
        days_history = self.config.get('data_fetch', {}).get('days', 30) # Used for non-BTC OHLCV

        # Step 1: Fetch data for the current symbol
        # This will put OptionsChainData or MarketData into self.options_data_queue
        self.fetch_data_for_symbol(symbol=current_symbol, days=days_history) 
        
        signals = []
        if current_symbol.upper() == "BTC-USD":
            # Step 2: Perform volatility analysis if it's BTC
            # This consumes from self.options_data_queue and puts VolatilitySmirkResult into self.volatility_analysis_queue
            self.perform_volatility_analysis()
            
            # Step 3: Generate trading signals from volatility analysis
            # This consumes from self.volatility_analysis_queue and puts TradingSignal into self.signal_queue
            signals = self.generate_trading_signals() 
        else:
            # Placeholder for non-BTC asset path if it were to be fully supported alongside BTC.
            # This might involve a different analysis method and signal generation path.
            # For the current plan focused on BTC, this path results in no signals.
            logger.info(f"Symbol {current_symbol} is not BTC-USD. Standard OHLCV data was fetched. " +
                        "Skipping BTC-specific volatility/smirk-based signal generation for this cycle.")
            # To make this path work for other assets you would need to:
            # 1. Ensure OHLCV MarketData from options_data_queue is processed by a different analysis method.
            # 2. That method puts its results (e.g. old SentimentResult) to a queue.
            # 3. generate_trading_signals (or another method) consumes that strategy.
            # This is out of scope for the current BTC refactoring.
            pass # No signals generated for non-BTC in this flow.

        # Step 4: Execute trades if signals were generated
        if not signals:
            logger.warning("No trading signals generated for the current cycle. Skipping trade execution.")
        else:
            # This consumes from self.signal_queue
            max_trades_to_execute = self.config.get('trading', {}).get('max_concurrent_trades', 1)
            self.execute_trades(max_trades=max_trades_to_execute) 
        
        # Display portfolio status
        if self.execution_agent:
            self.execution_agent.display_portfolio()
        
        logger.info("Trading cycle completed.")
    
    def start_automated_trading(self, interval: int = 3600):
        """
        Start automated trading with the specified interval.
        
        Args:
            interval (int, optional): Interval between trading cycles in seconds. Defaults to 3600 (1 hour).
        """
        logger.info(f"Starting automated trading with interval {interval} seconds...")
        
        self.initialize_agents()
        self.running = True
        
        def trading_loop():
            while self.running:
                try:
                    self.run_trading_cycle()
                    time.sleep(interval)
                except Exception as e:
                    logger.error(f"Error in trading loop: {e}")
                    time.sleep(10)  # Wait before retrying after an error
        
        # Start trading loop in a separate thread
        self.threads["trading_loop"] = threading.Thread(target=trading_loop)
        self.threads["trading_loop"].daemon = True
        self.threads["trading_loop"].start()
        
        logger.info("Automated trading started")
    
    def stop_automated_trading(self):
        """
        Stop automated trading.
        """
        logger.info("Stopping automated trading...")
        
        self.running = False
        
        # Wait for threads to finish
        for thread_name, thread in self.threads.items():
            if thread.is_alive():
                thread.join(timeout=5)
                logger.info(f"Thread {thread_name} stopped")
        
        logger.info("Automated trading stopped")
    
    def run_backtest(self, start_date: datetime, end_date: datetime) -> BacktestResult:
        """
        Run a backtest for the specified time period.
        
        Args:
            start_date (datetime): Start date for the backtest.
            end_date (datetime): End date for the backtest.
            
        Returns:
            BacktestResult: Backtest result object.
        """
        logger.info(f"Running backtest from {start_date} to {end_date}...")
        
        # Initialize backtest result
        backtest_result = BacktestResult(
            start_date=start_date,
            end_date=end_date,
            initial_capital=100000.0,
            final_capital=100000.0,
            total_trades=0,
            winning_trades=0,
            losing_trades=0,
            sharpe_ratio=0.0,
            max_drawdown=0.0
        )
        
        # TODO: Implement backtest logic
        
        logger.info("Backtest completed")
        
        return backtest_result

def main():
    """
    Main function to run the Agent Manager.
    """
    logger.info("Starting Agent Manager...")
    
    # Create Agent Manager
    manager = AgentManager()
    
    # Initialize agents
    manager.initialize_agents()
    
    # Run a trading cycle
    manager.run_trading_cycle()
    
    logger.info("Agent Manager execution completed")

if __name__ == "__main__":
    main()
