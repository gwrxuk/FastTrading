"use client";

import { useEffect, useState, useCallback } from "react";
import { useQuery } from "@tanstack/react-query";
import { market } from "@/lib/api";
import { tradingWs } from "@/lib/websocket";

interface MarketData {
  symbol: string;
  bid: number;
  ask: number;
  last: number;
  volume_24h: number;
  high_24h: number;
  low_24h: number;
  change_24h: number;
  change_percent_24h: number;
  timestamp: string;
}

interface OrderBookLevel {
  price: number;
  quantity: number;
  order_count: number;
}

interface OrderBook {
  symbol: string;
  bids: OrderBookLevel[];
  asks: OrderBookLevel[];
  timestamp: string;
  sequence: number;
}

export function useMarketPrice(symbol: string) {
  const [price, setPrice] = useState<MarketData | null>(null);

  // Initial fetch
  const { data, isLoading, error } = useQuery({
    queryKey: ["market-price", symbol],
    queryFn: async () => {
      const response = await market.price(symbol);
      return response.data as MarketData;
    },
    refetchInterval: 5000,
  });

  // WebSocket updates
  useEffect(() => {
    const channel = `prices:${symbol}`;
    
    const handleUpdate = (data: string) => {
      const [last, bid, ask, timestamp] = data.split("|");
      setPrice((prev) => ({
        ...(prev || {}),
        symbol,
        last: parseFloat(last),
        bid: parseFloat(bid),
        ask: parseFloat(ask),
        timestamp,
      } as MarketData));
    };

    tradingWs.connect();
    tradingWs.subscribe(channel);
    tradingWs.on(channel, handleUpdate);

    return () => {
      tradingWs.unsubscribe(channel);
      tradingWs.off(channel, handleUpdate);
    };
  }, [symbol]);

  return {
    price: price || data,
    isLoading,
    error,
  };
}

export function useAllMarketPrices() {
  return useQuery({
    queryKey: ["market-prices"],
    queryFn: async () => {
      const response = await market.prices();
      return response.data as MarketData[];
    },
    refetchInterval: 5000,
  });
}

export function useOrderBook(symbol: string, levels = 20) {
  const [orderBook, setOrderBook] = useState<OrderBook | null>(null);

  const { data, isLoading, error } = useQuery({
    queryKey: ["orderbook", symbol],
    queryFn: async () => {
      const response = await market.price(symbol);
      return response.data as OrderBook;
    },
    refetchInterval: 1000,
  });

  // WebSocket updates for order book
  useEffect(() => {
    const channel = `orderbook:${symbol}`;
    
    const handleUpdate = (data: any) => {
      setOrderBook(data);
    };

    tradingWs.connect();
    tradingWs.subscribe(channel);
    tradingWs.on(channel, handleUpdate);

    return () => {
      tradingWs.unsubscribe(channel);
      tradingWs.off(channel, handleUpdate);
    };
  }, [symbol]);

  return {
    orderBook: orderBook || data,
    isLoading,
    error,
  };
}

export function useCandles(symbol: string, interval = "1m", limit = 100) {
  return useQuery({
    queryKey: ["candles", symbol, interval, limit],
    queryFn: async () => {
      const response = await market.candles(symbol, interval, limit);
      return response.data;
    },
    refetchInterval: interval === "1m" ? 5000 : 30000,
  });
}

export function useTickers() {
  return useQuery({
    queryKey: ["tickers"],
    queryFn: async () => {
      const response = await market.tickers();
      return response.data;
    },
    refetchInterval: 5000,
  });
}

export function useSymbols() {
  return useQuery({
    queryKey: ["symbols"],
    queryFn: async () => {
      const response = await market.symbols();
      return response.data;
    },
    staleTime: 60000, // Symbols rarely change
  });
}

