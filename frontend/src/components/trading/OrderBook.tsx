"use client";

import { useEffect, useState, useMemo } from "react";
import clsx from "clsx";

interface OrderBookProps {
  symbol: string;
}

interface OrderLevel {
  price: number;
  quantity: number;
  total: number;
}

export function OrderBook({ symbol }: OrderBookProps) {
  const [asks, setAsks] = useState<OrderLevel[]>([]);
  const [bids, setBids] = useState<OrderLevel[]>([]);
  const [lastPrice, setLastPrice] = useState<number>(2256.78);
  const [priceDirection, setPriceDirection] = useState<"up" | "down">("up");

  // Generate and update mock order book
  useEffect(() => {
    const generateOrderLevels = (
      basePrice: number,
      isAsk: boolean,
      count: number
    ): OrderLevel[] => {
      const levels: OrderLevel[] = [];
      let runningTotal = 0;

      for (let i = 0; i < count; i++) {
        const priceOffset = (i + 1) * (Math.random() * 0.5 + 0.1);
        const price = isAsk
          ? basePrice + priceOffset
          : basePrice - priceOffset;
        const quantity = Math.random() * 50 + 1;
        runningTotal += quantity;

        levels.push({
          price,
          quantity,
          total: runningTotal,
        });
      }

      return levels;
    };

    const updateOrderBook = () => {
      const newPrice = lastPrice + (Math.random() - 0.5) * 2;
      setPriceDirection(newPrice >= lastPrice ? "up" : "down");
      setLastPrice(newPrice);

      setAsks(generateOrderLevels(newPrice, true, 15));
      setBids(generateOrderLevels(newPrice, false, 15));
    };

    updateOrderBook();
    const interval = setInterval(updateOrderBook, 500);

    return () => clearInterval(interval);
  }, []);

  const maxTotal = useMemo(() => {
    const maxAsk = asks.length > 0 ? asks[asks.length - 1].total : 0;
    const maxBid = bids.length > 0 ? bids[bids.length - 1].total : 0;
    return Math.max(maxAsk, maxBid);
  }, [asks, bids]);

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <h3 className="font-semibold">Order Book</h3>
        <div className="flex items-center gap-2">
          <button className="text-terminal-muted hover:text-white transition-colors">
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 10h16M4 14h16M4 18h16" />
            </svg>
          </button>
        </div>
      </div>

      {/* Column Headers */}
      <div className="grid grid-cols-3 gap-2 text-xs text-terminal-muted mb-2 px-1">
        <span>Price (USDT)</span>
        <span className="text-right">Size (ETH)</span>
        <span className="text-right">Total</span>
      </div>

      {/* Asks (Sell Orders) - Reversed so lowest ask is at bottom */}
      <div className="flex-1 overflow-hidden flex flex-col">
        <div className="flex-1 overflow-y-auto flex flex-col-reverse">
          {asks.slice().reverse().map((level, index) => (
            <OrderRow
              key={`ask-${index}`}
              level={level}
              type="ask"
              maxTotal={maxTotal}
            />
          ))}
        </div>

        {/* Spread / Last Price */}
        <div className="py-2 px-1 border-y border-terminal-border my-1">
          <div className="flex items-center justify-between">
            <span
              className={clsx(
                "font-mono font-bold text-lg",
                priceDirection === "up" ? "text-bull" : "text-bear"
              )}
            >
              ${lastPrice.toFixed(2)}
            </span>
            <span className="text-xs text-terminal-muted">
              ≈ ${lastPrice.toFixed(2)}
            </span>
          </div>
        </div>

        {/* Bids (Buy Orders) */}
        <div className="flex-1 overflow-y-auto">
          {bids.map((level, index) => (
            <OrderRow
              key={`bid-${index}`}
              level={level}
              type="bid"
              maxTotal={maxTotal}
            />
          ))}
        </div>
      </div>
    </div>
  );
}

function OrderRow({
  level,
  type,
  maxTotal,
}: {
  level: OrderLevel;
  type: "ask" | "bid";
  maxTotal: number;
}) {
  const depthPercentage = (level.total / maxTotal) * 100;

  return (
    <div
      className={clsx(
        "orderbook-row grid grid-cols-3 gap-2 py-0.5 px-1 text-xs font-mono cursor-pointer hover:bg-terminal-elevated/50",
        type
      )}
      style={{
        ["--depth-width" as string]: `${depthPercentage}%`,
      }}
    >
      <span className={type === "ask" ? "text-bear" : "text-bull"}>
        {level.price.toFixed(2)}
      </span>
      <span className="text-right">{level.quantity.toFixed(4)}</span>
      <span className="text-right text-terminal-muted">
        {level.total.toFixed(4)}
      </span>
      
      {/* Depth visualization */}
      <div
        className={clsx(
          "absolute top-0 bottom-0 opacity-20",
          type === "ask" ? "right-0 bg-bear" : "left-0 bg-bull"
        )}
        style={{
          width: `${depthPercentage}%`,
        }}
      />
    </div>
  );
}

