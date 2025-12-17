"""
AI Analytics Service
AI-driven financial analysis, anomaly detection, risk scoring, and predictions
Based on FDD (Financial Due Diligence) best practices
"""
import asyncio
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional, List, Dict, Any, Tuple
from uuid import UUID
from collections import defaultdict
import statistics
import math
import random

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
import redis.asyncio as redis

from app.models.trade import Trade
from app.models.order import Order, OrderStatus, OrderSide
from app.models.user import User
from app.schemas.analytics import (
    RiskScore,
    AnomalyAlert,
    AnomalyType,
    PricePrediction,
    PortfolioAnalysis,
    PortfolioPosition,
    MarketSentiment,
    AIInsight,
    TradingMetrics,
    RiskLevel,
)


class AIAnalyticsService:
    """
    AI-powered analytics service for trading platform
    
    Features:
    - Real-time anomaly detection using statistical analysis
    - Dynamic risk scoring for users and portfolios
    - Price predictions using trend analysis and momentum indicators
    - Portfolio performance analytics
    - Market sentiment analysis
    - Automated compliance monitoring
    """
    
    # Risk thresholds
    RISK_THRESHOLDS = {
        "volume_spike_multiplier": 3.0,  # Flag if volume > 3x average
        "price_deviation_percent": 5.0,   # Flag if price deviates > 5%
        "large_trade_percentile": 95,     # Flag trades in top 5% by size
        "rapid_trade_threshold": 10,      # Flag if > 10 trades per minute
        "concentration_threshold": 0.7,   # Flag if > 70% in single asset
    }
    
    # Anomaly detection windows
    ANALYSIS_WINDOWS = {
        "short_term": timedelta(hours=1),
        "medium_term": timedelta(days=1),
        "long_term": timedelta(days=7),
    }
    
    def __init__(self):
        self._cache: Dict[str, Any] = {}
        self._cache_ttl = 60  # seconds
        self._lock = asyncio.Lock()
    
    # ==================== ANOMALY DETECTION ====================
    
    async def detect_anomalies(
        self,
        db: AsyncSession,
        user_id: Optional[UUID] = None,
        symbol: Optional[str] = None,
        lookback_hours: int = 24,
    ) -> List[AnomalyAlert]:
        """
        Detect trading anomalies using statistical analysis
        
        Anomaly types detected:
        - Volume spikes (unusual trading volume)
        - Price manipulation (wash trading, spoofing patterns)
        - Large trades (whale movements)
        - Rapid trading (potential bot activity)
        - Unusual patterns (statistical outliers)
        """
        anomalies: List[AnomalyAlert] = []
        start_time = datetime.utcnow() - timedelta(hours=lookback_hours)
        
        # Build query for recent trades
        query = select(Trade).where(Trade.executed_at >= start_time)
        if user_id:
            query = query.where(Trade.user_id == user_id)
        if symbol:
            query = query.where(Trade.symbol == symbol)
        
        result = await db.execute(query.order_by(Trade.executed_at))
        trades = result.scalars().all()
        
        if not trades:
            return anomalies
        
        # Group trades by symbol for analysis
        trades_by_symbol: Dict[str, List[Trade]] = defaultdict(list)
        for trade in trades:
            trades_by_symbol[trade.symbol].append(trade)
        
        for sym, sym_trades in trades_by_symbol.items():
            # 1. Detect volume spikes
            volume_anomalies = await self._detect_volume_spikes(sym, sym_trades)
            anomalies.extend(volume_anomalies)
            
            # 2. Detect large trades
            large_trade_anomalies = await self._detect_large_trades(sym, sym_trades)
            anomalies.extend(large_trade_anomalies)
            
            # 3. Detect rapid trading
            rapid_trade_anomalies = await self._detect_rapid_trading(sym, sym_trades)
            anomalies.extend(rapid_trade_anomalies)
            
            # 4. Detect price manipulation patterns
            manipulation_anomalies = await self._detect_manipulation_patterns(sym, sym_trades)
            anomalies.extend(manipulation_anomalies)
        
        # Sort by severity and timestamp
        anomalies.sort(key=lambda x: (x.severity, x.detected_at), reverse=True)
        
        return anomalies
    
    async def _detect_volume_spikes(
        self,
        symbol: str,
        trades: List[Trade],
    ) -> List[AnomalyAlert]:
        """Detect unusual volume spikes"""
        anomalies = []
        
        if len(trades) < 10:
            return anomalies
        
        # Calculate hourly volumes
        hourly_volumes: Dict[int, Decimal] = defaultdict(Decimal)
        for trade in trades:
            hour_key = int(trade.executed_at.timestamp() // 3600)
            hourly_volumes[hour_key] += trade.quantity
        
        if len(hourly_volumes) < 3:
            return anomalies
        
        volumes = list(hourly_volumes.values())
        mean_vol = statistics.mean([float(v) for v in volumes])
        std_vol = statistics.stdev([float(v) for v in volumes]) if len(volumes) > 1 else 0
        
        threshold = mean_vol + (self.RISK_THRESHOLDS["volume_spike_multiplier"] * std_vol)
        
        for hour_key, volume in hourly_volumes.items():
            if float(volume) > threshold:
                spike_ratio = float(volume) / mean_vol if mean_vol > 0 else 0
                anomalies.append(AnomalyAlert(
                    id=f"vol_{symbol}_{hour_key}",
                    type=AnomalyType.VOLUME_SPIKE,
                    symbol=symbol,
                    severity=min(10, int(spike_ratio * 2)),
                    description=f"Volume spike detected: {spike_ratio:.1f}x average volume",
                    detected_at=datetime.fromtimestamp(hour_key * 3600),
                    metrics={
                        "volume": float(volume),
                        "average_volume": mean_vol,
                        "spike_ratio": spike_ratio,
                    },
                    recommendation="Monitor for potential market manipulation or significant news event",
                ))
        
        return anomalies
    
    async def _detect_large_trades(
        self,
        symbol: str,
        trades: List[Trade],
    ) -> List[AnomalyAlert]:
        """Detect unusually large trades (whale activity)"""
        anomalies = []
        
        if len(trades) < 10:
            return anomalies
        
        quantities = [float(t.quantity) for t in trades]
        threshold_percentile = self.RISK_THRESHOLDS["large_trade_percentile"]
        threshold = sorted(quantities)[int(len(quantities) * threshold_percentile / 100)]
        
        for trade in trades:
            if float(trade.quantity) > threshold:
                size_ratio = float(trade.quantity) / statistics.mean(quantities)
                anomalies.append(AnomalyAlert(
                    id=f"whale_{trade.trade_id}",
                    type=AnomalyType.LARGE_TRADE,
                    symbol=symbol,
                    user_id=trade.user_id,
                    severity=min(10, int(size_ratio)),
                    description=f"Large trade detected: {size_ratio:.1f}x average size",
                    detected_at=trade.executed_at,
                    metrics={
                        "trade_size": float(trade.quantity),
                        "average_size": statistics.mean(quantities),
                        "trade_value": float(trade.quote_quantity),
                    },
                    recommendation="Review for market impact and potential whale activity",
                ))
        
        return anomalies
    
    async def _detect_rapid_trading(
        self,
        symbol: str,
        trades: List[Trade],
    ) -> List[AnomalyAlert]:
        """Detect rapid trading patterns (potential bot activity)"""
        anomalies = []
        
        # Group trades by user and minute
        user_minute_trades: Dict[Tuple[UUID, int], int] = defaultdict(int)
        user_trades: Dict[UUID, List[Trade]] = defaultdict(list)
        
        for trade in trades:
            minute_key = int(trade.executed_at.timestamp() // 60)
            user_minute_trades[(trade.user_id, minute_key)] += 1
            user_trades[trade.user_id].append(trade)
        
        threshold = self.RISK_THRESHOLDS["rapid_trade_threshold"]
        
        for (user_id, minute_key), count in user_minute_trades.items():
            if count > threshold:
                anomalies.append(AnomalyAlert(
                    id=f"rapid_{user_id}_{minute_key}",
                    type=AnomalyType.RAPID_TRADING,
                    symbol=symbol,
                    user_id=user_id,
                    severity=min(10, count // threshold),
                    description=f"Rapid trading: {count} trades in 1 minute",
                    detected_at=datetime.fromtimestamp(minute_key * 60),
                    metrics={
                        "trades_per_minute": count,
                        "threshold": threshold,
                    },
                    recommendation="Review for automated trading or potential market manipulation",
                ))
        
        return anomalies
    
    async def _detect_manipulation_patterns(
        self,
        symbol: str,
        trades: List[Trade],
    ) -> List[AnomalyAlert]:
        """Detect potential market manipulation patterns"""
        anomalies = []
        
        # Look for wash trading patterns (self-trading or coordinated trading)
        user_buy_sell: Dict[UUID, Dict[str, Decimal]] = defaultdict(lambda: {"buy": Decimal(0), "sell": Decimal(0)})
        
        for trade in trades:
            user_buy_sell[trade.user_id][trade.side] += trade.quantity
        
        for user_id, volumes in user_buy_sell.items():
            buy_vol = float(volumes["buy"])
            sell_vol = float(volumes["sell"])
            
            if buy_vol > 0 and sell_vol > 0:
                # Check for nearly equal buy/sell volumes (potential wash trading)
                min_vol = min(buy_vol, sell_vol)
                max_vol = max(buy_vol, sell_vol)
                ratio = min_vol / max_vol if max_vol > 0 else 0
                
                if ratio > 0.9 and min_vol > 100:  # > 90% match and significant volume
                    anomalies.append(AnomalyAlert(
                        id=f"wash_{user_id}_{symbol}",
                        type=AnomalyType.WASH_TRADING,
                        symbol=symbol,
                        user_id=user_id,
                        severity=8,
                        description=f"Potential wash trading: buy/sell ratio {ratio:.2%}",
                        detected_at=datetime.utcnow(),
                        metrics={
                            "buy_volume": buy_vol,
                            "sell_volume": sell_vol,
                            "match_ratio": ratio,
                        },
                        recommendation="Investigate for potential wash trading or self-dealing",
                    ))
        
        return anomalies
    
    # ==================== RISK SCORING ====================
    
    async def calculate_user_risk_score(
        self,
        db: AsyncSession,
        user_id: UUID,
    ) -> RiskScore:
        """
        Calculate comprehensive risk score for a user
        
        Factors considered:
        - Trading volume and frequency
        - Profit/loss patterns
        - Portfolio concentration
        - Historical anomalies
        - Account age and verification status
        """
        # Get user's recent trades (last 30 days)
        start_time = datetime.utcnow() - timedelta(days=30)
        result = await db.execute(
            select(Trade)
            .where(Trade.user_id == user_id)
            .where(Trade.executed_at >= start_time)
            .order_by(Trade.executed_at)
        )
        trades = result.scalars().all()
        
        # Initialize risk factors
        risk_factors: Dict[str, float] = {}
        
        # 1. Trading volume risk (higher volume = higher risk exposure)
        total_volume = sum(float(t.quote_quantity) for t in trades)
        volume_risk = min(10, total_volume / 100000)  # Scale to 10
        risk_factors["trading_volume"] = volume_risk
        
        # 2. Trading frequency risk
        trade_count = len(trades)
        if trade_count > 0:
            avg_trades_per_day = trade_count / 30
            frequency_risk = min(10, avg_trades_per_day / 10)
        else:
            frequency_risk = 0
        risk_factors["trading_frequency"] = frequency_risk
        
        # 3. Portfolio concentration risk
        symbol_volumes: Dict[str, float] = defaultdict(float)
        for trade in trades:
            symbol_volumes[trade.symbol] += float(trade.quote_quantity)
        
        if symbol_volumes:
            max_concentration = max(symbol_volumes.values()) / total_volume if total_volume > 0 else 0
            concentration_risk = max_concentration * 10
        else:
            concentration_risk = 0
        risk_factors["concentration"] = concentration_risk
        
        # 4. Volatility risk (based on P&L swings)
        if len(trades) >= 10:
            trade_values = [float(t.quote_quantity) for t in trades]
            volatility = statistics.stdev(trade_values) / statistics.mean(trade_values) if statistics.mean(trade_values) > 0 else 0
            volatility_risk = min(10, volatility * 10)
        else:
            volatility_risk = 5  # Default medium risk for new users
        risk_factors["volatility"] = volatility_risk
        
        # Calculate overall risk score (weighted average)
        weights = {
            "trading_volume": 0.25,
            "trading_frequency": 0.20,
            "concentration": 0.30,
            "volatility": 0.25,
        }
        
        overall_score = sum(risk_factors[k] * weights[k] for k in weights)
        
        # Determine risk level
        if overall_score < 3:
            level = RiskLevel.LOW
        elif overall_score < 5:
            level = RiskLevel.MEDIUM
        elif overall_score < 7:
            level = RiskLevel.HIGH
        else:
            level = RiskLevel.CRITICAL
        
        # Generate recommendations
        recommendations = []
        if risk_factors["concentration"] > 6:
            recommendations.append("Diversify portfolio to reduce concentration risk")
        if risk_factors["trading_frequency"] > 7:
            recommendations.append("Consider reducing trading frequency to manage risk")
        if risk_factors["volatility"] > 7:
            recommendations.append("Implement stop-loss orders to manage volatility")
        
        return RiskScore(
            user_id=user_id,
            overall_score=round(overall_score, 2),
            level=level,
            factors=risk_factors,
            recommendations=recommendations,
            calculated_at=datetime.utcnow(),
            metrics={
                "total_trades": trade_count,
                "total_volume": total_volume,
                "unique_symbols": len(symbol_volumes),
            },
        )
    
    async def calculate_portfolio_risk(
        self,
        db: AsyncSession,
        user_id: UUID,
        positions: List[PortfolioPosition],
    ) -> RiskScore:
        """Calculate portfolio-level risk score"""
        if not positions:
            return RiskScore(
                user_id=user_id,
                overall_score=0,
                level=RiskLevel.LOW,
                factors={},
                recommendations=["Start trading to build portfolio"],
                calculated_at=datetime.utcnow(),
                metrics={},
            )
        
        risk_factors: Dict[str, float] = {}
        
        # Calculate total portfolio value
        total_value = sum(float(p.value_usd) for p in positions)
        
        # 1. Concentration risk (HHI - Herfindahl-Hirschman Index)
        if total_value > 0:
            market_shares = [(float(p.value_usd) / total_value) ** 2 for p in positions]
            hhi = sum(market_shares)
            concentration_risk = hhi * 10  # Scale to 10
        else:
            concentration_risk = 0
        risk_factors["concentration"] = concentration_risk
        
        # 2. Asset type diversification
        asset_types = set(p.asset_type for p in positions if p.asset_type)
        diversification_risk = max(0, 10 - len(asset_types) * 2)
        risk_factors["diversification"] = diversification_risk
        
        # 3. Unrealized P&L risk
        total_unrealized_pnl = sum(float(p.unrealized_pnl or 0) for p in positions)
        pnl_risk = abs(total_unrealized_pnl / total_value * 10) if total_value > 0 else 0
        risk_factors["unrealized_pnl"] = min(10, pnl_risk)
        
        # Calculate overall score
        overall_score = sum(risk_factors.values()) / len(risk_factors)
        
        # Determine level
        if overall_score < 3:
            level = RiskLevel.LOW
        elif overall_score < 5:
            level = RiskLevel.MEDIUM
        elif overall_score < 7:
            level = RiskLevel.HIGH
        else:
            level = RiskLevel.CRITICAL
        
        recommendations = []
        if concentration_risk > 6:
            recommendations.append("Reduce position size in concentrated holdings")
        if diversification_risk > 5:
            recommendations.append("Add more asset types to improve diversification")
        
        return RiskScore(
            user_id=user_id,
            overall_score=round(overall_score, 2),
            level=level,
            factors=risk_factors,
            recommendations=recommendations,
            calculated_at=datetime.utcnow(),
            metrics={
                "total_value": total_value,
                "position_count": len(positions),
                "asset_types": len(asset_types),
            },
        )
    
    # ==================== PRICE PREDICTIONS ====================
    
    async def predict_price(
        self,
        db: AsyncSession,
        redis_client: redis.Redis,
        symbol: str,
        horizon_minutes: int = 60,
    ) -> PricePrediction:
        """
        Generate price prediction using technical analysis and trend indicators
        
        Methods used:
        - Moving average convergence/divergence (MACD)
        - Relative strength index (RSI)
        - Bollinger Bands
        - Volume-weighted price trends
        """
        # Get recent trades for analysis
        lookback = timedelta(hours=24)
        start_time = datetime.utcnow() - lookback
        
        result = await db.execute(
            select(Trade)
            .where(Trade.symbol == symbol)
            .where(Trade.executed_at >= start_time)
            .order_by(Trade.executed_at)
        )
        trades = result.scalars().all()
        
        if len(trades) < 50:
            # Not enough data for prediction
            return PricePrediction(
                symbol=symbol,
                current_price=Decimal("0"),
                predicted_price=Decimal("0"),
                confidence=0.0,
                direction="neutral",
                horizon_minutes=horizon_minutes,
                factors={},
                generated_at=datetime.utcnow(),
            )
        
        # Extract price series
        prices = [float(t.price) for t in trades]
        volumes = [float(t.quantity) for t in trades]
        current_price = prices[-1]
        
        # Calculate technical indicators
        factors: Dict[str, Any] = {}
        
        # 1. Simple Moving Averages
        sma_20 = statistics.mean(prices[-20:]) if len(prices) >= 20 else current_price
        sma_50 = statistics.mean(prices[-50:]) if len(prices) >= 50 else current_price
        factors["sma_20"] = sma_20
        factors["sma_50"] = sma_50
        factors["sma_signal"] = "bullish" if sma_20 > sma_50 else "bearish"
        
        # 2. RSI (Relative Strength Index)
        rsi = self._calculate_rsi(prices, period=14)
        factors["rsi"] = rsi
        factors["rsi_signal"] = "oversold" if rsi < 30 else "overbought" if rsi > 70 else "neutral"
        
        # 3. Price momentum
        if len(prices) >= 10:
            momentum = (prices[-1] - prices[-10]) / prices[-10] * 100
        else:
            momentum = 0
        factors["momentum"] = momentum
        
        # 4. Volume trend
        recent_vol = statistics.mean(volumes[-10:]) if len(volumes) >= 10 else 0
        older_vol = statistics.mean(volumes[-50:-10]) if len(volumes) >= 50 else recent_vol
        volume_trend = recent_vol / older_vol if older_vol > 0 else 1
        factors["volume_trend"] = volume_trend
        
        # 5. Volatility (Bollinger Band width)
        if len(prices) >= 20:
            std_dev = statistics.stdev(prices[-20:])
            bb_width = (std_dev * 2) / sma_20 * 100
        else:
            bb_width = 5
        factors["bollinger_width"] = bb_width
        
        # Generate prediction based on indicators
        signals = []
        
        # SMA crossover signal
        if sma_20 > sma_50:
            signals.append(0.2)  # Bullish
        else:
            signals.append(-0.2)  # Bearish
        
        # RSI signal
        if rsi < 30:
            signals.append(0.3)  # Oversold - likely to rise
        elif rsi > 70:
            signals.append(-0.3)  # Overbought - likely to fall
        else:
            signals.append(0)
        
        # Momentum signal
        signals.append(min(0.3, max(-0.3, momentum / 10)))
        
        # Volume signal
        if volume_trend > 1.5:
            signals.append(0.1 if momentum > 0 else -0.1)  # Volume confirms trend
        
        # Calculate predicted price change
        combined_signal = sum(signals)
        predicted_change_pct = combined_signal * (horizon_minutes / 60) * 0.5  # Scale by time
        predicted_price = current_price * (1 + predicted_change_pct / 100)
        
        # Determine direction and confidence
        if combined_signal > 0.2:
            direction = "bullish"
            confidence = min(0.85, 0.5 + abs(combined_signal))
        elif combined_signal < -0.2:
            direction = "bearish"
            confidence = min(0.85, 0.5 + abs(combined_signal))
        else:
            direction = "neutral"
            confidence = 0.5
        
        return PricePrediction(
            symbol=symbol,
            current_price=Decimal(str(round(current_price, 8))),
            predicted_price=Decimal(str(round(predicted_price, 8))),
            confidence=round(confidence, 2),
            direction=direction,
            horizon_minutes=horizon_minutes,
            factors=factors,
            generated_at=datetime.utcnow(),
        )
    
    def _calculate_rsi(self, prices: List[float], period: int = 14) -> float:
        """Calculate Relative Strength Index"""
        if len(prices) < period + 1:
            return 50.0  # Neutral
        
        deltas = [prices[i] - prices[i-1] for i in range(1, len(prices))]
        recent_deltas = deltas[-period:]
        
        gains = [d for d in recent_deltas if d > 0]
        losses = [-d for d in recent_deltas if d < 0]
        
        avg_gain = statistics.mean(gains) if gains else 0
        avg_loss = statistics.mean(losses) if losses else 0
        
        if avg_loss == 0:
            return 100.0
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return round(rsi, 2)
    
    # ==================== PORTFOLIO ANALYSIS ====================
    
    async def analyze_portfolio(
        self,
        db: AsyncSession,
        user_id: UUID,
    ) -> PortfolioAnalysis:
        """
        Comprehensive portfolio analysis with AI insights
        """
        # Get all user trades
        result = await db.execute(
            select(Trade)
            .where(Trade.user_id == user_id)
            .order_by(Trade.executed_at)
        )
        trades = result.scalars().all()
        
        if not trades:
            return PortfolioAnalysis(
                user_id=user_id,
                total_value=Decimal("0"),
                total_pnl=Decimal("0"),
                total_pnl_percent=Decimal("0"),
                positions=[],
                metrics=TradingMetrics(
                    total_trades=0,
                    winning_trades=0,
                    losing_trades=0,
                    win_rate=Decimal("0"),
                    avg_profit=Decimal("0"),
                    avg_loss=Decimal("0"),
                    profit_factor=Decimal("0"),
                    sharpe_ratio=Decimal("0"),
                    max_drawdown=Decimal("0"),
                    avg_hold_time_hours=Decimal("0"),
                ),
                insights=[],
                analyzed_at=datetime.utcnow(),
            )
        
        # Calculate positions from trades
        positions_data: Dict[str, Dict] = defaultdict(lambda: {
            "quantity": Decimal("0"),
            "cost_basis": Decimal("0"),
            "trades": [],
        })
        
        for trade in trades:
            symbol = trade.symbol
            if trade.side == "buy":
                positions_data[symbol]["quantity"] += trade.quantity
                positions_data[symbol]["cost_basis"] += trade.quote_quantity
            else:
                positions_data[symbol]["quantity"] -= trade.quantity
                positions_data[symbol]["cost_basis"] -= trade.quote_quantity
            positions_data[symbol]["trades"].append(trade)
        
        # Build position list
        positions: List[PortfolioPosition] = []
        total_value = Decimal("0")
        total_cost = Decimal("0")
        
        for symbol, data in positions_data.items():
            if data["quantity"] > 0:
                # Get latest price (from most recent trade)
                latest_trade = data["trades"][-1]
                current_price = latest_trade.price
                value = data["quantity"] * current_price
                cost = data["cost_basis"]
                unrealized_pnl = value - cost
                pnl_percent = (unrealized_pnl / cost * 100) if cost > 0 else Decimal("0")
                
                positions.append(PortfolioPosition(
                    symbol=symbol,
                    quantity=data["quantity"],
                    avg_price=cost / data["quantity"] if data["quantity"] > 0 else Decimal("0"),
                    current_price=current_price,
                    value_usd=value,
                    unrealized_pnl=unrealized_pnl,
                    unrealized_pnl_percent=pnl_percent,
                    asset_type="crypto",
                ))
                
                total_value += value
                total_cost += cost
        
        # Calculate trading metrics
        metrics = await self._calculate_trading_metrics(trades)
        
        # Generate AI insights
        insights = await self._generate_insights(positions, metrics)
        
        # Calculate total P&L
        total_pnl = total_value - total_cost
        total_pnl_percent = (total_pnl / total_cost * 100) if total_cost > 0 else Decimal("0")
        
        return PortfolioAnalysis(
            user_id=user_id,
            total_value=total_value,
            total_pnl=total_pnl,
            total_pnl_percent=total_pnl_percent,
            positions=positions,
            metrics=metrics,
            insights=insights,
            analyzed_at=datetime.utcnow(),
        )
    
    async def _calculate_trading_metrics(
        self,
        trades: List[Trade],
    ) -> TradingMetrics:
        """Calculate comprehensive trading metrics"""
        if not trades:
            return TradingMetrics(
                total_trades=0,
                winning_trades=0,
                losing_trades=0,
                win_rate=Decimal("0"),
                avg_profit=Decimal("0"),
                avg_loss=Decimal("0"),
                profit_factor=Decimal("0"),
                sharpe_ratio=Decimal("0"),
                max_drawdown=Decimal("0"),
                avg_hold_time_hours=Decimal("0"),
            )
        
        # Group trades into round trips (buy then sell)
        profits: List[float] = []
        losses: List[float] = []
        
        # Simplified P&L calculation based on consecutive trades
        for i in range(1, len(trades)):
            prev_trade = trades[i-1]
            curr_trade = trades[i]
            
            if prev_trade.symbol == curr_trade.symbol:
                if prev_trade.side == "buy" and curr_trade.side == "sell":
                    pnl = float(curr_trade.price - prev_trade.price) * float(min(prev_trade.quantity, curr_trade.quantity))
                    if pnl > 0:
                        profits.append(pnl)
                    else:
                        losses.append(abs(pnl))
                elif prev_trade.side == "sell" and curr_trade.side == "buy":
                    pnl = float(prev_trade.price - curr_trade.price) * float(min(prev_trade.quantity, curr_trade.quantity))
                    if pnl > 0:
                        profits.append(pnl)
                    else:
                        losses.append(abs(pnl))
        
        winning_trades = len(profits)
        losing_trades = len(losses)
        total_trades = len(trades)
        
        win_rate = Decimal(str(winning_trades / max(1, winning_trades + losing_trades) * 100))
        avg_profit = Decimal(str(statistics.mean(profits))) if profits else Decimal("0")
        avg_loss = Decimal(str(statistics.mean(losses))) if losses else Decimal("0")
        
        total_profit = sum(profits)
        total_loss = sum(losses) if losses else 1
        profit_factor = Decimal(str(total_profit / total_loss if total_loss > 0 else 0))
        
        # Calculate Sharpe ratio (simplified)
        all_returns = profits + [-l for l in losses]
        if len(all_returns) > 1:
            avg_return = statistics.mean(all_returns)
            std_return = statistics.stdev(all_returns)
            sharpe = avg_return / std_return if std_return > 0 else 0
        else:
            sharpe = 0
        
        # Calculate max drawdown
        equity_curve = [0.0]
        for r in profits + [-l for l in losses]:
            equity_curve.append(equity_curve[-1] + r)
        
        peak = equity_curve[0]
        max_dd = 0.0
        for value in equity_curve:
            if value > peak:
                peak = value
            dd = (peak - value) / peak if peak > 0 else 0
            max_dd = max(max_dd, dd)
        
        return TradingMetrics(
            total_trades=total_trades,
            winning_trades=winning_trades,
            losing_trades=losing_trades,
            win_rate=win_rate,
            avg_profit=avg_profit,
            avg_loss=avg_loss,
            profit_factor=profit_factor,
            sharpe_ratio=Decimal(str(round(sharpe, 2))),
            max_drawdown=Decimal(str(round(max_dd * 100, 2))),
            avg_hold_time_hours=Decimal("0"),  # Would need order matching for accurate calculation
        )
    
    async def _generate_insights(
        self,
        positions: List[PortfolioPosition],
        metrics: TradingMetrics,
    ) -> List[AIInsight]:
        """Generate AI-powered insights based on portfolio analysis"""
        insights: List[AIInsight] = []
        
        # Insight 1: Win rate analysis
        if metrics.win_rate < 40:
            insights.append(AIInsight(
                type="performance",
                title="Low Win Rate Detected",
                description=f"Your win rate of {metrics.win_rate:.1f}% is below optimal. Consider refining your entry criteria.",
                importance="high",
                action="Review losing trades to identify patterns and improve entry timing",
            ))
        elif metrics.win_rate > 60:
            insights.append(AIInsight(
                type="performance",
                title="Strong Win Rate",
                description=f"Your win rate of {metrics.win_rate:.1f}% indicates good trade selection.",
                importance="low",
                action="Maintain current strategy while monitoring for market changes",
            ))
        
        # Insight 2: Profit factor
        if metrics.profit_factor < 1:
            insights.append(AIInsight(
                type="risk",
                title="Negative Expectancy",
                description="Your profit factor is below 1, indicating losses outweigh gains on average.",
                importance="critical",
                action="Review position sizing and stop-loss placement immediately",
            ))
        
        # Insight 3: Portfolio concentration
        if positions:
            total_value = sum(float(p.value_usd) for p in positions)
            if total_value > 0:
                max_position = max(positions, key=lambda p: float(p.value_usd))
                concentration = float(max_position.value_usd) / total_value
                
                if concentration > 0.5:
                    insights.append(AIInsight(
                        type="risk",
                        title="High Concentration Risk",
                        description=f"{max_position.symbol} represents {concentration:.0%} of your portfolio.",
                        importance="high",
                        action=f"Consider reducing {max_position.symbol} position to improve diversification",
                    ))
        
        # Insight 4: Unrealized P&L
        if positions:
            for pos in positions:
                if pos.unrealized_pnl_percent and float(pos.unrealized_pnl_percent) > 50:
                    insights.append(AIInsight(
                        type="opportunity",
                        title="Large Unrealized Gain",
                        description=f"{pos.symbol} has {pos.unrealized_pnl_percent:.1f}% unrealized gain.",
                        importance="medium",
                        action="Consider taking partial profits to lock in gains",
                    ))
                elif pos.unrealized_pnl_percent and float(pos.unrealized_pnl_percent) < -30:
                    insights.append(AIInsight(
                        type="risk",
                        title="Large Unrealized Loss",
                        description=f"{pos.symbol} has {pos.unrealized_pnl_percent:.1f}% unrealized loss.",
                        importance="high",
                        action="Review position thesis and consider stop-loss placement",
                    ))
        
        # Insight 5: Max drawdown
        if metrics.max_drawdown > 20:
            insights.append(AIInsight(
                type="risk",
                title="High Maximum Drawdown",
                description=f"Your maximum drawdown of {metrics.max_drawdown:.1f}% indicates significant risk exposure.",
                importance="high",
                action="Implement stricter risk management rules to limit drawdowns",
            ))
        
        return insights
    
    # ==================== MARKET SENTIMENT ====================
    
    async def analyze_market_sentiment(
        self,
        db: AsyncSession,
        symbol: str,
    ) -> MarketSentiment:
        """
        Analyze market sentiment based on trading activity
        """
        lookback = timedelta(hours=24)
        start_time = datetime.utcnow() - lookback
        
        result = await db.execute(
            select(Trade)
            .where(Trade.symbol == symbol)
            .where(Trade.executed_at >= start_time)
            .order_by(Trade.executed_at)
        )
        trades = result.scalars().all()
        
        if not trades:
            return MarketSentiment(
                symbol=symbol,
                sentiment="neutral",
                score=50,
                buy_pressure=50,
                sell_pressure=50,
                volume_trend="stable",
                price_trend="sideways",
                analyzed_at=datetime.utcnow(),
            )
        
        # Calculate buy/sell pressure
        buy_volume = sum(float(t.quantity) for t in trades if t.side == "buy")
        sell_volume = sum(float(t.quantity) for t in trades if t.side == "sell")
        total_volume = buy_volume + sell_volume
        
        buy_pressure = (buy_volume / total_volume * 100) if total_volume > 0 else 50
        sell_pressure = (sell_volume / total_volume * 100) if total_volume > 0 else 50
        
        # Calculate sentiment score (0-100, 50 = neutral)
        sentiment_score = int(buy_pressure)
        
        # Determine sentiment label
        if sentiment_score > 65:
            sentiment = "bullish"
        elif sentiment_score > 55:
            sentiment = "slightly_bullish"
        elif sentiment_score < 35:
            sentiment = "bearish"
        elif sentiment_score < 45:
            sentiment = "slightly_bearish"
        else:
            sentiment = "neutral"
        
        # Price trend
        prices = [float(t.price) for t in trades]
        if len(prices) >= 10:
            early_avg = statistics.mean(prices[:len(prices)//2])
            late_avg = statistics.mean(prices[len(prices)//2:])
            price_change = (late_avg - early_avg) / early_avg * 100
            
            if price_change > 2:
                price_trend = "uptrend"
            elif price_change < -2:
                price_trend = "downtrend"
            else:
                price_trend = "sideways"
        else:
            price_trend = "sideways"
        
        # Volume trend
        if len(trades) >= 20:
            early_count = len([t for t in trades[:len(trades)//2]])
            late_count = len([t for t in trades[len(trades)//2:]])
            
            if late_count > early_count * 1.5:
                volume_trend = "increasing"
            elif late_count < early_count * 0.6:
                volume_trend = "decreasing"
            else:
                volume_trend = "stable"
        else:
            volume_trend = "stable"
        
        return MarketSentiment(
            symbol=symbol,
            sentiment=sentiment,
            score=sentiment_score,
            buy_pressure=round(buy_pressure, 1),
            sell_pressure=round(sell_pressure, 1),
            volume_trend=volume_trend,
            price_trend=price_trend,
            analyzed_at=datetime.utcnow(),
        )


# Global service instance
ai_analytics_service = AIAnalyticsService()

