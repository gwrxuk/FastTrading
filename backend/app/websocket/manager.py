"""
WebSocket Connection Manager
High-performance real-time data distribution
"""
import asyncio
from typing import Dict, Set, Optional
from datetime import datetime
import json

from fastapi import WebSocket
import redis.asyncio as redis

from app.config import settings


class WebSocketManager:
    """
    WebSocket connection manager for real-time data streams
    
    Features:
    - Channel-based subscriptions (prices, trades, orders)
    - Redis pub/sub for distributed messaging
    - Automatic heartbeat and reconnection
    - Connection limiting
    """
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.subscriptions: Dict[str, Set[str]] = {}  # channel -> connection_ids
        self._redis: Optional[redis.Redis] = None
        self._pubsub: Optional[redis.client.PubSub] = None
        self._running = False
    
    async def start(self, redis_client: redis.Redis) -> None:
        """Start the WebSocket manager with Redis pub/sub"""
        self._redis = redis_client
        self._pubsub = redis_client.pubsub()
        self._running = True
        
        # Start background tasks
        asyncio.create_task(self._heartbeat_loop())
        asyncio.create_task(self._redis_subscriber())
    
    async def stop(self) -> None:
        """Stop the manager and close all connections"""
        self._running = False
        
        if self._pubsub:
            await self._pubsub.unsubscribe()
            await self._pubsub.close()
        
        for ws in self.active_connections.values():
            await ws.close()
        
        self.active_connections.clear()
        self.subscriptions.clear()
    
    async def connect(self, websocket: WebSocket, connection_id: str) -> bool:
        """
        Accept a new WebSocket connection
        Returns False if connection limit reached
        """
        if len(self.active_connections) >= settings.WS_MAX_CONNECTIONS:
            await websocket.close(code=1013, reason="Server overloaded")
            return False
        
        await websocket.accept()
        self.active_connections[connection_id] = websocket
        
        # Send welcome message
        await self.send_personal(connection_id, {
            "type": "connected",
            "connection_id": connection_id,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        return True
    
    async def disconnect(self, connection_id: str) -> None:
        """Handle connection disconnect"""
        if connection_id in self.active_connections:
            del self.active_connections[connection_id]
        
        # Remove from all subscriptions
        for channel in list(self.subscriptions.keys()):
            self.subscriptions[channel].discard(connection_id)
            if not self.subscriptions[channel]:
                del self.subscriptions[channel]
                if self._pubsub:
                    await self._pubsub.unsubscribe(channel)
    
    async def subscribe(self, connection_id: str, channel: str) -> None:
        """Subscribe a connection to a channel"""
        if channel not in self.subscriptions:
            self.subscriptions[channel] = set()
            # Subscribe to Redis channel
            if self._pubsub:
                await self._pubsub.subscribe(channel)
        
        self.subscriptions[channel].add(connection_id)
        
        await self.send_personal(connection_id, {
            "type": "subscribed",
            "channel": channel
        })
    
    async def unsubscribe(self, connection_id: str, channel: str) -> None:
        """Unsubscribe a connection from a channel"""
        if channel in self.subscriptions:
            self.subscriptions[channel].discard(connection_id)
            
            if not self.subscriptions[channel]:
                del self.subscriptions[channel]
                if self._pubsub:
                    await self._pubsub.unsubscribe(channel)
        
        await self.send_personal(connection_id, {
            "type": "unsubscribed",
            "channel": channel
        })
    
    async def send_personal(self, connection_id: str, message: dict) -> None:
        """Send message to a specific connection"""
        if connection_id in self.active_connections:
            try:
                await self.active_connections[connection_id].send_json(message)
            except Exception:
                await self.disconnect(connection_id)
    
    async def broadcast_to_channel(self, channel: str, message: dict) -> None:
        """Broadcast message to all subscribers of a channel"""
        if channel not in self.subscriptions:
            return
        
        disconnected = []
        
        for connection_id in self.subscriptions[channel]:
            if connection_id in self.active_connections:
                try:
                    await self.active_connections[connection_id].send_json(message)
                except Exception:
                    disconnected.append(connection_id)
        
        # Clean up disconnected clients
        for conn_id in disconnected:
            await self.disconnect(conn_id)
    
    async def _heartbeat_loop(self) -> None:
        """Send periodic heartbeats to keep connections alive"""
        while self._running:
            try:
                message = {
                    "type": "heartbeat",
                    "timestamp": datetime.utcnow().isoformat()
                }
                
                disconnected = []
                
                for conn_id, ws in list(self.active_connections.items()):
                    try:
                        await ws.send_json(message)
                    except Exception:
                        disconnected.append(conn_id)
                
                for conn_id in disconnected:
                    await self.disconnect(conn_id)
                
                await asyncio.sleep(settings.WS_HEARTBEAT_INTERVAL)
            except Exception as e:
                print(f"Heartbeat error: {e}")
                await asyncio.sleep(5)
    
    async def _redis_subscriber(self) -> None:
        """Listen for Redis pub/sub messages and broadcast to WebSocket clients"""
        while self._running:
            try:
                if self._pubsub:
                    message = await self._pubsub.get_message(
                        ignore_subscribe_messages=True,
                        timeout=1.0
                    )
                    
                    if message and message["type"] == "message":
                        channel = message["channel"]
                        if isinstance(channel, bytes):
                            channel = channel.decode()
                        
                        data = message["data"]
                        if isinstance(data, bytes):
                            data = data.decode()
                        
                        # Parse and broadcast
                        await self.broadcast_to_channel(channel, {
                            "type": "data",
                            "channel": channel,
                            "data": data,
                            "timestamp": datetime.utcnow().isoformat()
                        })
                else:
                    await asyncio.sleep(1)
            except Exception as e:
                print(f"Redis subscriber error: {e}")
                await asyncio.sleep(1)


# Singleton instance
ws_manager = WebSocketManager()

