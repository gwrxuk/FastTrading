"use client";

import { useState } from "react";
import { useAccount } from "wagmi";
import clsx from "clsx";
import { motion, AnimatePresence } from "framer-motion";

interface OrderFormProps {
  symbol: string;
}

type OrderSide = "buy" | "sell";
type OrderType = "limit" | "market";

export function OrderForm({ symbol }: OrderFormProps) {
  const { isConnected } = useAccount();
  const [side, setSide] = useState<OrderSide>("buy");
  const [orderType, setOrderType] = useState<OrderType>("limit");
  const [price, setPrice] = useState<string>("2256.78");
  const [amount, setAmount] = useState<string>("");
  const [total, setTotal] = useState<string>("");
  const [sliderValue, setSliderValue] = useState<number>(0);

  const handleAmountChange = (value: string) => {
    setAmount(value);
    if (price && value) {
      setTotal((parseFloat(price) * parseFloat(value)).toFixed(2));
    }
  };

  const handleTotalChange = (value: string) => {
    setTotal(value);
    if (price && value) {
      setAmount((parseFloat(value) / parseFloat(price)).toFixed(6));
    }
  };

  const handleSliderChange = (value: number) => {
    setSliderValue(value);
    // Calculate amount based on available balance
    const maxAmount = 10; // Mock available balance
    handleAmountChange((maxAmount * (value / 100)).toFixed(6));
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!isConnected) {
      alert("Please connect your wallet first");
      return;
    }
    console.log({ side, orderType, price, amount, total });
  };

  const [base, quote] = symbol.split("-");

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      {/* Buy/Sell Toggle */}
      <div className="grid grid-cols-2 gap-2 p-1 bg-terminal-elevated rounded-lg">
        <button
          type="button"
          onClick={() => setSide("buy")}
          className={clsx(
            "py-2 rounded-md font-semibold transition-all",
            side === "buy"
              ? "bg-bull text-terminal-bg"
              : "text-terminal-muted hover:text-white"
          )}
        >
          Buy
        </button>
        <button
          type="button"
          onClick={() => setSide("sell")}
          className={clsx(
            "py-2 rounded-md font-semibold transition-all",
            side === "sell"
              ? "bg-bear text-white"
              : "text-terminal-muted hover:text-white"
          )}
        >
          Sell
        </button>
      </div>

      {/* Order Type Tabs */}
      <div className="flex gap-4 border-b border-terminal-border pb-2">
        {(["limit", "market"] as const).map((type) => (
          <button
            key={type}
            type="button"
            onClick={() => setOrderType(type)}
            className={clsx(
              "text-sm font-medium capitalize transition-colors",
              orderType === type
                ? "text-accent-primary"
                : "text-terminal-muted hover:text-white"
            )}
          >
            {type}
          </button>
        ))}
      </div>

      {/* Price Input (for limit orders) */}
      <AnimatePresence mode="wait">
        {orderType === "limit" && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            className="space-y-1"
          >
            <label className="text-xs text-terminal-muted">Price</label>
            <div className="relative">
              <input
                type="number"
                value={price}
                onChange={(e) => setPrice(e.target.value)}
                className="input-field w-full pr-16 font-mono"
                placeholder="0.00"
                step="0.01"
              />
              <span className="absolute right-3 top-1/2 -translate-y-1/2 text-terminal-muted text-sm">
                {quote}
              </span>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Amount Input */}
      <div className="space-y-1">
        <label className="text-xs text-terminal-muted">Amount</label>
        <div className="relative">
          <input
            type="number"
            value={amount}
            onChange={(e) => handleAmountChange(e.target.value)}
            className="input-field w-full pr-16 font-mono"
            placeholder="0.00"
            step="0.0001"
          />
          <span className="absolute right-3 top-1/2 -translate-y-1/2 text-terminal-muted text-sm">
            {base}
          </span>
        </div>
      </div>

      {/* Percentage Slider */}
      <div className="space-y-2">
        <input
          type="range"
          min="0"
          max="100"
          value={sliderValue}
          onChange={(e) => handleSliderChange(parseInt(e.target.value))}
          className="w-full h-1 bg-terminal-elevated rounded-lg appearance-none cursor-pointer
                   [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:w-4 
                   [&::-webkit-slider-thumb]:h-4 [&::-webkit-slider-thumb]:rounded-full 
                   [&::-webkit-slider-thumb]:bg-accent-primary"
        />
        <div className="flex justify-between text-xs text-terminal-muted">
          {[0, 25, 50, 75, 100].map((pct) => (
            <button
              key={pct}
              type="button"
              onClick={() => handleSliderChange(pct)}
              className="hover:text-accent-primary transition-colors"
            >
              {pct}%
            </button>
          ))}
        </div>
      </div>

      {/* Total Input */}
      <div className="space-y-1">
        <label className="text-xs text-terminal-muted">Total</label>
        <div className="relative">
          <input
            type="number"
            value={total}
            onChange={(e) => handleTotalChange(e.target.value)}
            className="input-field w-full pr-16 font-mono"
            placeholder="0.00"
            step="0.01"
          />
          <span className="absolute right-3 top-1/2 -translate-y-1/2 text-terminal-muted text-sm">
            {quote}
          </span>
        </div>
      </div>

      {/* Available Balance */}
      <div className="flex justify-between text-xs">
        <span className="text-terminal-muted">Available</span>
        <span className="font-mono">
          {side === "buy" ? "10,000.00 USDT" : "4.5678 ETH"}
        </span>
      </div>

      {/* Submit Button */}
      <button
        type="submit"
        className={clsx(
          "w-full py-3 rounded-lg font-semibold transition-all active:scale-[0.98]",
          side === "buy"
            ? "bg-bull text-terminal-bg hover:brightness-110"
            : "bg-bear text-white hover:brightness-110",
          !isConnected && "opacity-50 cursor-not-allowed"
        )}
        disabled={!isConnected}
      >
        {isConnected
          ? `${side === "buy" ? "Buy" : "Sell"} ${base}`
          : "Connect Wallet to Trade"}
      </button>
    </form>
  );
}

