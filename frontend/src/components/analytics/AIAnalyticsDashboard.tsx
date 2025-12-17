"use client";

import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import clsx from "clsx";
import { RiskScoreCard } from "./RiskScoreCard";
import { AnomalyAlerts } from "./AnomalyAlerts";
import { PricePredictions } from "./PricePredictions";
import { PortfolioInsights } from "./PortfolioInsights";
import { MarketSentiment } from "./MarketSentiment";

interface AIAnalyticsDashboardProps {
  symbols?: string[];
}

const TABS = [
  { id: "overview", label: "Overview", icon: "📊" },
  { id: "risk", label: "Risk Analysis", icon: "⚠️" },
  { id: "predictions", label: "AI Predictions", icon: "🔮" },
  { id: "anomalies", label: "Anomalies", icon: "🚨" },
  { id: "portfolio", label: "Portfolio", icon: "💼" },
] as const;

export function AIAnalyticsDashboard({ symbols = ["ETH-USDT", "BTC-USDT"] }: AIAnalyticsDashboardProps) {
  const [activeTab, setActiveTab] = useState<string>("overview");
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // Simulate initial load
    const timer = setTimeout(() => setIsLoading(false), 1000);
    return () => clearTimeout(timer);
  }, []);

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-purple-500 to-cyan-500 flex items-center justify-center">
            <span className="text-xl">🤖</span>
          </div>
          <div>
            <h2 className="font-display font-bold text-lg">AI Analytics</h2>
            <p className="text-xs text-terminal-muted">Real-time insights powered by AI</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <div className="flex items-center gap-1.5 px-3 py-1.5 bg-terminal-elevated rounded-lg">
            <span className="w-2 h-2 bg-bull rounded-full animate-pulse" />
            <span className="text-xs text-terminal-muted">Live Analysis</span>
          </div>
        </div>
      </div>

      {/* Tab Navigation */}
      <div className="flex gap-1 p-1 bg-terminal-elevated rounded-xl mb-4 overflow-x-auto">
        {TABS.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={clsx(
              "flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all whitespace-nowrap",
              activeTab === tab.id
                ? "bg-gradient-to-r from-purple-500/20 to-cyan-500/20 text-white border border-purple-500/30"
                : "text-terminal-muted hover:text-white hover:bg-terminal-surface"
            )}
          >
            <span>{tab.icon}</span>
            <span>{tab.label}</span>
          </button>
        ))}
      </div>

      {/* Tab Content */}
      <div className="flex-1 overflow-hidden">
        <AnimatePresence mode="wait">
          {isLoading ? (
            <motion.div
              key="loading"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="h-full flex items-center justify-center"
            >
              <div className="flex flex-col items-center gap-4">
                <div className="w-16 h-16 border-4 border-purple-500/20 border-t-purple-500 rounded-full animate-spin" />
                <p className="text-terminal-muted">Analyzing market data...</p>
              </div>
            </motion.div>
          ) : (
            <motion.div
              key={activeTab}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              transition={{ duration: 0.2 }}
              className="h-full overflow-y-auto"
            >
              {activeTab === "overview" && (
                <OverviewTab symbols={symbols} />
              )}
              {activeTab === "risk" && (
                <RiskTab />
              )}
              {activeTab === "predictions" && (
                <PricePredictions symbols={symbols} />
              )}
              {activeTab === "anomalies" && (
                <AnomalyAlerts />
              )}
              {activeTab === "portfolio" && (
                <PortfolioInsights />
              )}
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}

function OverviewTab({ symbols }: { symbols: string[] }) {
  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
      {/* Risk Score Card */}
      <div className="lg:col-span-2">
        <RiskScoreCard />
      </div>

      {/* Market Sentiment */}
      <div className="bg-terminal-elevated rounded-xl p-4 border border-terminal-border">
        <h3 className="font-semibold mb-3 flex items-center gap-2">
          <span>📈</span> Market Sentiment
        </h3>
        <div className="space-y-3">
          {symbols.map((symbol) => (
            <MarketSentiment key={symbol} symbol={symbol} compact />
          ))}
        </div>
      </div>

      {/* Quick Predictions */}
      <div className="bg-terminal-elevated rounded-xl p-4 border border-terminal-border">
        <h3 className="font-semibold mb-3 flex items-center gap-2">
          <span>🔮</span> Price Predictions
        </h3>
        <PricePredictions symbols={symbols} compact />
      </div>

      {/* Recent Anomalies */}
      <div className="lg:col-span-2">
        <AnomalyAlerts limit={3} compact />
      </div>
    </div>
  );
}

function RiskTab() {
  return (
    <div className="space-y-4">
      <RiskScoreCard detailed />
      
      {/* Risk Breakdown */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <RiskFactorCard
          title="Trading Volume"
          value={3.5}
          description="Moderate trading activity"
          trend="stable"
        />
        <RiskFactorCard
          title="Concentration"
          value={6.2}
          description="High portfolio concentration"
          trend="warning"
        />
        <RiskFactorCard
          title="Volatility"
          value={4.8}
          description="Average market exposure"
          trend="stable"
        />
        <RiskFactorCard
          title="Frequency"
          value={2.1}
          description="Conservative trading pace"
          trend="good"
        />
      </div>
    </div>
  );
}

interface RiskFactorCardProps {
  title: string;
  value: number;
  description: string;
  trend: "good" | "stable" | "warning";
}

function RiskFactorCard({ title, value, description, trend }: RiskFactorCardProps) {
  const trendColors = {
    good: "text-bull",
    stable: "text-accent-primary",
    warning: "text-bear",
  };

  return (
    <div className="bg-terminal-elevated rounded-xl p-4 border border-terminal-border">
      <div className="flex items-center justify-between mb-2">
        <span className="text-terminal-muted text-sm">{title}</span>
        <span className={clsx("text-xs font-medium", trendColors[trend])}>
          {trend === "good" ? "✓ Low Risk" : trend === "warning" ? "⚠ High Risk" : "● Moderate"}
        </span>
      </div>
      <div className="flex items-end gap-2 mb-2">
        <span className="text-2xl font-bold font-mono">{value.toFixed(1)}</span>
        <span className="text-terminal-muted text-sm">/10</span>
      </div>
      <p className="text-xs text-terminal-muted">{description}</p>
      
      {/* Progress bar */}
      <div className="mt-3 h-1.5 bg-terminal-surface rounded-full overflow-hidden">
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
  );
}

