"use client";

import { useState } from "react";
import { Header } from "@/components/layout/Header";
import { TradingView } from "@/components/trading/TradingView";
import { OrderBook } from "@/components/trading/OrderBook";
import { OrderForm } from "@/components/trading/OrderForm";
import { RecentTrades } from "@/components/trading/RecentTrades";
import { UserOrders } from "@/components/trading/UserOrders";
import { MarketOverview } from "@/components/market/MarketOverview";
import { AIAnalyticsDashboard } from "@/components/analytics";
import { motion, AnimatePresence } from "framer-motion";
import clsx from "clsx";

type ViewMode = "trading" | "analytics";

export default function Home() {
  const [viewMode, setViewMode] = useState<ViewMode>("trading");
  const [showAIPanel, setShowAIPanel] = useState(false);

  return (
    <main className="min-h-screen bg-terminal-bg grid-pattern">
      <Header />
      
      <div className="container mx-auto px-4 py-4">
        {/* View Mode Toggle & AI Quick Actions */}
        <motion.div 
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="flex items-center justify-between mb-4"
        >
          {/* View Mode Tabs */}
          <div className="flex items-center gap-2 p-1 bg-terminal-surface rounded-xl">
            <button
              onClick={() => setViewMode("trading")}
              className={clsx(
                "flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all",
                viewMode === "trading"
                  ? "bg-accent-primary text-terminal-bg"
                  : "text-terminal-muted hover:text-white"
              )}
            >
              <span>📈</span> Trading
            </button>
            <button
              onClick={() => setViewMode("analytics")}
              className={clsx(
                "flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all",
                viewMode === "analytics"
                  ? "bg-gradient-to-r from-purple-500 to-cyan-500 text-white"
                  : "text-terminal-muted hover:text-white"
              )}
            >
              <span>🤖</span> AI Analytics
            </button>
          </div>

          {/* Quick AI Toggle (visible in trading view) */}
          {viewMode === "trading" && (
            <button
              onClick={() => setShowAIPanel(!showAIPanel)}
              className={clsx(
                "flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all",
                showAIPanel
                  ? "bg-purple-500/20 text-purple-400 border border-purple-500/30"
                  : "bg-terminal-surface text-terminal-muted hover:text-white"
              )}
            >
              <span>🧠</span>
              <span className="hidden sm:inline">AI Insights</span>
              {showAIPanel ? (
                <span className="text-xs bg-purple-500/20 px-1.5 py-0.5 rounded">ON</span>
              ) : (
                <span className="text-xs bg-terminal-elevated px-1.5 py-0.5 rounded">OFF</span>
              )}
            </button>
          )}
        </motion.div>

        <AnimatePresence mode="wait">
          {viewMode === "trading" ? (
            <motion.div
              key="trading"
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 20 }}
              transition={{ duration: 0.2 }}
            >
              {/* Market Overview Banner */}
              <motion.div 
                initial={{ opacity: 0, y: -20 }}
                animate={{ opacity: 1, y: 0 }}
                className="mb-4"
              >
                <MarketOverview />
              </motion.div>

              {/* Main Trading Grid */}
              <div className={clsx(
                "grid gap-4",
                showAIPanel ? "grid-cols-12" : "grid-cols-12"
              )}>
                {/* Left Column - Order Book */}
                <motion.div
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: 0.1 }}
                  className={clsx(
                    "col-span-12",
                    showAIPanel ? "lg:col-span-2" : "lg:col-span-3"
                  )}
                >
                  <div className="trading-card panel-glow h-[600px]">
                    <OrderBook symbol="ETH-USDT" />
                  </div>
                </motion.div>

                {/* Center Column - Chart */}
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.2 }}
                  className={clsx(
                    "col-span-12",
                    showAIPanel ? "lg:col-span-5" : "lg:col-span-6"
                  )}
                >
                  <div className="trading-card panel-glow h-[600px]">
                    <TradingView symbol="ETH-USDT" />
                  </div>
                </motion.div>

                {/* Right Column - Order Form & Recent Trades */}
                <motion.div
                  initial={{ opacity: 0, x: 20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: 0.3 }}
                  className={clsx(
                    "col-span-12 space-y-4",
                    showAIPanel ? "lg:col-span-2" : "lg:col-span-3"
                  )}
                >
                  <div className="trading-card panel-glow">
                    <OrderForm symbol="ETH-USDT" />
                  </div>
                  <div className="trading-card panel-glow h-[250px]">
                    <RecentTrades symbol="ETH-USDT" />
                  </div>
                </motion.div>

                {/* AI Insights Panel (Collapsible) */}
                <AnimatePresence>
                  {showAIPanel && (
                    <motion.div
                      initial={{ opacity: 0, x: 20, width: 0 }}
                      animate={{ opacity: 1, x: 0, width: "auto" }}
                      exit={{ opacity: 0, x: 20, width: 0 }}
                      transition={{ duration: 0.3 }}
                      className="col-span-12 lg:col-span-3"
                    >
                      <div className="trading-card panel-glow h-[600px] overflow-hidden border-purple-500/20">
                        <AIQuickInsights />
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>

              {/* Bottom - User Orders */}
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.4 }}
                className="mt-4"
              >
                <div className="trading-card panel-glow">
                  <UserOrders />
                </div>
              </motion.div>
            </motion.div>
          ) : (
            <motion.div
              key="analytics"
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              transition={{ duration: 0.2 }}
            >
              <div className="trading-card panel-glow min-h-[800px]">
                <AIAnalyticsDashboard symbols={["ETH-USDT", "BTC-USDT", "SOL-USDT"]} />
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </main>
  );
}

// Quick AI Insights component for sidebar
function AIQuickInsights() {
  return (
    <div className="h-full flex flex-col p-1">
      <div className="flex items-center gap-2 mb-3">
        <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-purple-500 to-cyan-500 flex items-center justify-center">
          <span>🧠</span>
        </div>
        <div>
          <h3 className="font-semibold text-sm">AI Insights</h3>
          <p className="text-xs text-terminal-muted">Real-time analysis</p>
        </div>
      </div>

      <div className="flex-1 space-y-3 overflow-y-auto">
        {/* Risk Score Mini */}
        <QuickCard
          icon="🛡️"
          title="Risk Score"
          value="4.2"
          subtitle="Medium Risk"
          color="yellow"
        />

        {/* Sentiment Mini */}
        <QuickCard
          icon="📊"
          title="ETH Sentiment"
          value="62"
          subtitle="Bullish"
          color="green"
        />

        {/* Prediction Mini */}
        <QuickCard
          icon="🔮"
          title="ETH 1H Prediction"
          value="+1.2%"
          subtitle="75% confidence"
          color="green"
        />

        {/* Recent Alert */}
        <div className="bg-bear/10 border border-bear/20 rounded-lg p-2">
          <div className="flex items-center gap-2 mb-1">
            <span>🚨</span>
            <span className="text-xs font-medium text-bear">Alert</span>
          </div>
          <p className="text-xs text-terminal-muted">
            Volume spike detected on ETH-USDT (3.2x average)
          </p>
        </div>

        {/* AI Recommendation */}
        <div className="bg-purple-500/10 border border-purple-500/20 rounded-lg p-2">
          <div className="flex items-center gap-2 mb-1">
            <span>💡</span>
            <span className="text-xs font-medium text-purple-400">Recommendation</span>
          </div>
          <p className="text-xs text-terminal-muted">
            Consider diversifying - portfolio concentration is high
          </p>
        </div>
      </div>
    </div>
  );
}

interface QuickCardProps {
  icon: string;
  title: string;
  value: string;
  subtitle: string;
  color: "green" | "yellow" | "red";
}

function QuickCard({ icon, title, value, subtitle, color }: QuickCardProps) {
  const colorClasses = {
    green: "text-bull",
    yellow: "text-yellow-500",
    red: "text-bear",
  };

  return (
    <div className="bg-terminal-elevated rounded-lg p-2">
      <div className="flex items-center gap-2 mb-1">
        <span className="text-sm">{icon}</span>
        <span className="text-xs text-terminal-muted">{title}</span>
      </div>
      <div className="flex items-baseline gap-1">
        <span className={clsx("text-lg font-bold font-mono", colorClasses[color])}>
          {value}
        </span>
        <span className="text-xs text-terminal-muted">{subtitle}</span>
      </div>
    </div>
  );
}

