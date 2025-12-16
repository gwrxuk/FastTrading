"use client";

import { useEffect, useState } from "react";
import clsx from "clsx";

interface RecentTradesProps {
  symbol: string;
}

interface Trade {
  id: number;
  price: number;
  quantity: number;
  side: "buy" | "sell";
  time: Date;
}

export function RecentTrades({ symbol }: RecentTradesProps) {
  const [trades, setTrades] = useState<Trade[]>([]);

  useEffect(() => {
    // Initialize with mock trades
    const initialTrades: Trade[] = Array.from({ length: 20 }, (_, i) => ({
      id: Date.now() - i * 1000,
      price: 2256.78 + (Math.random() - 0.5) * 20,
      quantity: Math.random() * 5,
      side: Math.random() > 0.5 ? "buy" : "sell",
      time: new Date(Date.now() - i * 1000),
    }));
    setTrades(initialTrades);

    // Simulate real-time trades
    const interval = setInterval(() => {
      const newTrade: Trade = {
        id: Date.now(),
        price: 2256.78 + (Math.random() - 0.5) * 20,
        quantity: Math.random() * 2,
        side: Math.random() > 0.5 ? "buy" : "sell",
        time: new Date(),
      };

      setTrades((prev) => [newTrade, ...prev.slice(0, 19)]);
    }, 1500);

    return () => clearInterval(interval);
  }, []);

  return (
    <div className="h-full flex flex-col">
      <h3 className="font-semibold mb-3">Recent Trades</h3>

      {/* Column Headers */}
      <div className="grid grid-cols-3 gap-2 text-xs text-terminal-muted mb-2 px-1">
        <span>Price (USDT)</span>
        <span className="text-right">Size (ETH)</span>
        <span className="text-right">Time</span>
      </div>

      {/* Trades List */}
      <div className="flex-1 overflow-y-auto space-y-0.5">
        {trades.map((trade, index) => (
          <div
            key={trade.id}
            className={clsx(
              "grid grid-cols-3 gap-2 py-0.5 px-1 text-xs font-mono",
              index === 0 && (trade.side === "buy" ? "animate-flash-green" : "animate-flash-red")
            )}
          >
            <span className={trade.side === "buy" ? "text-bull" : "text-bear"}>
              {trade.price.toFixed(2)}
            </span>
            <span className="text-right">{trade.quantity.toFixed(4)}</span>
            <span className="text-right text-terminal-muted">
              {formatTime(trade.time)}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}

function formatTime(date: Date): string {
  return date.toLocaleTimeString("en-US", {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    hour12: false,
  });
}

