"""
AI Analytics Schemas
Data structures for AI-driven analytics, risk scoring, and predictions
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID
from decimal import Decimal
from enum import Enum


class RiskLevel(str, Enum):
    """Risk level classification"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AnomalyType(str, Enum):
    """Types of detected anomalies"""
    VOLUME_SPIKE = "volume_spike"
    LARGE_TRADE = "large_trade"
    RAPID_TRADING = "rapid_trading"
    PRICE_DEVIATION = "price_deviation"
    WASH_TRADING = "wash_trading"
    SPOOFING = "spoofing"
    UNUSUAL_PATTERN = "unusual_pattern"


class AnomalyAlert(BaseModel):
    """Alert for detected anomaly"""
    id: str
    type: AnomalyType
    symbol: str
    user_id: Optional[UUID] = None
    severity: int = Field(ge=1, le=10, description="Severity score 1-10")
    description: str
    detected_at: datetime
    metrics: Dict[str, Any] = {}
    recommendation: Optional[str] = None
    
    class Config:
        from_attributes = True


class RiskScore(BaseModel):
    """Comprehensive risk assessment"""
    user_id: Optional[UUID] = None
    overall_score: float = Field(ge=0, le=10, description="Overall risk score 0-10")
    level: RiskLevel
    factors: Dict[str, float] = Field(default_factory=dict, description="Individual risk factors")
    recommendations: List[str] = Field(default_factory=list)
    calculated_at: datetime
    metrics: Dict[str, Any] = {}
    
    class Config:
        from_attributes = True


class PricePrediction(BaseModel):
    """AI-generated price prediction"""
    symbol: str
    current_price: Decimal
    predicted_price: Decimal
    confidence: float = Field(ge=0, le=1, description="Confidence level 0-1")
    direction: str = Field(description="bullish, bearish, or neutral")
    horizon_minutes: int
    factors: Dict[str, Any] = Field(default_factory=dict, description="Technical indicators used")
    generated_at: datetime
    
    class Config:
        from_attributes = True


class PortfolioPosition(BaseModel):
    """Individual portfolio position"""
    symbol: str
    quantity: Decimal
    avg_price: Decimal
    current_price: Decimal
    value_usd: Decimal
    unrealized_pnl: Optional[Decimal] = None
    unrealized_pnl_percent: Optional[Decimal] = None
    asset_type: Optional[str] = None
    
    class Config:
        from_attributes = True


class TradingMetrics(BaseModel):
    """Comprehensive trading performance metrics"""
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: Decimal
    avg_profit: Decimal
    avg_loss: Decimal
    profit_factor: Decimal
    sharpe_ratio: Decimal
    max_drawdown: Decimal
    avg_hold_time_hours: Decimal
    
    class Config:
        from_attributes = True


class AIInsight(BaseModel):
    """AI-generated insight or recommendation"""
    type: str = Field(description="performance, risk, opportunity, or warning")
    title: str
    description: str
    importance: str = Field(description="low, medium, high, or critical")
    action: Optional[str] = None
    
    class Config:
        from_attributes = True


class PortfolioAnalysis(BaseModel):
    """Complete portfolio analysis"""
    user_id: UUID
    total_value: Decimal
    total_pnl: Decimal
    total_pnl_percent: Decimal
    positions: List[PortfolioPosition]
    metrics: TradingMetrics
    insights: List[AIInsight]
    analyzed_at: datetime
    
    class Config:
        from_attributes = True


class MarketSentiment(BaseModel):
    """Market sentiment analysis"""
    symbol: str
    sentiment: str = Field(description="bullish, bearish, neutral, etc.")
    score: int = Field(ge=0, le=100, description="Sentiment score 0-100")
    buy_pressure: float
    sell_pressure: float
    volume_trend: str
    price_trend: str
    analyzed_at: datetime
    
    class Config:
        from_attributes = True


# Request/Response models
class AnomalyDetectionRequest(BaseModel):
    """Request for anomaly detection"""
    user_id: Optional[UUID] = None
    symbol: Optional[str] = None
    lookback_hours: int = Field(default=24, ge=1, le=168)


class RiskScoreRequest(BaseModel):
    """Request for risk score calculation"""
    user_id: UUID


class PricePredictionRequest(BaseModel):
    """Request for price prediction"""
    symbol: str
    horizon_minutes: int = Field(default=60, ge=5, le=1440)


class PortfolioAnalysisRequest(BaseModel):
    """Request for portfolio analysis"""
    user_id: UUID


class MarketSentimentRequest(BaseModel):
    """Request for market sentiment analysis"""
    symbol: str


class AIAnalyticsSummary(BaseModel):
    """Summary of AI analytics for dashboard"""
    risk_score: Optional[RiskScore] = None
    recent_anomalies: List[AnomalyAlert] = []
    predictions: Dict[str, PricePrediction] = {}
    sentiment: Dict[str, MarketSentiment] = {}
    insights: List[AIInsight] = []
    generated_at: datetime
    
    class Config:
        from_attributes = True


class ComplianceAlert(BaseModel):
    """Compliance-related alert"""
    id: str
    type: str
    severity: str
    description: str
    regulation: Optional[str] = None
    action_required: str
    deadline: Optional[datetime] = None
    detected_at: datetime
    
    class Config:
        from_attributes = True


class AMLScreeningResult(BaseModel):
    """Anti-Money Laundering screening result"""
    user_id: UUID
    status: str = Field(description="clear, flagged, or blocked")
    risk_indicators: List[str] = []
    suspicious_patterns: List[Dict[str, Any]] = []
    recommendation: str
    screened_at: datetime
    
    class Config:
        from_attributes = True

