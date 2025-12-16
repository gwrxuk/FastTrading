"use client";

import { useState } from "react";
import { useAccount } from "wagmi";
import clsx from "clsx";

type TabType = "open" | "history" | "trades";

interface Order {
  id: string;
  symbol: string;
  side: "buy" | "sell";
  type: "limit" | "market";
  price: number;
  amount: number;
  filled: number;
  status: "open" | "partial" | "filled" | "cancelled";
  time: Date;
}

const MOCK_ORDERS: Order[] = [
  {
    id: "1",
    symbol: "ETH-USDT",
    side: "buy",
    type: "limit",
    price: 2200.0,
    amount: 2.5,
    filled: 0,
    status: "open",
    time: new Date(Date.now() - 3600000),
  },
  {
    id: "2",
    symbol: "ETH-USDT",
    side: "sell",
    type: "limit",
    price: 2350.0,
    amount: 1.0,
    filled: 0.5,
    status: "partial",
    time: new Date(Date.now() - 7200000),
  },
  {
    id: "3",
    symbol: "BTC-USDT",
    side: "buy",
    type: "market",
    price: 42500.0,
    amount: 0.1,
    filled: 0.1,
    status: "filled",
    time: new Date(Date.now() - 86400000),
  },
];

export function UserOrders() {
  const { isConnected } = useAccount();
  const [activeTab, setActiveTab] = useState<TabType>("open");

  const openOrders = MOCK_ORDERS.filter(
    (o) => o.status === "open" || o.status === "partial"
  );
  const orderHistory = MOCK_ORDERS.filter(
    (o) => o.status === "filled" || o.status === "cancelled"
  );

  if (!isConnected) {
    return (
      <div className="py-8 text-center">
        <p className="text-terminal-muted">
          Connect your wallet to view orders
        </p>
      </div>
    );
  }

  return (
    <div>
      {/* Tabs */}
      <div className="flex items-center gap-6 border-b border-terminal-border mb-4">
        {(["open", "history", "trades"] as const).map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={clsx(
              "pb-3 text-sm font-medium capitalize transition-colors relative",
              activeTab === tab ? "text-white" : "text-terminal-muted hover:text-white"
            )}
          >
            {tab === "open" ? `Open Orders (${openOrders.length})` : tab}
            {activeTab === tab && (
              <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-accent-primary" />
            )}
          </button>
        ))}
      </div>

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-terminal-muted text-xs">
              <th className="text-left pb-3 font-medium">Time</th>
              <th className="text-left pb-3 font-medium">Symbol</th>
              <th className="text-left pb-3 font-medium">Type</th>
              <th className="text-left pb-3 font-medium">Side</th>
              <th className="text-right pb-3 font-medium">Price</th>
              <th className="text-right pb-3 font-medium">Amount</th>
              <th className="text-right pb-3 font-medium">Filled</th>
              <th className="text-right pb-3 font-medium">Status</th>
              <th className="text-right pb-3 font-medium">Action</th>
            </tr>
          </thead>
          <tbody>
            {(activeTab === "open" ? openOrders : orderHistory).map((order) => (
              <tr
                key={order.id}
                className="border-t border-terminal-border/50 hover:bg-terminal-elevated/30"
              >
                <td className="py-3 font-mono text-terminal-muted">
                  {formatDateTime(order.time)}
                </td>
                <td className="py-3 font-medium">{order.symbol}</td>
                <td className="py-3 capitalize">{order.type}</td>
                <td className="py-3">
                  <span
                    className={clsx(
                      "capitalize font-medium",
                      order.side === "buy" ? "text-bull" : "text-bear"
                    )}
                  >
                    {order.side}
                  </span>
                </td>
                <td className="py-3 text-right font-mono">
                  ${order.price.toLocaleString()}
                </td>
                <td className="py-3 text-right font-mono">{order.amount}</td>
                <td className="py-3 text-right font-mono">
                  {order.filled} ({((order.filled / order.amount) * 100).toFixed(0)}%)
                </td>
                <td className="py-3 text-right">
                  <StatusBadge status={order.status} />
                </td>
                <td className="py-3 text-right">
                  {(order.status === "open" || order.status === "partial") && (
                    <button className="text-bear hover:text-bear-light text-xs font-medium">
                      Cancel
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>

        {(activeTab === "open" ? openOrders : orderHistory).length === 0 && (
          <div className="py-8 text-center text-terminal-muted">
            No {activeTab === "open" ? "open orders" : "order history"}
          </div>
        )}
      </div>
    </div>
  );
}

function StatusBadge({ status }: { status: Order["status"] }) {
  const styles: Record<Order["status"], string> = {
    open: "bg-accent-primary/20 text-accent-primary",
    partial: "bg-accent-tertiary/20 text-accent-tertiary",
    filled: "bg-bull/20 text-bull",
    cancelled: "bg-terminal-muted/20 text-terminal-muted",
  };

  return (
    <span
      className={clsx(
        "px-2 py-0.5 rounded text-xs font-medium capitalize",
        styles[status]
      )}
    >
      {status}
    </span>
  );
}

function formatDateTime(date: Date): string {
  return date.toLocaleString("en-US", {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  });
}

