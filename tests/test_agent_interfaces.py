"""
Tests for agent_interfaces.py

This module contains tests for the agent interfaces defined in agent_interfaces.py.
"""

import unittest
from datetime import datetime
from agent_interfaces import (
    TradingSignal, MarketData, SentimentResult, SatelliteData,
    TradeExecution, Position, Portfolio, RiskParameters, BacktestResult
)

class TestTradingSignal(unittest.TestCase):
    """Tests for the TradingSignal class."""
    
    def test_trading_signal_creation(self):
        """Test creating a TradingSignal object."""
        signal = TradingSignal(
            date=datetime.now(),
            price=70.5,
            signal=1,
            confidence=0.8,
            source="test"
        )
        self.assertEqual(signal.price, 70.5)
        self.assertEqual(signal.signal, 1)
        self.assertEqual(signal.confidence, 0.8)
        self.assertEqual(signal.source, "test")
        self.assertIsNone(signal.limit_price)

    def test_trading_signal_with_limit_price(self):
        """Test creating a TradingSignal object with a limit price."""
        signal = TradingSignal(
            date=datetime.now(),
            price=70.5,
            signal=1,
            confidence=0.8,
            limit_price=71.0,
            source="test"
        )
        self.assertEqual(signal.price, 70.5)
        self.assertEqual(signal.limit_price, 71.0)

class TestMarketData(unittest.TestCase):
    """Tests for the MarketData class."""
    
    def test_market_data_creation(self):
        """Test creating a MarketData object."""
        data = MarketData(
            date=datetime.now(),
            open=70.0,
            high=71.0,
            low=69.0,
            close=70.5,
            volume=1000
        )
        self.assertEqual(data.open, 70.0)
        self.assertEqual(data.high, 71.0)
        self.assertEqual(data.low, 69.0)
        self.assertEqual(data.close, 70.5)
        self.assertEqual(data.volume, 1000)

class TestSentimentResult(unittest.TestCase):
    """Tests for the SentimentResult class."""
    
    def test_sentiment_result_creation(self):
        """Test creating a SentimentResult object."""
        result = SentimentResult(
            date=datetime.now(),
            source="news",
            sentiment_score=0.8,
            confidence=0.9,
            text_snippet="Positive news about oil prices."
        )
        self.assertEqual(result.source, "news")
        self.assertEqual(result.sentiment_score, 0.8)
        self.assertEqual(result.confidence, 0.9)
        self.assertEqual(result.text_snippet, "Positive news about oil prices.")

class TestSatelliteData(unittest.TestCase):
    """Tests for the SatelliteData class."""
    
    def test_satellite_data_creation(self):
        """Test creating a SatelliteData object."""
        data = SatelliteData(
            date=datetime.now(),
            location="cushing_oklahoma",
            metric_type="oil_storage",
            value=0.75,
            confidence=0.8
        )
        self.assertEqual(data.location, "cushing_oklahoma")
        self.assertEqual(data.metric_type, "oil_storage")
        self.assertEqual(data.value, 0.75)
        self.assertEqual(data.confidence, 0.8)

class TestTradeExecution(unittest.TestCase):
    """Tests for the TradeExecution class."""
    
    def test_trade_execution_creation(self):
        """Test creating a TradeExecution object."""
        trade = TradeExecution(
            date=datetime.now(),
            symbol="CL=F",
            order_type="BUY",
            quantity=1.0,
            price=70.5,
            status="EXECUTED"
        )
        self.assertEqual(trade.symbol, "CL=F")
        self.assertEqual(trade.order_type, "BUY")
        self.assertEqual(trade.quantity, 1.0)
        self.assertEqual(trade.price, 70.5)
        self.assertEqual(trade.status, "EXECUTED")
        self.assertIsNone(trade.limit_price)
        self.assertIsNone(trade.execution_id)

class TestPosition(unittest.TestCase):
    """Tests for the Position class."""
    
    def test_position_creation(self):
        """Test creating a Position object."""
        position = Position(
            symbol="CL=F",
            quantity=1.0,
            entry_price=70.0,
            current_price=71.0
        )
        self.assertEqual(position.symbol, "CL=F")
        self.assertEqual(position.quantity, 1.0)
        self.assertEqual(position.entry_price, 70.0)
        self.assertEqual(position.current_price, 71.0)
    
    def test_position_calculations(self):
        """Test position calculations."""
        position = Position(
            symbol="CL=F",
            quantity=2.0,
            entry_price=70.0,
            current_price=71.0
        )
        self.assertEqual(position.market_value, 142.0)  # 2.0 * 71.0
        self.assertEqual(position.profit_loss, 2.0)  # 2.0 * (71.0 - 70.0)
        self.assertAlmostEqual(position.profit_loss_percent, 1.4285714285714286)  # (71.0 - 70.0) / 70.0 * 100

class TestPortfolio(unittest.TestCase):
    """Tests for the Portfolio class."""
    
    def test_portfolio_creation(self):
        """Test creating a Portfolio object."""
        positions = [
            Position(symbol="CL=F", quantity=1.0, entry_price=70.0, current_price=71.0),
            Position(symbol="BZ=F", quantity=2.0, entry_price=75.0, current_price=76.0)
        ]
        portfolio = Portfolio(
            date=datetime.now(),
            cash=10000.0,
            positions=positions
        )
        self.assertEqual(portfolio.cash, 10000.0)
        self.assertEqual(len(portfolio.positions), 2)
    
    def test_portfolio_calculations(self):
        """Test portfolio calculations."""
        positions = [
            Position(symbol="CL=F", quantity=1.0, entry_price=70.0, current_price=71.0),
            Position(symbol="BZ=F", quantity=2.0, entry_price=75.0, current_price=76.0)
        ]
        portfolio = Portfolio(
            date=datetime.now(),
            cash=10000.0,
            positions=positions
        )
        self.assertEqual(portfolio.total_value, 10000.0 + 71.0 + 2.0 * 76.0)  # cash + CL=F value + BZ=F value
        self.assertEqual(portfolio.total_profit_loss, 1.0 + 2.0)  # CL=F P/L + BZ=F P/L

class TestRiskParameters(unittest.TestCase):
    """Tests for the RiskParameters class."""
    
    def test_risk_parameters_creation(self):
        """Test creating a RiskParameters object."""
        params = RiskParameters(
            max_position_size=0.05,
            max_portfolio_risk=0.2,
            stop_loss_percent=0.02,
            take_profit_percent=0.05
        )
        self.assertEqual(params.max_position_size, 0.05)
        self.assertEqual(params.max_portfolio_risk, 0.2)
        self.assertEqual(params.stop_loss_percent, 0.02)
        self.assertEqual(params.take_profit_percent, 0.05)

class TestBacktestResult(unittest.TestCase):
    """Tests for the BacktestResult class."""
    
    def test_backtest_result_creation(self):
        """Test creating a BacktestResult object."""
        result = BacktestResult(
            start_date=datetime(2023, 1, 1),
            end_date=datetime(2023, 12, 31),
            initial_capital=100000.0,
            final_capital=110000.0,
            total_trades=100,
            winning_trades=60,
            losing_trades=40,
            sharpe_ratio=1.5,
            max_drawdown=0.1
        )
        self.assertEqual(result.start_date, datetime(2023, 1, 1))
        self.assertEqual(result.end_date, datetime(2023, 12, 31))
        self.assertEqual(result.initial_capital, 100000.0)
        self.assertEqual(result.final_capital, 110000.0)
        self.assertEqual(result.total_trades, 100)
        self.assertEqual(result.winning_trades, 60)
        self.assertEqual(result.losing_trades, 40)
        self.assertEqual(result.sharpe_ratio, 1.5)
        self.assertEqual(result.max_drawdown, 0.1)
    
    def test_backtest_result_calculations(self):
        """Test backtest result calculations."""
        result = BacktestResult(
            start_date=datetime(2023, 1, 1),
            end_date=datetime(2023, 12, 31),
            initial_capital=100000.0,
            final_capital=110000.0,
            total_trades=100,
            winning_trades=60,
            losing_trades=40,
            sharpe_ratio=1.5,
            max_drawdown=0.1
        )
        self.assertEqual(result.win_rate, 0.6)  # 60 / 100
        self.assertEqual(result.profit_loss, 10000.0)  # 110000.0 - 100000.0
        self.assertEqual(result.profit_loss_percent, 10.0)  # (110000.0 - 100000.0) / 100000.0 * 100

if __name__ == "__main__":
    unittest.main()
