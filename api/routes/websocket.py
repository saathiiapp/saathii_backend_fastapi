from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException, Header
from app.clients.websocket_manager import manager
from app.clients.jwt_handler import decode_jwt
from app.clients.redis_client import redis_client
import json
import logging

logger = logging.getLogger(__name__)

router = APIRouter(tags=["WebSocket"])


async def get_current_user_from_websocket(websocket: WebSocket, token: str):
    """Extract and validate user from WebSocket token"""
    try:
        payload = decode_jwt(token)
        if not payload:
            await websocket.close(code=1008, reason="Invalid token")
            return None
        
        if payload.get("type") != "access":
            await websocket.close(code=1008, reason="Access token required")
            return None
        
        # Check if token is blacklisted
        user_id = payload.get("user_id")
        jti = payload.get("jti")
        if user_id and jti and await redis_client.get(f"access:{user_id}:{jti}"):
            await websocket.close(code=1008, reason="Token has been revoked")
            return None
        
        return payload
    except Exception as e:
        logger.error(f"WebSocket authentication error: {e}")
        await websocket.close(code=1008, reason="Authentication failed")
        return None


@router.websocket("/ws/feed")
async def websocket_feed_endpoint(websocket: WebSocket, token: str = None):
    """
    WebSocket endpoint for real-time feed updates
    
    Query Parameters:
    - token: JWT access token for authentication
    """
    if not token:
        await websocket.close(code=1008, reason="Token required")
        return
    
    # Authenticate user
    user = await get_current_user_from_websocket(websocket, token)
    if not user:
        return
    
    user_id = user["user_id"]
    
    try:
        # Connect the user
        await manager.connect(websocket, user_id)
        
        # Send initial connection confirmation
        await websocket.send_text(json.dumps({
            "type": "connection_established",
            "message": "Connected to feed updates",
            "user_id": user_id
        }))
        
        # Keep the connection alive and handle incoming messages
        while True:
            try:
                # Wait for any message from client (ping/pong, etc.)
                data = await websocket.receive_text()
                message = json.loads(data)
                
                # Handle different message types
                if message.get("type") == "ping":
                    await websocket.send_text(json.dumps({
                        "type": "pong",
                        "timestamp": message.get("timestamp")
                    }))
                elif message.get("type") == "subscribe":
                    # Client can subscribe to specific updates
                    await websocket.send_text(json.dumps({
                        "type": "subscription_confirmed",
                        "subscription": message.get("subscription", "feed")
                    }))
                
            except WebSocketDisconnect:
                break
            except json.JSONDecodeError:
                # Ignore invalid JSON messages
                continue
            except Exception as e:
                logger.error(f"WebSocket error for user {user_id}: {e}")
                break
                
    except WebSocketDisconnect:
        logger.info(f"User {user_id} disconnected from feed WebSocket")
    except Exception as e:
        logger.error(f"WebSocket connection error for user {user_id}: {e}")
    finally:
        # Clean up connection
        manager.disconnect(websocket, user_id)


@router.websocket("/ws/presence")
async def websocket_presence_endpoint(websocket: WebSocket, token: str = None):
    """
    WebSocket endpoint for real-time presence updates
    
    Query Parameters:
    - token: JWT access token for authentication
    """
    if not token:
        await websocket.close(code=1008, reason="Token required")
        return
    
    # Authenticate user
    user = await get_current_user_from_websocket(websocket, token)
    if not user:
        return
    
    user_id = user["user_id"]
    
    try:
        # Connect the user
        await manager.connect(websocket, user_id)
        
        # Send initial connection confirmation
        await websocket.send_text(json.dumps({
            "type": "presence_connection_established",
            "message": "Connected to presence updates",
            "user_id": user_id
        }))
        
        # Keep the connection alive
        while True:
            try:
                data = await websocket.receive_text()
                message = json.loads(data)
                
                if message.get("type") == "ping":
                    await websocket.send_text(json.dumps({
                        "type": "pong",
                        "timestamp": message.get("timestamp")
                    }))
                
            except WebSocketDisconnect:
                break
            except json.JSONDecodeError:
                continue
            except Exception as e:
                logger.error(f"Presence WebSocket error for user {user_id}: {e}")
                break
                
    except WebSocketDisconnect:
        logger.info(f"User {user_id} disconnected from presence WebSocket")
    except Exception as e:
        logger.error(f"Presence WebSocket connection error for user {user_id}: {e}")
    finally:
        # Clean up connection
        manager.disconnect(websocket, user_id)
