"use client";

import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import clsx from "clsx";

interface Anomaly {
  id: string;
  type: string;
  symbol: string;
  severity: number;
  description: string;
  detected_at: string;
  recommendation?: string;
  metrics: Record<string, number>;
}

interface AnomalyAlertsProps {
  limit?: number;
  compact?: boolean;
}

const ANOMALY_ICONS: Record<string, string> = {
  volume_spike: "📊",
  large_trade: "🐋",
  rapid_trading: "⚡",
  wash_trading: "🔄",
  price_deviation: "📉",
  unusual_pattern: "🔍",
};

const SEVERITY_CONFIG = {
  low: { color: "text-yellow-500", bg: "bg-yellow-500/10", border: "border-yellow-500/20" },
  medium: { color: "text-orange-500", bg: "bg-orange-500/10", border: "border-orange-500/20" },
  high: { color: "text-bear", bg: "bg-bear/10", border: "border-bear/20" },
};

export function AnomalyAlerts({ limit = 10, compact = false }: AnomalyAlertsProps) {
  const [anomalies, setAnomalies] = useState<Anomaly[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [expandedId, setExpandedId] = useState<string | null>(null);

  useEffect(() => {
    // Simulate API call with mock data
    const timer = setTimeout(() => {
      setAnomalies([
        {
          id: "1",
          type: "volume_spike",
          symbol: "ETH-USDT",
          severity: 7,
          description: "Volume spike detected: 3.2x average volume",
          detected_at: new Date(Date.now() - 1000 * 60 * 5).toISOString(),
          recommendation: "Monitor for potential market manipulation or significant news event",
          metrics: { volume: 1250000, average_volume: 390000, spike_ratio: 3.2 },
        },
        {
          id: "2",
          type: "large_trade",
          symbol: "BTC-USDT",
          severity: 6,
          description: "Large trade detected: 2.8x average size",
          detected_at: new Date(Date.now() - 1000 * 60 * 15).toISOString(),
          recommendation: "Review for market impact and potential whale activity",
          metrics: { trade_size: 45000, average_size: 16000, trade_value: 2850000 },
        },
        {
          id: "3",
          type: "rapid_trading",
          symbol: "ETH-USDT",
          severity: 5,
          description: "Rapid trading: 15 trades in 1 minute",
          detected_at: new Date(Date.now() - 1000 * 60 * 30).toISOString(),
          recommendation: "Review for automated trading or potential market manipulation",
          metrics: { trades_per_minute: 15, threshold: 10 },
        },
        {
          id: "4",
          type: "wash_trading",
          symbol: "SOL-USDT",
          severity: 8,
          description: "Potential wash trading: buy/sell ratio 94%",
          detected_at: new Date(Date.now() - 1000 * 60 * 45).toISOString(),
          recommendation: "Investigate for potential wash trading or self-dealing",
          metrics: { buy_volume: 125000, sell_volume: 118000, match_ratio: 0.94 },
        },
      ].slice(0, limit));
      setIsLoading(false);
    }, 600);

    return () => clearTimeout(timer);
  }, [limit]);

  const getSeverityLevel = (severity: number): "low" | "medium" | "high" => {
    if (severity < 4) return "low";
    if (severity < 7) return "medium";
    return "high";
  };

  const formatTime = (isoString: string) => {
    const date = new Date(isoString);
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const minutes = Math.floor(diff / 60000);
    
    if (minutes < 1) return "Just now";
    if (minutes < 60) return `${minutes}m ago`;
    if (minutes < 1440) return `${Math.floor(minutes / 60)}h ago`;
    return `${Math.floor(minutes / 1440)}d ago`;
  };

  if (isLoading) {
    return (
      <div className={clsx(
        "bg-terminal-elevated rounded-xl border border-terminal-border",
        compact ? "p-3" : "p-4"
      )}>
        <div className="flex items-center justify-between mb-4">
          <div className="h-5 w-32 bg-terminal-surface rounded animate-pulse" />
          <div className="h-5 w-16 bg-terminal-surface rounded animate-pulse" />
        </div>
        {[...Array(3)].map((_, i) => (
          <div key={i} className="h-16 bg-terminal-surface rounded-lg mb-2 animate-pulse" />
        ))}
      </div>
    );
  }

  return (
    <div className={clsx(
      "bg-terminal-elevated rounded-xl border border-terminal-border",
      compact ? "p-3" : "p-4"
    )}>
      <div className="flex items-center justify-between mb-4">
        <h3 className={clsx("font-semibold flex items-center gap-2", compact && "text-sm")}>
          <span>🚨</span> Anomaly Detection
        </h3>
        <span className="text-xs text-terminal-muted bg-terminal-surface px-2 py-1 rounded-full">
          {anomalies.length} alerts
        </span>
      </div>

      {anomalies.length === 0 ? (
        <div className="text-center py-8">
          <span className="text-3xl mb-2 block">✅</span>
          <p className="text-terminal-muted text-sm">No anomalies detected</p>
        </div>
      ) : (
        <div className="space-y-2">
          <AnimatePresence>
            {anomalies.map((anomaly, index) => {
              const level = getSeverityLevel(anomaly.severity);
              const config = SEVERITY_CONFIG[level];
              const isExpanded = expandedId === anomaly.id;

              return (
                <motion.div
                  key={anomaly.id}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -10 }}
                  transition={{ delay: index * 0.05 }}
                  className={clsx(
                    "rounded-lg border cursor-pointer transition-all",
                    config.border,
                    config.bg,
                    isExpanded && "ring-1 ring-accent-primary/50"
                  )}
                  onClick={() => setExpandedId(isExpanded ? null : anomaly.id)}
                >
                  <div className={clsx("flex items-center gap-3", compact ? "p-2" : "p-3")}>
                    <span className="text-xl">
                      {ANOMALY_ICONS[anomaly.type] || "⚠️"}
                    </span>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <span className="font-mono text-xs text-accent-primary">
                          {anomaly.symbol}
                        </span>
                        <span className={clsx(
                          "px-1.5 py-0.5 rounded text-xs font-medium",
                          config.color,
                          config.bg
                        )}>
                          Severity: {anomaly.severity}/10
                        </span>
                      </div>
                      <p className={clsx(
                        "text-terminal-muted truncate",
                        compact ? "text-xs" : "text-sm"
                      )}>
                        {anomaly.description}
                      </p>
                    </div>
                    <span className="text-xs text-terminal-muted whitespace-nowrap">
                      {formatTime(anomaly.detected_at)}
                    </span>
                  </div>

                  {/* Expanded content */}
                  <AnimatePresence>
                    {isExpanded && !compact && (
                      <motion.div
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: "auto", opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }}
                        className="overflow-hidden"
                      >
                        <div className="px-3 pb-3 pt-1 border-t border-terminal-border/50">
                          {/* Metrics */}
                          <div className="grid grid-cols-3 gap-2 mb-3">
                            {Object.entries(anomaly.metrics).map(([key, value]) => (
                              <div key={key} className="bg-terminal-surface rounded p-2">
                                <div className="text-xs text-terminal-muted capitalize">
                                  {key.replace(/_/g, " ")}
                                </div>
                                <div className="font-mono text-sm">
                                  {typeof value === "number" 
                                    ? value > 1000 
                                      ? `${(value / 1000).toFixed(1)}K`
                                      : value.toFixed(2)
                                    : value}
                                </div>
                              </div>
                            ))}
                          </div>
                          
                          {/* Recommendation */}
                          {anomaly.recommendation && (
                            <div className="flex items-start gap-2 text-xs">
                              <span className="text-accent-primary">💡</span>
                              <span className="text-terminal-muted">
                                {anomaly.recommendation}
                              </span>
                            </div>
                          )}
                        </div>
                      </motion.div>
                    )}
                  </AnimatePresence>
                </motion.div>
              );
            })}
          </AnimatePresence>
        </div>
      )}
    </div>
  );
}

