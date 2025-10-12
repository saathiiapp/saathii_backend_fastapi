import json
import asyncio
from typing import Dict, List, Set
from fastapi import WebSocket, WebSocketDisconnect
from api.clients.redis_client import redis_client
import logging

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections for real-time updates"""
    
    def __init__(self):
        # Store active connections by user_id
        self.active_connections: Dict[int, Set[WebSocket]] = {}
        # Store all connections for broadcasting
        self.all_connections: Set[WebSocket] = set()
        # Redis pub/sub for scaling across instances
        self.redis_pubsub = None
        self.redis_subscriber = None
    
    async def connect(self, websocket: WebSocket, user_id: int):
        """Accept a new WebSocket connection"""
        await websocket.accept()
        
        # Add to user-specific connections
        if user_id not in self.active_connections:
            self.active_connections[user_id] = set()
        self.active_connections[user_id].add(websocket)
        
        # Add to all connections
        self.all_connections.add(websocket)
        
        logger.info(f"User {user_id} connected. Total connections: {len(self.all_connections)}")
    
    def disconnect(self, websocket: WebSocket, user_id: int):
        """Remove a WebSocket connection"""
        # Remove from user-specific connections
        if user_id in self.active_connections:
            self.active_connections[user_id].discard(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
        
        # Remove from all connections
        self.all_connections.discard(websocket)
        
        logger.info(f"User {user_id} disconnected. Total connections: {len(self.all_connections)}")
    
    async def send_personal_message(self, message: dict, user_id: int):
        """Send message to a specific user"""
        if user_id in self.active_connections:
            dead_connections = set()
            for connection in self.active_connections[user_id]:
                try:
                    await connection.send_text(json.dumps(message))
                except:
                    dead_connections.add(connection)
            
            # Clean up dead connections
            for connection in dead_connections:
                self.disconnect(connection, user_id)
    
    async def broadcast_to_feed(self, message: dict):
        """Broadcast message to all feed page connections"""
        dead_connections = set()
        for connection in self.all_connections:
            try:
                await connection.send_text(json.dumps(message))
            except:
                dead_connections.add(connection)
        
        # Clean up dead connections
        for connection in dead_connections:
            # Find user_id for this connection (inefficient but necessary for cleanup)
            for user_id, connections in self.active_connections.items():
                if connection in connections:
                    self.disconnect(connection, user_id)
                    break
    
    async def start_redis_subscriber(self):
        """Start Redis subscriber for cross-instance communication"""
        try:
            self.redis_subscriber = redis_client.pubsub()
            await self.redis_subscriber.subscribe("status_updates")
            
            # Start listening in background
            asyncio.create_task(self._listen_redis_messages())
            logger.info("Redis subscriber started for status updates")
        except Exception as e:
            logger.error(f"Failed to start Redis subscriber: {e}")
    
    async def _listen_redis_messages(self):
        """Listen for Redis messages and broadcast to local connections"""
        try:
            async for message in self.redis_subscriber.listen():
                if message["type"] == "message":
                    try:
                        data = json.loads(message["data"])
                        await self.broadcast_to_feed(data)
                    except json.JSONDecodeError:
                        logger.error(f"Invalid JSON in Redis message: {message['data']}")
        except Exception as e:
            logger.error(f"Error in Redis subscriber: {e}")
    
    async def publish_status_update(self, user_id: int, status_data: dict):
        """Publish status update to Redis for other instances"""
        try:
            message = {
                "type": "status_update",
                "user_id": user_id,
                "data": status_data,
                "timestamp": status_data.get("timestamp")
            }
            await redis_client.publish("status_updates", json.dumps(message))
        except Exception as e:
            logger.error(f"Failed to publish status update: {e}")


# Global connection manager instance
manager = ConnectionManager()


async def get_connection_manager():
    """Dependency to get the connection manager"""
    return manager
