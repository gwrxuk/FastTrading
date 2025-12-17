"use client";

import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import clsx from "clsx";

interface RiskScore {
  overall_score: number;
  level: "low" | "medium" | "high" | "critical";
  factors: Record<string, number>;
  recommendations: string[];
}

interface RiskScoreCardProps {
  detailed?: boolean;
}

export function RiskScoreCard({ detailed = false }: RiskScoreCardProps) {
  const [riskScore, setRiskScore] = useState<RiskScore | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // Simulate API call with mock data
    const timer = setTimeout(() => {
      setRiskScore({
        overall_score: 4.2,
        level: "medium",
        factors: {
          trading_volume: 3.5,
          trading_frequency: 2.1,
          concentration: 6.2,
          volatility: 4.8,
        },
        recommendations: [
          "Diversify portfolio to reduce concentration risk",
          "Consider setting stop-loss orders for volatile positions",
          "Monitor large position exposure in ETH-USDT",
        ],
      });
      setIsLoading(false);
    }, 500);

    return () => clearTimeout(timer);
  }, []);

  if (isLoading) {
    return (
      <div className="bg-terminal-elevated rounded-xl p-6 border border-terminal-border animate-pulse">
        <div className="h-6 w-32 bg-terminal-surface rounded mb-4" />
        <div className="h-24 w-24 bg-terminal-surface rounded-full mx-auto mb-4" />
        <div className="h-4 w-48 bg-terminal-surface rounded mx-auto" />
      </div>
    );
  }

  if (!riskScore) return null;

  const levelConfig = {
    low: { color: "text-bull", bg: "bg-bull/10", border: "border-bull/30", label: "Low Risk" },
    medium: { color: "text-yellow-500", bg: "bg-yellow-500/10", border: "border-yellow-500/30", label: "Medium Risk" },
    high: { color: "text-orange-500", bg: "bg-orange-500/10", border: "border-orange-500/30", label: "High Risk" },
    critical: { color: "text-bear", bg: "bg-bear/10", border: "border-bear/30", label: "Critical Risk" },
  };

  const config = levelConfig[riskScore.level];
  const circumference = 2 * Math.PI * 45;
  const strokeDashoffset = circumference - (riskScore.overall_score / 10) * circumference;

  return (
    <div className={clsx(
      "bg-terminal-elevated rounded-xl p-6 border",
      config.border
    )}>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h3 className="font-semibold text-lg flex items-center gap-2">
            <span>🛡️</span> Risk Assessment
          </h3>
          <p className="text-sm text-terminal-muted">Real-time portfolio risk analysis</p>
        </div>
        <span className={clsx(
          "px-3 py-1 rounded-full text-sm font-medium",
          config.bg,
          config.color
        )}>
          {config.label}
        </span>
      </div>

      <div className={clsx("flex gap-8", detailed ? "flex-col lg:flex-row" : "items-center")}>
        {/* Risk Score Circle */}
        <div className="relative w-32 h-32 mx-auto lg:mx-0 flex-shrink-0">
          <svg className="w-full h-full transform -rotate-90">
            {/* Background circle */}
            <circle
              cx="64"
              cy="64"
              r="45"
              fill="none"
              stroke="currentColor"
              strokeWidth="8"
              className="text-terminal-surface"
            />
            {/* Progress circle */}
            <motion.circle
              cx="64"
              cy="64"
              r="45"
              fill="none"
              stroke="currentColor"
              strokeWidth="8"
              strokeLinecap="round"
              className={config.color}
              initial={{ strokeDashoffset: circumference }}
              animate={{ strokeDashoffset }}
              transition={{ duration: 1.5, ease: "easeOut" }}
              style={{
                strokeDasharray: circumference,
              }}
            />
          </svg>
          <div className="absolute inset-0 flex flex-col items-center justify-center">
            <motion.span
              initial={{ opacity: 0, scale: 0.5 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: 0.5 }}
              className="text-3xl font-bold font-mono"
            >
              {riskScore.overall_score.toFixed(1)}
            </motion.span>
            <span className="text-xs text-terminal-muted">out of 10</span>
          </div>
        </div>

        {/* Risk Factors */}
        {detailed && (
          <div className="flex-1 space-y-3">
            <h4 className="text-sm font-medium text-terminal-muted mb-2">Risk Factors</h4>
            {Object.entries(riskScore.factors).map(([key, value]) => (
              <div key={key} className="space-y-1">
                <div className="flex justify-between text-sm">
                  <span className="text-terminal-muted capitalize">
                    {key.replace(/_/g, " ")}
                  </span>
                  <span className="font-mono">{value.toFixed(1)}</span>
                </div>
                <div className="h-1.5 bg-terminal-surface rounded-full overflow-hidden">
                  <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: `${value * 10}%` }}
                    transition={{ duration: 1, ease: "easeOut" }}
                    className={clsx(
                      "h-full rounded-full",
                      value < 4 ? "bg-bull" : value < 7 ? "bg-yellow-500" : "bg-bear"
                    )}
                  />
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Recommendations */}
        {detailed && riskScore.recommendations.length > 0 && (
          <div className="flex-1">
            <h4 className="text-sm font-medium text-terminal-muted mb-3">AI Recommendations</h4>
            <ul className="space-y-2">
              {riskScore.recommendations.map((rec, index) => (
                <motion.li
                  key={index}
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: 0.1 * index }}
                  className="flex items-start gap-2 text-sm"
                >
                  <span className="text-accent-primary mt-0.5">→</span>
                  <span className="text-terminal-muted">{rec}</span>
                </motion.li>
              ))}
            </ul>
          </div>
        )}
      </div>

      {/* Quick Stats */}
      {!detailed && (
        <div className="mt-6 pt-4 border-t border-terminal-border grid grid-cols-4 gap-4 text-center">
          {Object.entries(riskScore.factors).map(([key, value]) => (
            <div key={key}>
              <div className={clsx(
                "text-lg font-bold font-mono",
                value < 4 ? "text-bull" : value < 7 ? "text-yellow-500" : "text-bear"
              )}>
                {value.toFixed(1)}
              </div>
              <div className="text-xs text-terminal-muted capitalize">
                {key.replace(/_/g, " ").split(" ")[0]}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

