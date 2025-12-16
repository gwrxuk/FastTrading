"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import clsx from "clsx";

interface MarketTicker {
  symbol: string;
  price: number;
  change: number;
  changePercent: number;
  volume: number;
}

// Simulated market data
const MOCK_TICKERS: MarketTicker[] = [
  { symbol: "BTC-USDT", price: 42534.56, change: 1245.32, changePercent: 3.02, volume: 1234567890 },
  { symbol: "ETH-USDT", price: 2256.78, change: -45.23, changePercent: -1.96, volume: 567890123 },
  { symbol: "SOL-USDT", price: 98.45, change: 5.67, changePercent: 6.11, volume: 234567890 },
  { symbol: "AVAX-USDT", price: 35.23, change: 0.89, changePercent: 2.59, volume: 123456789 },
  { symbol: "MATIC-USDT", price: 0.8567, change: -0.0234, changePercent: -2.66, volume: 98765432 },
];

export function MarketOverview() {
  const [tickers, setTickers] = useState<MarketTicker[]>(MOCK_TICKERS);

  // Simulate real-time updates
  useEffect(() => {
    const interval = setInterval(() => {
      setTickers((prev) =>
        prev.map((ticker) => {
          const changeFactor = (Math.random() - 0.5) * 0.002;
          const newPrice = ticker.price * (1 + changeFactor);
          const priceChange = newPrice - ticker.price;
          
          return {
            ...ticker,
            price: newPrice,
            change: ticker.change + priceChange,
            changePercent: ((ticker.change + priceChange) / ticker.price) * 100,
          };
        })
      );
    }, 2000);

    return () => clearInterval(interval);
  }, []);

  return (
    <div className="flex items-center gap-6 overflow-x-auto pb-2 scrollbar-hide">
      {tickers.map((ticker, index) => (
        <motion.div
          key={ticker.symbol}
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: index * 0.05 }}
          className="flex items-center gap-4 bg-terminal-surface/50 border border-terminal-border 
                     rounded-lg px-4 py-2 min-w-[200px] hover:border-accent-primary/30 transition-colors cursor-pointer"
        >
          <div className="flex items-center gap-2">
            <CryptoIcon symbol={ticker.symbol.split("-")[0]} />
            <span className="font-medium">{ticker.symbol}</span>
          </div>
          
          <div className="text-right">
            <div className="font-mono font-semibold">
              ${formatPrice(ticker.price)}
            </div>
            <div
              className={clsx(
                "text-xs font-mono",
                ticker.changePercent >= 0 ? "text-bull" : "text-bear"
              )}
            >
              {ticker.changePercent >= 0 ? "+" : ""}
              {ticker.changePercent.toFixed(2)}%
            </div>
          </div>
        </motion.div>
      ))}
    </div>
  );
}

function CryptoIcon({ symbol }: { symbol: string }) {
  const colors: Record<string, string> = {
    BTC: "bg-[#f7931a]",
    ETH: "bg-[#627eea]",
    SOL: "bg-gradient-to-br from-[#00ffa3] to-[#dc1fff]",
    AVAX: "bg-[#e84142]",
    MATIC: "bg-[#8247e5]",
  };

  return (
    <div
      className={clsx(
        "w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold text-white",
        colors[symbol] || "bg-terminal-muted"
      )}
    >
      {symbol.charAt(0)}
    </div>
  );
}

function formatPrice(price: number): string {
  if (price >= 1000) {
    return price.toLocaleString("en-US", {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    });
  }
  if (price >= 1) {
    return price.toFixed(4);
  }
  return price.toFixed(6);
}

