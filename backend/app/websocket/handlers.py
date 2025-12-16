"""
WebSocket Endpoint Handlers
Real-time data streaming for trading interface
"""
import uuid
from typing import Optional

from fastapi import WebSocket, WebSocketDisconnect, Query

from app.websocket.manager import ws_manager
from app.services.auth import AuthService


auth_service = AuthService()


async def websocket_endpoint(
    websocket: WebSocket,
    token: Optional[str] = Query(None)
):
    """
    WebSocket endpoint for real-time data streams
    
    Channels:
    - prices:{symbol} - Real-time price updates
    - trades:{symbol} - Trade executions
    - orderbook:{symbol} - Order book updates
    - orders - User's order updates (requires auth)
    
    Messages:
    - {"action": "subscribe", "channel": "prices:ETH-USDT"}
    - {"action": "unsubscribe", "channel": "prices:ETH-USDT"}
    - {"action": "ping"} -> {"type": "pong"}
    """
    connection_id = str(uuid.uuid4())
    user_id = None
    
    # Authenticate if token provided
    if token:
        payload = auth_service.decode_token(token)
        if payload:
            user_id = payload.get("sub")
    
    # Accept connection
    if not await ws_manager.connect(websocket, connection_id):
        return
    
    try:
        while True:
            # Receive message
            data = await websocket.receive_json()
            action = data.get("action")
            
            if action == "subscribe":
                channel = data.get("channel", "")
                
                # Validate channel
                if channel.startswith("orders") and not user_id:
                    await ws_manager.send_personal(connection_id, {
                        "type": "error",
                        "message": "Authentication required for orders channel"
                    })
                    continue
                
                # Subscribe to user-specific orders channel
                if channel == "orders" and user_id:
                    channel = f"orders:{user_id}"
                
                await ws_manager.subscribe(connection_id, channel)
            
            elif action == "unsubscribe":
                channel = data.get("channel", "")
                if channel == "orders" and user_id:
                    channel = f"orders:{user_id}"
                await ws_manager.unsubscribe(connection_id, channel)
            
            elif action == "ping":
                await ws_manager.send_personal(connection_id, {
                    "type": "pong",
                    "timestamp": data.get("timestamp")
                })
            
            else:
                await ws_manager.send_personal(connection_id, {
                    "type": "error",
                    "message": f"Unknown action: {action}"
                })
    
    except WebSocketDisconnect:
        pass
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        await ws_manager.disconnect(connection_id)

