"use client";

import { Header } from "@/components/layout/Header";
import { TradingView } from "@/components/trading/TradingView";
import { OrderBook } from "@/components/trading/OrderBook";
import { OrderForm } from "@/components/trading/OrderForm";
import { RecentTrades } from "@/components/trading/RecentTrades";
import { UserOrders } from "@/components/trading/UserOrders";
import { MarketOverview } from "@/components/market/MarketOverview";
import { motion } from "framer-motion";

export default function Home() {
  return (
    <main className="min-h-screen bg-terminal-bg grid-pattern">
      <Header />
      
      <div className="container mx-auto px-4 py-4">
        {/* Market Overview Banner */}
        <motion.div 
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-4"
        >
          <MarketOverview />
        </motion.div>

        {/* Main Trading Grid */}
        <div className="grid grid-cols-12 gap-4">
          {/* Left Column - Order Book */}
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.1 }}
            className="col-span-12 lg:col-span-3"
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
            className="col-span-12 lg:col-span-6"
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
            className="col-span-12 lg:col-span-3 space-y-4"
          >
            <div className="trading-card panel-glow">
              <OrderForm symbol="ETH-USDT" />
            </div>
            <div className="trading-card panel-glow h-[250px]">
              <RecentTrades symbol="ETH-USDT" />
            </div>
          </motion.div>
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
      </div>
    </main>
  );
}

