"use client";

import { useState, useEffect, useCallback } from "react";
import { analytics } from "@/lib/api";
import { tradingWs } from "@/lib/websocket";

// Types
export interface RiskScore {
  user_id?: string;
  overall_score: number;
  level: "low" | "medium" | "high" | "critical";
  factors: Record<string, number>;
  recommendations: string[];
  calculated_at: string;
  metrics: Record<string, any>;
}

export interface AnomalyAlert {
  id: string;
  type: string;
  symbol: string;
  user_id?: string;
  severity: number;
  description: string;
  detected_at: string;
  metrics: Record<string, any>;
  recommendation?: string;
}

export interface PricePrediction {
  symbol: string;
  current_price: number;
  predicted_price: number;
  confidence: number;
  direction: "bullish" | "bearish" | "neutral";
  horizon_minutes: number;
  factors: Record<string, any>;
  generated_at: string;
}

export interface MarketSentiment {
  symbol: string;
  sentiment: string;
  score: number;
  buy_pressure: number;
  sell_pressure: number;
  volume_trend: string;
  price_trend: string;
  analyzed_at: string;
}

export interface AIInsight {
  type: string;
  title: string;
  description: string;
  importance: string;
  action?: string;
}

export interface PortfolioAnalysis {
  user_id: string;
  total_value: number;
  total_pnl: number;
  total_pnl_percent: number;
  positions: any[];
  metrics: any;
  insights: AIInsight[];
  analyzed_at: string;
}

// Hook for risk score
export function useRiskScore() {
  const [riskScore, setRiskScore] = useState<RiskScore | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchRiskScore = useCallback(async () => {
    try {
      setIsLoading(true);
      const response = await analytics.getUserRiskScore();
      setRiskScore(response.data);
      setError(null);
    } catch (err: any) {
      setError(err.message || "Failed to fetch risk score");
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchRiskScore();
    
    // Refresh every 5 minutes
    const interval = setInterval(fetchRiskScore, 5 * 60 * 1000);
    return () => clearInterval(interval);
  }, [fetchRiskScore]);

  return { riskScore, isLoading, error, refetch: fetchRiskScore };
}

// Hook for anomaly alerts
export function useAnomalyAlerts(options?: {
  symbol?: string;
  lookbackHours?: number;
  userOnly?: boolean;
}) {
  const [anomalies, setAnomalies] = useState<AnomalyAlert[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchAnomalies = useCallback(async () => {
    try {
      setIsLoading(true);
      const response = await analytics.getAnomalies({
        symbol: options?.symbol,
        lookback_hours: options?.lookbackHours,
        user_only: options?.userOnly,
      });
      setAnomalies(response.data);
      setError(null);
    } catch (err: any) {
      setError(err.message || "Failed to fetch anomalies");
    } finally {
      setIsLoading(false);
    }
  }, [options?.symbol, options?.lookbackHours, options?.userOnly]);

  useEffect(() => {
    fetchAnomalies();
    
    // Subscribe to real-time anomaly alerts
    const handleNewAnomaly = (data: AnomalyAlert) => {
      setAnomalies((prev) => [data, ...prev].slice(0, 50));
    };

    tradingWs.on("analytics:anomaly", handleNewAnomaly);
    tradingWs.subscribe("analytics:anomaly");

    return () => {
      tradingWs.off("analytics:anomaly", handleNewAnomaly);
      tradingWs.unsubscribe("analytics:anomaly");
    };
  }, [fetchAnomalies]);

  return { anomalies, isLoading, error, refetch: fetchAnomalies };
}

// Hook for price predictions
export function usePricePrediction(symbol: string, horizonMinutes = 60) {
  const [prediction, setPrediction] = useState<PricePrediction | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchPrediction = useCallback(async () => {
    try {
      setIsLoading(true);
      const response = await analytics.getPricePrediction(symbol, horizonMinutes);
      setPrediction(response.data);
      setError(null);
    } catch (err: any) {
      setError(err.message || "Failed to fetch prediction");
    } finally {
      setIsLoading(false);
    }
  }, [symbol, horizonMinutes]);

  useEffect(() => {
    fetchPrediction();
    
    // Refresh every minute
    const interval = setInterval(fetchPrediction, 60 * 1000);
    return () => clearInterval(interval);
  }, [fetchPrediction]);

  return { prediction, isLoading, error, refetch: fetchPrediction };
}

// Hook for market sentiment
export function useMarketSentiment(symbol: string) {
  const [sentiment, setSentiment] = useState<MarketSentiment | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchSentiment = useCallback(async () => {
    try {
      setIsLoading(true);
      const response = await analytics.getMarketSentiment(symbol);
      setSentiment(response.data);
      setError(null);
    } catch (err: any) {
      setError(err.message || "Failed to fetch sentiment");
    } finally {
      setIsLoading(false);
    }
  }, [symbol]);

  useEffect(() => {
    fetchSentiment();
    
    // Refresh every 30 seconds
    const interval = setInterval(fetchSentiment, 30 * 1000);
    return () => clearInterval(interval);
  }, [fetchSentiment]);

  return { sentiment, isLoading, error, refetch: fetchSentiment };
}

// Hook for portfolio analysis
export function usePortfolioAnalysis() {
  const [portfolio, setPortfolio] = useState<PortfolioAnalysis | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchPortfolio = useCallback(async () => {
    try {
      setIsLoading(true);
      const response = await analytics.getPortfolioAnalysis();
      setPortfolio(response.data);
      setError(null);
    } catch (err: any) {
      setError(err.message || "Failed to fetch portfolio");
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchPortfolio();
    
    // Refresh every 2 minutes
    const interval = setInterval(fetchPortfolio, 2 * 60 * 1000);
    return () => clearInterval(interval);
  }, [fetchPortfolio]);

  return { portfolio, isLoading, error, refetch: fetchPortfolio };
}

// Hook for AI insights
export function useAIInsights() {
  const [insights, setInsights] = useState<AIInsight[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchInsights = useCallback(async () => {
    try {
      setIsLoading(true);
      const response = await analytics.getInsights();
      setInsights(response.data);
      setError(null);
    } catch (err: any) {
      setError(err.message || "Failed to fetch insights");
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchInsights();
    
    // Refresh every 5 minutes
    const interval = setInterval(fetchInsights, 5 * 60 * 1000);
    return () => clearInterval(interval);
  }, [fetchInsights]);

  return { insights, isLoading, error, refetch: fetchInsights };
}

// Comprehensive analytics summary hook
export function useAnalyticsSummary(symbols: string[] = ["ETH-USDT", "BTC-USDT"]) {
  const [summary, setSummary] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchSummary = useCallback(async () => {
    try {
      setIsLoading(true);
      const response = await analytics.getSummary(symbols);
      setSummary(response.data);
      setError(null);
    } catch (err: any) {
      setError(err.message || "Failed to fetch summary");
    } finally {
      setIsLoading(false);
    }
  }, [symbols.join(",")]);

  useEffect(() => {
    fetchSummary();
    
    // Refresh every 2 minutes
    const interval = setInterval(fetchSummary, 2 * 60 * 1000);
    return () => clearInterval(interval);
  }, [fetchSummary]);

  return { summary, isLoading, error, refetch: fetchSummary };
}

