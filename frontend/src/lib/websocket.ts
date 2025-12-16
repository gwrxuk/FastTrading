type MessageHandler = (data: any) => void;

interface WebSocketMessage {
  type: string;
  channel?: string;
  data?: any;
  timestamp?: string;
}

class TradingWebSocket {
  private ws: WebSocket | null = null;
  private url: string;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000;
  private handlers: Map<string, Set<MessageHandler>> = new Map();
  private subscriptions: Set<string> = new Set();
  private token: string | null = null;

  constructor() {
    this.url = process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8000/ws";
  }

  connect(token?: string): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      return;
    }

    this.token = token || null;
    const wsUrl = token ? `${this.url}?token=${token}` : this.url;

    try {
      this.ws = new WebSocket(wsUrl);
      this.setupEventHandlers();
    } catch (error) {
      console.error("WebSocket connection failed:", error);
      this.attemptReconnect();
    }
  }

  private setupEventHandlers(): void {
    if (!this.ws) return;

    this.ws.onopen = () => {
      console.log("WebSocket connected");
      this.reconnectAttempts = 0;
      
      // Resubscribe to previous channels
      this.subscriptions.forEach((channel) => {
        this.send({ action: "subscribe", channel });
      });
      
      this.emit("connected", { connected: true });
    };

    this.ws.onclose = (event) => {
      console.log("WebSocket disconnected:", event.code, event.reason);
      this.emit("disconnected", { code: event.code, reason: event.reason });
      
      if (!event.wasClean) {
        this.attemptReconnect();
      }
    };

    this.ws.onerror = (error) => {
      console.error("WebSocket error:", error);
      this.emit("error", { error });
    };

    this.ws.onmessage = (event) => {
      try {
        const message: WebSocketMessage = JSON.parse(event.data);
        this.handleMessage(message);
      } catch (error) {
        console.error("Failed to parse WebSocket message:", error);
      }
    };
  }

  private handleMessage(message: WebSocketMessage): void {
    const { type, channel, data } = message;

    // Handle different message types
    switch (type) {
      case "connected":
        this.emit("connected", message);
        break;
      
      case "subscribed":
        console.log(`Subscribed to ${channel}`);
        break;
      
      case "unsubscribed":
        console.log(`Unsubscribed from ${channel}`);
        break;
      
      case "heartbeat":
        // Respond to heartbeat
        this.send({ action: "ping", timestamp: message.timestamp });
        break;
      
      case "pong":
        // Heartbeat response received
        break;
      
      case "data":
        // Emit data to channel handlers
        if (channel) {
          this.emit(channel, data);
        }
        break;
      
      case "error":
        console.error("WebSocket server error:", message);
        this.emit("error", message);
        break;
      
      default:
        console.log("Unknown message type:", type);
    }
  }

  private attemptReconnect(): void {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error("Max reconnection attempts reached");
      this.emit("max_reconnect", {});
      return;
    }

    this.reconnectAttempts++;
    const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);
    
    console.log(`Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts})`);
    
    setTimeout(() => {
      this.connect(this.token || undefined);
    }, delay);
  }

  subscribe(channel: string): void {
    this.subscriptions.add(channel);
    
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.send({ action: "subscribe", channel });
    }
  }

  unsubscribe(channel: string): void {
    this.subscriptions.delete(channel);
    
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.send({ action: "unsubscribe", channel });
    }
  }

  on(event: string, handler: MessageHandler): void {
    if (!this.handlers.has(event)) {
      this.handlers.set(event, new Set());
    }
    this.handlers.get(event)!.add(handler);
  }

  off(event: string, handler: MessageHandler): void {
    this.handlers.get(event)?.delete(handler);
  }

  private emit(event: string, data: any): void {
    this.handlers.get(event)?.forEach((handler) => {
      try {
        handler(data);
      } catch (error) {
        console.error("Error in WebSocket handler:", error);
      }
    });
  }

  private send(data: object): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data));
    }
  }

  disconnect(): void {
    this.subscriptions.clear();
    this.handlers.clear();
    
    if (this.ws) {
      this.ws.close(1000, "Client disconnect");
      this.ws = null;
    }
  }

  get isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN;
  }
}

// Singleton instance
export const tradingWs = new TradingWebSocket();

// React hook for WebSocket
export function useWebSocket() {
  return tradingWs;
}

