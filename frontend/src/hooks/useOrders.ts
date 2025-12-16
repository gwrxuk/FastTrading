"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { orders } from "@/lib/api";
import { useEffect } from "react";
import { tradingWs } from "@/lib/websocket";

interface Order {
  id: string;
  client_order_id: string;
  symbol: string;
  side: "buy" | "sell";
  order_type: "market" | "limit" | "stop_limit";
  status: "pending" | "open" | "partial" | "filled" | "cancelled";
  price: string | null;
  quantity: string;
  filled_quantity: string;
  remaining_quantity: string;
  average_fill_price: string | null;
  commission: string;
  created_at: string;
  updated_at: string;
}

interface CreateOrderParams {
  symbol: string;
  side: "buy" | "sell";
  order_type: "market" | "limit";
  quantity: string;
  price?: string;
  time_in_force?: "gtc" | "ioc" | "fok";
}

export function useOrders(params?: { symbol?: string; status?: string; limit?: number }) {
  const queryClient = useQueryClient();

  const query = useQuery({
    queryKey: ["orders", params],
    queryFn: async () => {
      const response = await orders.list(params);
      return response.data as Order[];
    },
    refetchInterval: 5000,
  });

  // WebSocket updates for order status
  useEffect(() => {
    const token = localStorage.getItem("access_token");
    if (!token) return;

    const handleOrderUpdate = (data: any) => {
      queryClient.invalidateQueries({ queryKey: ["orders"] });
    };

    tradingWs.connect(token);
    tradingWs.subscribe("orders");
    tradingWs.on("orders", handleOrderUpdate);

    return () => {
      tradingWs.unsubscribe("orders");
      tradingWs.off("orders", handleOrderUpdate);
    };
  }, [queryClient]);

  return query;
}

export function useOrder(orderId: string) {
  return useQuery({
    queryKey: ["order", orderId],
    queryFn: async () => {
      const response = await orders.get(orderId);
      return response.data as Order;
    },
    enabled: !!orderId,
  });
}

export function useCreateOrder() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (params: CreateOrderParams) => {
      const response = await orders.create(params);
      return response.data as Order;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["orders"] });
    },
  });
}

export function useCancelOrder() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (orderId: string) => {
      await orders.cancel(orderId);
      return orderId;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["orders"] });
    },
  });
}

export function useCancelAllOrders() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (symbol?: string) => {
      const response = await orders.cancelAll(symbol);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["orders"] });
    },
  });
}

export function useOpenOrders(symbol?: string) {
  return useOrders({ symbol, status: "open" });
}

export function useOrderHistory(params?: { symbol?: string; limit?: number }) {
  return useOrders({ ...params, status: "filled" });
}

