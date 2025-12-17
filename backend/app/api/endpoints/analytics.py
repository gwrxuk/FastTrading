"""
AI Analytics API Endpoints
AI-driven financial analysis, risk scoring, anomaly detection, and predictions
"""
from datetime import datetime
from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
import redis.asyncio as redis

from app.database import get_db, get_redis
from app.api.deps import get_current_user
from app.models.user import User
from app.services.ai_analytics import ai_analytics_service
from app.schemas.analytics import (
    AnomalyAlert,
    AnomalyDetectionRequest,
    RiskScore,
    RiskScoreRequest,
    PricePrediction,
    PricePredictionRequest,
    PortfolioAnalysis,
    PortfolioAnalysisRequest,
    MarketSentiment,
    MarketSentimentRequest,
    AIAnalyticsSummary,
    AIInsight,
)

router = APIRouter()


@router.get("/anomalies", response_model=List[AnomalyAlert])
async def detect_anomalies(
    symbol: Optional[str] = Query(None, description="Filter by trading pair"),
    lookback_hours: int = Query(24, ge=1, le=168, description="Hours to look back"),
    user_only: bool = Query(False, description="Only show anomalies for current user"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Detect trading anomalies using AI analysis
    
    Detects:
    - Volume spikes (unusual trading activity)
    - Large trades (whale movements)
    - Rapid trading (potential bot activity)
    - Wash trading patterns
    - Price manipulation indicators
    """
    user_id = current_user.id if user_only else None
    
    anomalies = await ai_analytics_service.detect_anomalies(
        db=db,
        user_id=user_id,
        symbol=symbol,
        lookback_hours=lookback_hours,
    )
    
    return anomalies


@router.get("/risk/user", response_model=RiskScore)
async def get_user_risk_score(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Calculate comprehensive risk score for current user
    
    Factors analyzed:
    - Trading volume and frequency
    - Portfolio concentration
    - Volatility exposure
    - Historical patterns
    """
    risk_score = await ai_analytics_service.calculate_user_risk_score(
        db=db,
        user_id=current_user.id,
    )
    
    return risk_score


@router.get("/risk/user/{user_id}", response_model=RiskScore)
async def get_specific_user_risk_score(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Calculate risk score for a specific user (admin only)
    """
    # In production, add admin check here
    risk_score = await ai_analytics_service.calculate_user_risk_score(
        db=db,
        user_id=user_id,
    )
    
    return risk_score


@router.get("/predictions/{symbol}", response_model=PricePrediction)
async def get_price_prediction(
    symbol: str,
    horizon_minutes: int = Query(60, ge=5, le=1440, description="Prediction horizon in minutes"),
    db: AsyncSession = Depends(get_db),
    redis_client: redis.Redis = Depends(get_redis),
    current_user: User = Depends(get_current_user),
):
    """
    Get AI-powered price prediction for a symbol
    
    Analysis includes:
    - Moving average signals (SMA, EMA)
    - RSI (Relative Strength Index)
    - Volume trends
    - Momentum indicators
    - Bollinger Band analysis
    """
    prediction = await ai_analytics_service.predict_price(
        db=db,
        redis_client=redis_client,
        symbol=symbol,
        horizon_minutes=horizon_minutes,
    )
    
    return prediction


@router.get("/portfolio", response_model=PortfolioAnalysis)
async def analyze_portfolio(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get comprehensive AI portfolio analysis
    
    Includes:
    - Position breakdown
    - P&L analysis
    - Trading metrics (win rate, Sharpe ratio, etc.)
    - AI-generated insights and recommendations
    """
    analysis = await ai_analytics_service.analyze_portfolio(
        db=db,
        user_id=current_user.id,
    )
    
    return analysis


@router.get("/sentiment/{symbol}", response_model=MarketSentiment)
async def get_market_sentiment(
    symbol: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get AI-analyzed market sentiment for a symbol
    
    Analyzes:
    - Buy/sell pressure ratio
    - Volume trends
    - Price momentum
    - Order flow imbalance
    """
    sentiment = await ai_analytics_service.analyze_market_sentiment(
        db=db,
        symbol=symbol,
    )
    
    return sentiment


@router.get("/summary", response_model=AIAnalyticsSummary)
async def get_analytics_summary(
    symbols: List[str] = Query(default=["ETH-USDT", "BTC-USDT"]),
    db: AsyncSession = Depends(get_db),
    redis_client: redis.Redis = Depends(get_redis),
    current_user: User = Depends(get_current_user),
):
    """
    Get comprehensive AI analytics summary for dashboard
    
    Combines:
    - User risk score
    - Recent anomalies
    - Price predictions for specified symbols
    - Market sentiment
    - AI insights
    """
    # Get risk score
    risk_score = await ai_analytics_service.calculate_user_risk_score(
        db=db,
        user_id=current_user.id,
    )
    
    # Get recent anomalies
    anomalies = await ai_analytics_service.detect_anomalies(
        db=db,
        user_id=current_user.id,
        lookback_hours=24,
    )
    
    # Get predictions and sentiment for each symbol
    predictions = {}
    sentiment = {}
    
    for symbol in symbols[:5]:  # Limit to 5 symbols
        try:
            predictions[symbol] = await ai_analytics_service.predict_price(
                db=db,
                redis_client=redis_client,
                symbol=symbol,
                horizon_minutes=60,
            )
            sentiment[symbol] = await ai_analytics_service.analyze_market_sentiment(
                db=db,
                symbol=symbol,
            )
        except Exception:
            continue  # Skip symbols with errors
    
    # Get portfolio insights
    portfolio = await ai_analytics_service.analyze_portfolio(
        db=db,
        user_id=current_user.id,
    )
    
    return AIAnalyticsSummary(
        risk_score=risk_score,
        recent_anomalies=anomalies[:10],  # Top 10 anomalies
        predictions=predictions,
        sentiment=sentiment,
        insights=portfolio.insights,
        generated_at=datetime.utcnow(),
    )


@router.get("/insights", response_model=List[AIInsight])
async def get_ai_insights(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get AI-generated insights and recommendations
    
    Provides actionable insights based on:
    - Trading performance
    - Portfolio composition
    - Risk exposure
    - Market conditions
    """
    portfolio = await ai_analytics_service.analyze_portfolio(
        db=db,
        user_id=current_user.id,
    )
    
    return portfolio.insights


@router.get("/metrics", response_model=dict)
async def get_trading_metrics(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get detailed trading performance metrics
    
    Metrics include:
    - Win rate
    - Profit factor
    - Sharpe ratio
    - Maximum drawdown
    - Average profit/loss
    """
    portfolio = await ai_analytics_service.analyze_portfolio(
        db=db,
        user_id=current_user.id,
    )
    
    return {
        "metrics": portfolio.metrics,
        "total_value": portfolio.total_value,
        "total_pnl": portfolio.total_pnl,
        "total_pnl_percent": portfolio.total_pnl_percent,
        "position_count": len(portfolio.positions),
    }

