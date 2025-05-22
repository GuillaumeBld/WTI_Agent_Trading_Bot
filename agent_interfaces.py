# agent_interfaces.py
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List, Dict, Any, Union

class TradingSignal(BaseModel):
    date: datetime
    price: float
    signal: int          # 1 for BUY, -1 for SELL, 0 for HOLD
    confidence: float    # Confidence level (0.0 to 1.0)
    limit_price: Optional[float] = None  # Optional limit price for order execution
    source: str = "default"  # Indicates which agent generated the signal

    class Config:
        orm_mode = True

class MarketData(BaseModel):
    date: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int
    
    class Config:
        orm_mode = True

class SentimentResult(BaseModel):
    date: datetime
    source: str
    sentiment_score: float  # Range from -1.0 (negative) to 1.0 (positive)
    confidence: float       # Confidence level (0.0 to 1.0)
    text_snippet: Optional[str] = None  # Optional snippet of the analyzed text
    
    class Config:
        orm_mode = True

class SatelliteData(BaseModel):
    date: datetime
    location: str
    metric_type: str  # e.g., "oil_storage", "tanker_count"
    value: float
    confidence: float  # Confidence level (0.0 to 1.0)
    
    class Config:
        orm_mode = True

class TradeExecution(BaseModel):
    date: datetime
    symbol: str
    order_type: str  # "BUY", "SELL"
    quantity: float
    price: float
    limit_price: Optional[float] = None
    status: str  # "PENDING", "EXECUTED", "FAILED"
    execution_id: Optional[str] = None
    
    class Config:
        orm_mode = True

class Position(BaseModel):
    symbol: str
    quantity: float
    entry_price: float
    current_price: float
    
    @property
    def market_value(self) -> float:
        return self.quantity * self.current_price
    
    @property
    def profit_loss(self) -> float:
        return self.quantity * (self.current_price - self.entry_price)
    
    @property
    def profit_loss_percent(self) -> float:
        return (self.current_price - self.entry_price) / self.entry_price * 100

class Portfolio(BaseModel):
    date: datetime
    cash: float
    positions: List[Position]
    
    @property
    def total_value(self) -> float:
        positions_value = sum(position.market_value for position in self.positions)
        return self.cash + positions_value
    
    @property
    def total_profit_loss(self) -> float:
        return sum(position.profit_loss for position in self.positions)

class RiskParameters(BaseModel):
    max_position_size: float  # Maximum size of a single position as % of portfolio
    max_portfolio_risk: float  # Maximum total risk as % of portfolio
    stop_loss_percent: float  # Default stop loss as % of entry price
    take_profit_percent: float  # Default take profit as % of entry price
    
    class Config:
        orm_mode = True

class BacktestResult(BaseModel):
    start_date: datetime
    end_date: datetime
    initial_capital: float
    final_capital: float
    total_trades: int
    winning_trades: int
    losing_trades: int
    sharpe_ratio: float
    max_drawdown: float
    
    @property
    def win_rate(self) -> float:
        return self.winning_trades / self.total_trades if self.total_trades > 0 else 0
    
    @property
    def profit_loss(self) -> float:
        return self.final_capital - self.initial_capital
    
    @property
    def profit_loss_percent(self) -> float:
        return (self.final_capital - self.initial_capital) / self.initial_capital * 100
    
    class Config:
        orm_mode = True


class OptionsContractData(BaseModel):
    strike_price: float
    contract_type: str  # e.g., "call" or "put"
    implied_volatility: Optional[float]
    volume: Optional[int]
    open_interest: Optional[int]
    delta: Optional[float]
    gamma: Optional[float]
    theta: Optional[float]
    vega: Optional[float]
    last_traded_price: Optional[float]

    class Config:
        orm_mode = True


class OptionsChainData(BaseModel):
    underlying_symbol: str  # e.g., "BTC"
    spot_price: float  # current price of the underlying asset
    expiry_date: datetime
    contracts: List[OptionsContractData]  # a list of OptionsContractData objects

    class Config:
        orm_mode = True


class VolatilitySmirkResult(BaseModel):
    date: datetime
    underlying_symbol: str
    expiry_date: datetime
    skewness_metric: Optional[float]  # e.g., ratio of OTM call IV to OTM put IV, or slope of IV curve
    sentiment_label: str  # e.g., "bullish", "bearish", "neutral"
    confidence: float  # confidence in the sentiment_label, 0.0 to 1.0
    details: Optional[Dict[str, Any]]  # for any additional parameters or raw data

    class Config:
        orm_mode = True
