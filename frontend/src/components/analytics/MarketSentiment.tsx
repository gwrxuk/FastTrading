"use client";

import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import clsx from "clsx";

interface SentimentData {
  symbol: string;
  sentiment: string;
  score: number;
  buy_pressure: number;
  sell_pressure: number;
  volume_trend: string;
  price_trend: string;
}

interface MarketSentimentProps {
  symbol: string;
  compact?: boolean;
}

export function MarketSentiment({ symbol, compact = false }: MarketSentimentProps) {
  const [sentiment, setSentiment] = useState<SentimentData | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // Simulate API call with mock data
    const timer = setTimeout(() => {
      const score = 45 + Math.floor(Math.random() * 30);
      setSentiment({
        symbol,
        sentiment: score > 60 ? "bullish" : score < 40 ? "bearish" : "neutral",
        score,
        buy_pressure: score + Math.random() * 10 - 5,
        sell_pressure: 100 - score + Math.random() * 10 - 5,
        volume_trend: Math.random() > 0.5 ? "increasing" : "stable",
        price_trend: score > 55 ? "uptrend" : score < 45 ? "downtrend" : "sideways",
      });
      setIsLoading(false);
    }, 400 + Math.random() * 300);

    return () => clearTimeout(timer);
  }, [symbol]);

  if (isLoading) {
    return (
      <div className={clsx(
        "bg-terminal-surface rounded-lg animate-pulse",
        compact ? "h-10" : "h-32"
      )} />
    );
  }

  if (!sentiment) return null;

  const sentimentConfig = {
    bullish: { color: "text-bull", bg: "bg-bull/10", icon: "🐂", label: "Bullish" },
    slightly_bullish: { color: "text-bull/70", bg: "bg-bull/5", icon: "📈", label: "Slightly Bullish" },
    neutral: { color: "text-terminal-muted", bg: "bg-terminal-surface", icon: "➡️", label: "Neutral" },
    slightly_bearish: { color: "text-bear/70", bg: "bg-bear/5", icon: "📉", label: "Slightly Bearish" },
    bearish: { color: "text-bear", bg: "bg-bear/10", icon: "🐻", label: "Bearish" },
  };

  const config = sentimentConfig[sentiment.sentiment as keyof typeof sentimentConfig] || sentimentConfig.neutral;

  if (compact) {
    return (
      <motion.div
        initial={{ opacity: 0, x: -10 }}
        animate={{ opacity: 1, x: 0 }}
        className="flex items-center justify-between p-2 bg-terminal-surface rounded-lg"
      >
        <div className="flex items-center gap-2">
          <span>{config.icon}</span>
          <span className="font-mono text-sm">{symbol}</span>
        </div>
        <div className="flex items-center gap-3">
          {/* Mini gauge */}
          <div className="w-20 h-1.5 bg-terminal-elevated rounded-full overflow-hidden">
            <motion.div
              initial={{ width: 0 }}
              animate={{ width: `${sentiment.score}%` }}
              transition={{ duration: 0.8 }}
              className={clsx(
                "h-full rounded-full",
                sentiment.score > 60 ? "bg-bull" : sentiment.score < 40 ? "bg-bear" : "bg-terminal-muted"
              )}
            />
          </div>
          <span className={clsx("text-xs font-medium", config.color)}>
            {config.label}
          </span>
        </div>
      </motion.div>
    );
  }

  return (
    <div className={clsx("rounded-xl p-4 border", config.bg, "border-terminal-border")}>
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <span className="text-2xl">{config.icon}</span>
          <div>
            <h4 className="font-mono font-bold">{symbol}</h4>
            <span className={clsx("text-sm", config.color)}>{config.label}</span>
          </div>
        </div>
        <div className="text-right">
          <div className="text-3xl font-bold font-mono">{sentiment.score}</div>
          <div className="text-xs text-terminal-muted">Sentiment Score</div>
        </div>
      </div>

      {/* Sentiment gauge */}
      <div className="mb-4">
        <div className="relative h-3 bg-terminal-elevated rounded-full overflow-hidden">
          {/* Gradient background */}
          <div className="absolute inset-0 bg-gradient-to-r from-bear via-terminal-muted to-bull opacity-30" />
          
          {/* Indicator */}
          <motion.div
            initial={{ left: "50%" }}
            animate={{ left: `${sentiment.score}%` }}
            transition={{ duration: 1, ease: "easeOut" }}
            className="absolute top-1/2 -translate-y-1/2 -translate-x-1/2 w-4 h-4 bg-white rounded-full shadow-lg border-2 border-terminal-bg"
          />
        </div>
        <div className="flex justify-between text-xs text-terminal-muted mt-1">
          <span>Bearish</span>
          <span>Neutral</span>
          <span>Bullish</span>
        </div>
      </div>

      {/* Buy/Sell pressure */}
      <div className="grid grid-cols-2 gap-3 mb-4">
        <div className="bg-bull/10 rounded-lg p-2">
          <div className="text-xs text-terminal-muted mb-1">Buy Pressure</div>
          <div className="flex items-center gap-2">
            <span className="text-bull text-lg font-bold font-mono">
              {sentiment.buy_pressure.toFixed(1)}%
            </span>
            <div className="flex-1 h-1.5 bg-terminal-elevated rounded-full overflow-hidden">
              <motion.div
                initial={{ width: 0 }}
                animate={{ width: `${sentiment.buy_pressure}%` }}
                className="h-full bg-bull rounded-full"
              />
            </div>
          </div>
        </div>
        <div className="bg-bear/10 rounded-lg p-2">
          <div className="text-xs text-terminal-muted mb-1">Sell Pressure</div>
          <div className="flex items-center gap-2">
            <span className="text-bear text-lg font-bold font-mono">
              {sentiment.sell_pressure.toFixed(1)}%
            </span>
            <div className="flex-1 h-1.5 bg-terminal-elevated rounded-full overflow-hidden">
              <motion.div
                initial={{ width: 0 }}
                animate={{ width: `${sentiment.sell_pressure}%` }}
                className="h-full bg-bear rounded-full"
              />
            </div>
          </div>
        </div>
      </div>

      {/* Trends */}
      <div className="flex gap-2">
        <TrendBadge label="Volume" value={sentiment.volume_trend} />
        <TrendBadge label="Price" value={sentiment.price_trend} />
      </div>
    </div>
  );
}

interface TrendBadgeProps {
  label: string;
  value: string;
}

function TrendBadge({ label, value }: TrendBadgeProps) {
  const trendConfig: Record<string, { icon: string; color: string }> = {
    increasing: { icon: "📈", color: "text-bull" },
    decreasing: { icon: "📉", color: "text-bear" },
    stable: { icon: "➡️", color: "text-terminal-muted" },
    uptrend: { icon: "🔼", color: "text-bull" },
    downtrend: { icon: "🔽", color: "text-bear" },
    sideways: { icon: "◀▶", color: "text-terminal-muted" },
  };

  const config = trendConfig[value] || trendConfig.stable;

  return (
    <div className="flex-1 bg-terminal-surface rounded-lg p-2 text-center">
      <div className="text-xs text-terminal-muted">{label}</div>
      <div className={clsx("text-sm font-medium capitalize flex items-center justify-center gap-1", config.color)}>
        <span>{config.icon}</span>
        <span>{value}</span>
      </div>
    </div>
  );
}

