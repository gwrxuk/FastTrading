import axios, { AxiosInstance, AxiosError } from "axios";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// Create axios instance with default config
const api: AxiosInstance = axios.create({
  baseURL: `${API_URL}/api/v1`,
  headers: {
    "Content-Type": "application/json",
  },
  timeout: 10000,
});

// Request interceptor to add auth token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem("access_token");
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    if (error.response?.status === 401) {
      localStorage.removeItem("access_token");
      window.location.href = "/login";
    }
    return Promise.reject(error);
  }
);

// Auth endpoints
export const auth = {
  register: (email: string, password: string) =>
    api.post("/auth/register", { email, password }),
  
  login: async (email: string, password: string) => {
    const response = await api.post("/auth/login", { email, password });
    localStorage.setItem("access_token", response.data.access_token);
    return response.data;
  },
  
  logout: () => {
    localStorage.removeItem("access_token");
  },
  
  me: () => api.get("/auth/me"),
  
  bindWallet: (address: string, signature: string, message: string) =>
    api.post("/auth/bind-wallet", { address, signature, message }),
};

// Order endpoints
export const orders = {
  create: (order: {
    symbol: string;
    side: "buy" | "sell";
    order_type: "market" | "limit";
    quantity: string;
    price?: string;
    time_in_force?: string;
  }) => api.post("/orders", order),
  
  list: (params?: { symbol?: string; status?: string; limit?: number }) =>
    api.get("/orders", { params }),
  
  get: (orderId: string) => api.get(`/orders/${orderId}`),
  
  cancel: (orderId: string) => api.delete(`/orders/${orderId}`),
  
  cancelAll: (symbol?: string) =>
    api.post("/orders/cancel-all", null, { params: { symbol } }),
  
  getOrderBook: (symbol: string, levels = 20) =>
    api.get(`/orders/book/${symbol}`, { params: { levels } }),
};

// Trade endpoints
export const trades = {
  list: (params?: {
    symbol?: string;
    start_time?: string;
    end_time?: string;
    limit?: number;
  }) => api.get("/trades", { params }),
  
  stats: (params?: { symbol?: string; period?: string }) =>
    api.get("/trades/stats", { params }),
  
  recent: (symbol: string, limit = 50) =>
    api.get(`/trades/recent/${symbol}`, { params: { limit } }),
};

// Wallet endpoints
export const wallets = {
  requestSignMessage: (address: string) =>
    api.post("/wallets/sign-message", { address }),
  
  bind: (data: {
    address: string;
    chain: string;
    currency: string;
    signature: string;
    message: string;
  }) => api.post("/wallets/bind", data),
  
  list: () => api.get("/wallets"),
  
  balances: () => api.get("/wallets/balances"),
  
  estimateGas: (toAddress: string, amount: number, currency = "ETH") =>
    api.get("/wallets/estimate-gas", {
      params: { to_address: toAddress, amount, currency },
    }),
  
  withdraw: (walletId: string, data: {
    to_address: string;
    currency: string;
    amount: string;
  }) => api.post("/wallets/withdraw", data, { params: { wallet_id: walletId } }),
  
  transactions: (limit = 50) =>
    api.get("/wallets/transactions", { params: { limit } }),
};

// Market data endpoints
export const market = {
  price: (symbol: string) => api.get(`/market/price/${symbol}`),
  
  prices: () => api.get("/market/prices"),
  
  ticker: (symbol: string) => api.get(`/market/ticker/${symbol}`),
  
  tickers: () => api.get("/market/tickers"),
  
  candles: (symbol: string, interval = "1m", limit = 100) =>
    api.get(`/market/candles/${symbol}`, { params: { interval, limit } }),
  
  symbols: () => api.get("/market/symbols"),
};

// AI Analytics endpoints
export const analytics = {
  // Anomaly detection
  getAnomalies: (params?: { symbol?: string; lookback_hours?: number; user_only?: boolean }) =>
    api.get("/analytics/anomalies", { params }),
  
  // Risk scoring
  getUserRiskScore: () => api.get("/analytics/risk/user"),
  
  getSpecificUserRiskScore: (userId: string) =>
    api.get(`/analytics/risk/user/${userId}`),
  
  // Price predictions
  getPricePrediction: (symbol: string, horizonMinutes = 60) =>
    api.get(`/analytics/predictions/${symbol}`, { params: { horizon_minutes: horizonMinutes } }),
  
  // Portfolio analysis
  getPortfolioAnalysis: () => api.get("/analytics/portfolio"),
  
  // Market sentiment
  getMarketSentiment: (symbol: string) =>
    api.get(`/analytics/sentiment/${symbol}`),
  
  // Summary dashboard
  getSummary: (symbols: string[] = ["ETH-USDT", "BTC-USDT"]) =>
    api.get("/analytics/summary", { params: { symbols } }),
  
  // AI insights
  getInsights: () => api.get("/analytics/insights"),
  
  // Trading metrics
  getTradingMetrics: () => api.get("/analytics/metrics"),
};

export default api;

