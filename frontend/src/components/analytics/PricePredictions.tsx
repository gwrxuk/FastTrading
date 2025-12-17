"use client";

import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import clsx from "clsx";

interface PricePrediction {
  symbol: string;
  current_price: number;
  predicted_price: number;
  confidence: number;
  direction: "bullish" | "bearish" | "neutral";
  horizon_minutes: number;
  factors: {
    sma_20?: number;
    sma_50?: number;
    sma_signal?: string;
    rsi?: number;
    rsi_signal?: string;
    momentum?: number;
    volume_trend?: number;
    bollinger_width?: number;
  };
}

interface PricePredictionsProps {
  symbols: string[];
  compact?: boolean;
}

export function PricePredictions({ symbols, compact = false }: PricePredictionsProps) {
  const [predictions, setPredictions] = useState<Record<string, PricePrediction>>({});
  const [isLoading, setIsLoading] = useState(true);
  const [selectedSymbol, setSelectedSymbol] = useState<string | null>(null);

  useEffect(() => {
    // Simulate API call with mock data
    const timer = setTimeout(() => {
      const mockPredictions: Record<string, PricePrediction> = {};
      
      symbols.forEach((symbol) => {
        const isEth = symbol.includes("ETH");
        const basePrice = isEth ? 2256.78 : 43250.00;
        const direction = Math.random() > 0.4 ? "bullish" : Math.random() > 0.5 ? "bearish" : "neutral";
        const changePercent = direction === "bullish" ? 0.8 + Math.random() * 1.5 : 
                            direction === "bearish" ? -0.8 - Math.random() * 1.5 : 
                            Math.random() * 0.4 - 0.2;
        
        mockPredictions[symbol] = {
          symbol,
          current_price: basePrice,
          predicted_price: basePrice * (1 + changePercent / 100),
          confidence: 0.6 + Math.random() * 0.25,
          direction,
          horizon_minutes: 60,
          factors: {
            sma_20: basePrice * (1 + Math.random() * 0.02),
            sma_50: basePrice * (1 - Math.random() * 0.01),
            sma_signal: direction === "bullish" ? "bullish" : "bearish",
            rsi: 30 + Math.random() * 40,
            rsi_signal: "neutral",
            momentum: changePercent * 2,
            volume_trend: 0.8 + Math.random() * 0.4,
            bollinger_width: 3 + Math.random() * 4,
          },
        };
      });
      
      setPredictions(mockPredictions);
      setIsLoading(false);
    }, 700);

    return () => clearTimeout(timer);
  }, [symbols]);

  if (isLoading) {
    return (
      <div className={clsx(compact && "space-y-2")}>
        {compact ? (
          symbols.map((symbol) => (
            <div key={symbol} className="h-12 bg-terminal-surface rounded-lg animate-pulse" />
          ))
        ) : (
          <div className="h-48 bg-terminal-surface rounded-lg animate-pulse" />
        )}
      </div>
    );
  }

  if (compact) {
    return (
      <div className="space-y-2">
        {symbols.map((symbol) => {
          const prediction = predictions[symbol];
          if (!prediction) return null;

          const priceChange = prediction.predicted_price - prediction.current_price;
          const changePercent = (priceChange / prediction.current_price) * 100;

          return (
            <motion.div
              key={symbol}
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              className="flex items-center justify-between p-2 bg-terminal-surface rounded-lg"
            >
              <div className="flex items-center gap-2">
                <span className={clsx(
                  "text-lg",
                  prediction.direction === "bullish" ? "text-bull" :
                  prediction.direction === "bearish" ? "text-bear" : "text-terminal-muted"
                )}>
                  {prediction.direction === "bullish" ? "📈" :
                   prediction.direction === "bearish" ? "📉" : "➡️"}
                </span>
                <div>
                  <span className="font-mono text-sm">{symbol}</span>
                  <div className="text-xs text-terminal-muted">
                    {Math.round(prediction.confidence * 100)}% confidence
                  </div>
                </div>
              </div>
              <div className="text-right">
                <div className="font-mono text-sm">
                  ${prediction.predicted_price.toFixed(2)}
                </div>
                <div className={clsx(
                  "text-xs font-mono",
                  changePercent >= 0 ? "text-bull" : "text-bear"
                )}>
                  {changePercent >= 0 ? "+" : ""}{changePercent.toFixed(2)}%
                </div>
              </div>
            </motion.div>
          );
        })}
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Symbol tabs */}
      <div className="flex gap-2">
        {symbols.map((symbol) => (
          <button
            key={symbol}
            onClick={() => setSelectedSymbol(selectedSymbol === symbol ? null : symbol)}
            className={clsx(
              "px-4 py-2 rounded-lg text-sm font-medium transition-all",
              selectedSymbol === symbol
                ? "bg-accent-primary text-terminal-bg"
                : "bg-terminal-surface text-terminal-muted hover:text-white"
            )}
          >
            {symbol}
          </button>
        ))}
      </div>

      {/* Predictions grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {(selectedSymbol ? [selectedSymbol] : symbols).map((symbol) => {
          const prediction = predictions[symbol];
          if (!prediction) return null;

          const priceChange = prediction.predicted_price - prediction.current_price;
          const changePercent = (priceChange / prediction.current_price) * 100;

          return (
            <motion.div
              key={symbol}
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              className={clsx(
                "p-4 rounded-xl border",
                prediction.direction === "bullish" 
                  ? "bg-bull/5 border-bull/20" 
                  : prediction.direction === "bearish"
                  ? "bg-bear/5 border-bear/20"
                  : "bg-terminal-surface border-terminal-border"
              )}
            >
              {/* Header */}
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-2">
                  <span className="text-2xl">
                    {prediction.direction === "bullish" ? "🚀" :
                     prediction.direction === "bearish" ? "🔻" : "⏸️"}
                  </span>
                  <div>
                    <h4 className="font-mono font-bold">{symbol}</h4>
                    <span className="text-xs text-terminal-muted">
                      {prediction.horizon_minutes}min forecast
                    </span>
                  </div>
                </div>
                <div className={clsx(
                  "px-3 py-1 rounded-full text-sm font-medium",
                  prediction.direction === "bullish" 
                    ? "bg-bull/20 text-bull"
                    : prediction.direction === "bearish"
                    ? "bg-bear/20 text-bear"
                    : "bg-terminal-muted/20 text-terminal-muted"
                )}>
                  {prediction.direction.charAt(0).toUpperCase() + prediction.direction.slice(1)}
                </div>
              </div>

              {/* Price prediction */}
              <div className="flex items-end justify-between mb-4">
                <div>
                  <div className="text-xs text-terminal-muted mb-1">Current Price</div>
                  <div className="font-mono text-lg">${prediction.current_price.toFixed(2)}</div>
                </div>
                <div className="text-2xl text-terminal-muted">→</div>
                <div className="text-right">
                  <div className="text-xs text-terminal-muted mb-1">Predicted Price</div>
                  <div className={clsx(
                    "font-mono text-xl font-bold",
                    changePercent >= 0 ? "text-bull" : "text-bear"
                  )}>
                    ${prediction.predicted_price.toFixed(2)}
                  </div>
                  <div className={clsx(
                    "text-sm font-mono",
                    changePercent >= 0 ? "text-bull" : "text-bear"
                  )}>
                    {changePercent >= 0 ? "+" : ""}{changePercent.toFixed(2)}%
                  </div>
                </div>
              </div>

              {/* Confidence meter */}
              <div className="mb-4">
                <div className="flex justify-between text-xs text-terminal-muted mb-1">
                  <span>Confidence Level</span>
                  <span className="font-mono">{Math.round(prediction.confidence * 100)}%</span>
                </div>
                <div className="h-2 bg-terminal-elevated rounded-full overflow-hidden">
                  <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: `${prediction.confidence * 100}%` }}
                    transition={{ duration: 1 }}
                    className={clsx(
                      "h-full rounded-full",
                      prediction.confidence > 0.7 ? "bg-bull" :
                      prediction.confidence > 0.5 ? "bg-yellow-500" : "bg-terminal-muted"
                    )}
                  />
                </div>
              </div>

              {/* Technical factors */}
              <div className="grid grid-cols-3 gap-2">
                <FactorBadge
                  label="RSI"
                  value={prediction.factors.rsi?.toFixed(0) || "N/A"}
                  signal={prediction.factors.rsi && prediction.factors.rsi < 30 ? "oversold" :
                          prediction.factors.rsi && prediction.factors.rsi > 70 ? "overbought" : "neutral"}
                />
                <FactorBadge
                  label="Momentum"
                  value={`${prediction.factors.momentum && prediction.factors.momentum > 0 ? "+" : ""}${prediction.factors.momentum?.toFixed(1)}%`}
                  signal={prediction.factors.momentum && prediction.factors.momentum > 0 ? "bullish" : "bearish"}
                />
                <FactorBadge
                  label="Volume"
                  value={`${((prediction.factors.volume_trend || 1) * 100).toFixed(0)}%`}
                  signal={prediction.factors.volume_trend && prediction.factors.volume_trend > 1.2 ? "high" : "normal"}
                />
              </div>
            </motion.div>
          );
        })}
      </div>
    </div>
  );
}

interface FactorBadgeProps {
  label: string;
  value: string;
  signal: string;
}

function FactorBadge({ label, value, signal }: FactorBadgeProps) {
  const signalColors: Record<string, string> = {
    bullish: "text-bull",
    bearish: "text-bear",
    oversold: "text-bull",
    overbought: "text-bear",
    high: "text-accent-primary",
    normal: "text-terminal-muted",
    neutral: "text-terminal-muted",
  };

  return (
    <div className="bg-terminal-elevated rounded-lg p-2 text-center">
      <div className="text-xs text-terminal-muted">{label}</div>
      <div className={clsx("font-mono text-sm", signalColors[signal] || "text-white")}>
        {value}
      </div>
    </div>
  );
}

