"use client";

import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import clsx from "clsx";

interface Position {
  symbol: string;
  quantity: number;
  avg_price: number;
  current_price: number;
  value_usd: number;
  unrealized_pnl: number;
  unrealized_pnl_percent: number;
}

interface TradingMetrics {
  total_trades: number;
  winning_trades: number;
  losing_trades: number;
  win_rate: number;
  avg_profit: number;
  avg_loss: number;
  profit_factor: number;
  sharpe_ratio: number;
  max_drawdown: number;
}

interface AIInsight {
  type: string;
  title: string;
  description: string;
  importance: string;
  action?: string;
}

interface PortfolioAnalysis {
  total_value: number;
  total_pnl: number;
  total_pnl_percent: number;
  positions: Position[];
  metrics: TradingMetrics;
  insights: AIInsight[];
}

export function PortfolioInsights() {
  const [portfolio, setPortfolio] = useState<PortfolioAnalysis | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [activeView, setActiveView] = useState<"overview" | "positions" | "metrics">("overview");

  useEffect(() => {
    // Simulate API call with mock data
    const timer = setTimeout(() => {
      setPortfolio({
        total_value: 125450.75,
        total_pnl: 12340.50,
        total_pnl_percent: 10.92,
        positions: [
          {
            symbol: "ETH-USDT",
            quantity: 25.5,
            avg_price: 2150.00,
            current_price: 2256.78,
            value_usd: 57547.89,
            unrealized_pnl: 2722.89,
            unrealized_pnl_percent: 4.97,
          },
          {
            symbol: "BTC-USDT",
            quantity: 1.25,
            avg_price: 41000.00,
            current_price: 43250.00,
            value_usd: 54062.50,
            unrealized_pnl: 2812.50,
            unrealized_pnl_percent: 5.49,
          },
          {
            symbol: "SOL-USDT",
            quantity: 150,
            avg_price: 85.00,
            current_price: 92.27,
            value_usd: 13840.36,
            unrealized_pnl: 1090.36,
            unrealized_pnl_percent: 8.56,
          },
        ],
        metrics: {
          total_trades: 156,
          winning_trades: 98,
          losing_trades: 58,
          win_rate: 62.82,
          avg_profit: 485.50,
          avg_loss: 312.25,
          profit_factor: 1.86,
          sharpe_ratio: 1.42,
          max_drawdown: 12.5,
        },
        insights: [
          {
            type: "performance",
            title: "Strong Win Rate",
            description: "Your win rate of 62.82% indicates good trade selection.",
            importance: "low",
            action: "Maintain current strategy while monitoring for market changes",
          },
          {
            type: "risk",
            title: "High Concentration Risk",
            description: "ETH-USDT represents 46% of your portfolio.",
            importance: "high",
            action: "Consider reducing ETH-USDT position to improve diversification",
          },
          {
            type: "opportunity",
            title: "Large Unrealized Gain",
            description: "SOL-USDT has 8.56% unrealized gain.",
            importance: "medium",
            action: "Consider taking partial profits to lock in gains",
          },
        ],
      });
      setIsLoading(false);
    }, 800);

    return () => clearTimeout(timer);
  }, []);

  if (isLoading) {
    return (
      <div className="space-y-4">
        <div className="h-32 bg-terminal-surface rounded-xl animate-pulse" />
        <div className="grid grid-cols-3 gap-4">
          {[...Array(3)].map((_, i) => (
            <div key={i} className="h-24 bg-terminal-surface rounded-xl animate-pulse" />
          ))}
        </div>
      </div>
    );
  }

  if (!portfolio) return null;

  return (
    <div className="space-y-4">
      {/* Portfolio Summary */}
      <div className="bg-gradient-to-br from-purple-500/10 to-cyan-500/10 rounded-xl p-6 border border-purple-500/20">
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-semibold text-lg flex items-center gap-2">
            <span>💼</span> Portfolio Overview
          </h3>
          <div className="flex gap-1 p-1 bg-terminal-surface rounded-lg">
            {(["overview", "positions", "metrics"] as const).map((view) => (
              <button
                key={view}
                onClick={() => setActiveView(view)}
                className={clsx(
                  "px-3 py-1 rounded text-xs font-medium transition-all capitalize",
                  activeView === view
                    ? "bg-accent-primary text-terminal-bg"
                    : "text-terminal-muted hover:text-white"
                )}
              >
                {view}
              </button>
            ))}
          </div>
        </div>

        {/* Summary stats */}
        <div className="grid grid-cols-3 gap-4">
          <div>
            <div className="text-sm text-terminal-muted mb-1">Total Value</div>
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="text-2xl font-bold font-mono"
            >
              ${portfolio.total_value.toLocaleString()}
            </motion.div>
          </div>
          <div>
            <div className="text-sm text-terminal-muted mb-1">Total P&L</div>
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className={clsx(
                "text-2xl font-bold font-mono",
                portfolio.total_pnl >= 0 ? "text-bull" : "text-bear"
              )}
            >
              {portfolio.total_pnl >= 0 ? "+" : ""}${portfolio.total_pnl.toLocaleString()}
            </motion.div>
          </div>
          <div>
            <div className="text-sm text-terminal-muted mb-1">Return</div>
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className={clsx(
                "text-2xl font-bold font-mono",
                portfolio.total_pnl_percent >= 0 ? "text-bull" : "text-bear"
              )}
            >
              {portfolio.total_pnl_percent >= 0 ? "+" : ""}{portfolio.total_pnl_percent.toFixed(2)}%
            </motion.div>
          </div>
        </div>
      </div>

      {/* View content */}
      {activeView === "overview" && (
        <OverviewView portfolio={portfolio} />
      )}
      {activeView === "positions" && (
        <PositionsView positions={portfolio.positions} />
      )}
      {activeView === "metrics" && (
        <MetricsView metrics={portfolio.metrics} />
      )}
    </div>
  );
}

function OverviewView({ portfolio }: { portfolio: PortfolioAnalysis }) {
  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
      {/* AI Insights */}
      <div className="bg-terminal-elevated rounded-xl p-4 border border-terminal-border">
        <h4 className="font-semibold mb-3 flex items-center gap-2">
          <span>🧠</span> AI Insights
        </h4>
        <div className="space-y-3">
          {portfolio.insights.map((insight, index) => {
            const importanceConfig = {
              low: { icon: "✓", color: "text-bull", bg: "bg-bull/10" },
              medium: { icon: "!", color: "text-yellow-500", bg: "bg-yellow-500/10" },
              high: { icon: "⚠", color: "text-orange-500", bg: "bg-orange-500/10" },
              critical: { icon: "🚨", color: "text-bear", bg: "bg-bear/10" },
            };
            const config = importanceConfig[insight.importance as keyof typeof importanceConfig] || importanceConfig.medium;

            return (
              <motion.div
                key={index}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: index * 0.1 }}
                className={clsx("p-3 rounded-lg", config.bg)}
              >
                <div className="flex items-start gap-2">
                  <span className={clsx("text-sm", config.color)}>{config.icon}</span>
                  <div>
                    <div className={clsx("font-medium text-sm", config.color)}>
                      {insight.title}
                    </div>
                    <p className="text-xs text-terminal-muted mt-1">
                      {insight.description}
                    </p>
                    {insight.action && (
                      <p className="text-xs text-accent-primary mt-2">
                        → {insight.action}
                      </p>
                    )}
                  </div>
                </div>
              </motion.div>
            );
          })}
        </div>
      </div>

      {/* Quick Metrics */}
      <div className="bg-terminal-elevated rounded-xl p-4 border border-terminal-border">
        <h4 className="font-semibold mb-3 flex items-center gap-2">
          <span>📊</span> Quick Stats
        </h4>
        <div className="grid grid-cols-2 gap-3">
          <MetricCard
            label="Win Rate"
            value={`${portfolio.metrics.win_rate.toFixed(1)}%`}
            trend={portfolio.metrics.win_rate > 50 ? "up" : "down"}
          />
          <MetricCard
            label="Profit Factor"
            value={portfolio.metrics.profit_factor.toFixed(2)}
            trend={portfolio.metrics.profit_factor > 1 ? "up" : "down"}
          />
          <MetricCard
            label="Sharpe Ratio"
            value={portfolio.metrics.sharpe_ratio.toFixed(2)}
            trend={portfolio.metrics.sharpe_ratio > 1 ? "up" : "down"}
          />
          <MetricCard
            label="Max Drawdown"
            value={`${portfolio.metrics.max_drawdown.toFixed(1)}%`}
            trend="down"
          />
        </div>
      </div>
    </div>
  );
}

function PositionsView({ positions }: { positions: Position[] }) {
  return (
    <div className="space-y-3">
      {positions.map((position, index) => (
        <motion.div
          key={position.symbol}
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: index * 0.1 }}
          className="bg-terminal-elevated rounded-xl p-4 border border-terminal-border"
        >
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-full bg-gradient-to-br from-purple-500 to-cyan-500 flex items-center justify-center font-bold text-sm">
                {position.symbol.split("-")[0].slice(0, 2)}
              </div>
              <div>
                <div className="font-mono font-bold">{position.symbol}</div>
                <div className="text-xs text-terminal-muted">
                  {position.quantity} @ ${position.avg_price.toFixed(2)}
                </div>
              </div>
            </div>
            <div className="text-right">
              <div className="font-mono font-bold">
                ${position.value_usd.toLocaleString()}
              </div>
              <div className={clsx(
                "text-sm font-mono",
                position.unrealized_pnl >= 0 ? "text-bull" : "text-bear"
              )}>
                {position.unrealized_pnl >= 0 ? "+" : ""}${position.unrealized_pnl.toFixed(2)}
                <span className="text-xs ml-1">
                  ({position.unrealized_pnl_percent >= 0 ? "+" : ""}{position.unrealized_pnl_percent.toFixed(2)}%)
                </span>
              </div>
            </div>
          </div>

          {/* Position bar */}
          <div className="mt-3">
            <div className="flex justify-between text-xs text-terminal-muted mb-1">
              <span>Entry: ${position.avg_price.toFixed(2)}</span>
              <span>Current: ${position.current_price.toFixed(2)}</span>
            </div>
            <div className="h-1.5 bg-terminal-surface rounded-full overflow-hidden">
              <motion.div
                initial={{ width: 0 }}
                animate={{ 
                  width: `${Math.min(100, (position.current_price / position.avg_price) * 50)}%` 
                }}
                className={clsx(
                  "h-full rounded-full",
                  position.unrealized_pnl >= 0 ? "bg-bull" : "bg-bear"
                )}
              />
            </div>
          </div>
        </motion.div>
      ))}
    </div>
  );
}

function MetricsView({ metrics }: { metrics: TradingMetrics }) {
  return (
    <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
      <MetricCard label="Total Trades" value={metrics.total_trades.toString()} />
      <MetricCard label="Winning Trades" value={metrics.winning_trades.toString()} trend="up" />
      <MetricCard label="Losing Trades" value={metrics.losing_trades.toString()} trend="down" />
      <MetricCard label="Win Rate" value={`${metrics.win_rate.toFixed(1)}%`} trend={metrics.win_rate > 50 ? "up" : "down"} />
      <MetricCard label="Avg Profit" value={`$${metrics.avg_profit.toFixed(2)}`} trend="up" />
      <MetricCard label="Avg Loss" value={`$${metrics.avg_loss.toFixed(2)}`} trend="down" />
      <MetricCard label="Profit Factor" value={metrics.profit_factor.toFixed(2)} trend={metrics.profit_factor > 1 ? "up" : "down"} />
      <MetricCard label="Sharpe Ratio" value={metrics.sharpe_ratio.toFixed(2)} trend={metrics.sharpe_ratio > 1 ? "up" : "down"} />
      <MetricCard label="Max Drawdown" value={`${metrics.max_drawdown.toFixed(1)}%`} trend="down" />
    </div>
  );
}

interface MetricCardProps {
  label: string;
  value: string;
  trend?: "up" | "down";
}

function MetricCard({ label, value, trend }: MetricCardProps) {
  return (
    <div className="bg-terminal-elevated rounded-xl p-4 border border-terminal-border">
      <div className="text-xs text-terminal-muted mb-1">{label}</div>
      <div className="flex items-center gap-2">
        <span className={clsx(
          "text-xl font-bold font-mono",
          trend === "up" ? "text-bull" : trend === "down" ? "text-bear" : "text-white"
        )}>
          {value}
        </span>
        {trend && (
          <span className={trend === "up" ? "text-bull" : "text-bear"}>
            {trend === "up" ? "↑" : "↓"}
          </span>
        )}
      </div>
    </div>
  );
}

