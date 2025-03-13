"""
Agent Manager Module

This module coordinates the different agents in the trading system:
- Data Fetching Agent
- Sentiment Analysis Agent
- Technical Analysis Agent
- Strategy Agent
- Risk Management Agent
- Trade Execution Agent

The Agent Manager is responsible for:
1. Initializing all agents
2. Coordinating data flow between agents
3. Scheduling agent execution
4. Handling errors and retries
5. Logging agent activities
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
    MarketData, SentimentResult, TradingSignal, 
    TradeExecution, Position, Portfolio, BacktestResult
)

# Import utility functions
from utils import get_data_directory, get_db_connection, setup_logger

# Import agents
# Import agents
from scripts.data_fetch.data_fetch import fetch_market_data, convert_to_market_data
from scripts.sentiment.sentiment_analysis import SentimentAnalyzer
from scripts.strategy.strategy import TradingStrategy, generate_signals_with_ml
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
        self.market_data_queue = queue.Queue()
        self.sentiment_queue = queue.Queue()
        self.signal_queue = queue.Queue()
        self.trade_queue = queue.Queue()
        
        # Initialize agents
        self.data_agent = None
        self.sentiment_agent = None
        self.strategy_agent = None
        self.risk_agent = None
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
        
        # Initialize sentiment agent
        try:
            self.sentiment_agent = SentimentAnalyzer()
            logger.info("Sentiment Agent initialized")
        except Exception as e:
            logger.error(f"Error initializing Sentiment Agent: {e}")
            self.sentiment_agent = None
        
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
    
    def fetch_market_data(self, symbol: str = "CL=F", days: int = 30) -> List[MarketData]:
        """
        Fetch market data for the specified symbol and time period.
        
        Args:
            symbol (str, optional): Symbol to fetch data for. Defaults to "CL=F" (WTI Crude Oil).
            days (int, optional): Number of days of historical data to fetch. Defaults to 30.
            
        Returns:
            List[MarketData]: List of MarketData objects.
        """
        logger.info(f"Fetching market data for {symbol} for the past {days} days...")
        
        try:
            # Fetch market data
            df = fetch_market_data(days=days, symbol=symbol)
            if df is None:
                logger.error("Failed to fetch market data")
                return []
            
            # Calculate indicators
            df_with_indicators = calculate_indicators(df)
            
            # Convert to MarketData objects
            market_data_list = convert_to_market_data(df_with_indicators)
            
            logger.info(f"Fetched {len(market_data_list)} market data records")
            
            # Put market data in queue for other agents
            for data in market_data_list:
                self.market_data_queue.put(data)
            
            return market_data_list
        except Exception as e:
            logger.error(f"Error fetching market data: {e}")
            return []
    
    def analyze_sentiment(self) -> List[SentimentResult]:
        """
        Run sentiment analysis on news articles.
        
        Returns:
            List[SentimentResult]: List of SentimentResult objects.
        """
        logger.info("Running sentiment analysis...")
        
        if self.sentiment_agent is None:
            logger.error("Sentiment Agent not initialized")
            return []
        
        try:
            # Run sentiment analysis
            sentiment_results = self.sentiment_agent.run()
            
            logger.info(f"Generated {len(sentiment_results)} sentiment results")
            
            # Put sentiment results in queue for other agents
            for result in sentiment_results:
                self.sentiment_queue.put(result)
            
            return sentiment_results
        except Exception as e:
            logger.error(f"Error running sentiment analysis: {e}")
            return []
    
    def generate_trading_signals(self, use_sentiment: bool = True) -> List[TradingSignal]:
        """
        Generate trading signals based on market data and sentiment analysis.
        
        Args:
            use_sentiment (bool, optional): Whether to use sentiment analysis. Defaults to True.
            
        Returns:
            List[TradingSignal]: List of TradingSignal objects.
        """
        logger.info("Generating trading signals...")
        
        if self.strategy_agent is None:
            logger.error("Strategy Agent not initialized")
            return []
        
        try:
            # Get market data from queue
            market_data_list = []
            while not self.market_data_queue.empty():
                market_data_list.append(self.market_data_queue.get())
            
            if not market_data_list:
                logger.warning("No market data available for signal generation")
                return []
            
            # Convert MarketData objects to dictionary format expected by strategy
            data = []
            for md in market_data_list:
                data.append({
                    'Date': md.date,
                    'Open': md.open,
                    'High': md.high,
                    'Low': md.low,
                    'Close': md.close,
                    'Volume': md.volume
                })
            
            # Generate signals
            signals = generate_signals_with_ml(data, use_sentiment=use_sentiment)
            
            logger.info(f"Generated {len(signals)} trading signals")
            
            # Put signals in queue for other agents
            for signal in signals:
                self.signal_queue.put(signal)
            
            return signals
        except Exception as e:
            logger.error(f"Error generating trading signals: {e}")
            return []
    
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
                        symbol="CL=F",
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
                        logger.info(f"Executed BUY trade for CL=F at ${signal.price:.2f}")
                    else:
                        logger.error("Failed to execute BUY trade")
                
                elif signal.signal == -1:  # SELL
                    # Create a TradeExecution object
                    trade = TradeExecution(
                        date=datetime.now(),
                        symbol="CL=F",
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
                        logger.info(f"Executed SELL trade for CL=F at ${signal.price:.2f}")
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
        Run a complete trading cycle:
        1. Fetch market data
        2. Analyze sentiment
        3. Generate trading signals
        4. Execute trades
        """
        logger.info("Starting trading cycle...")
        
        # Fetch market data
        market_data = self.fetch_market_data()
        if not market_data:
            logger.error("Failed to fetch market data. Aborting trading cycle.")
            return
        
        # Analyze sentiment
        sentiment_results = self.analyze_sentiment()
        
        # Generate trading signals
        signals = self.generate_trading_signals(use_sentiment=bool(sentiment_results))
        if not signals:
            logger.warning("No trading signals generated. Skipping trade execution.")
            return
        
        # Execute trades
        executed_trades = self.execute_trades()
        
        # Update portfolio
        if self.execution_agent:
            self.execution_agent.display_portfolio()
        
        logger.info("Trading cycle completed")
    
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
