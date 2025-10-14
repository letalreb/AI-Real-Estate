"""
WebSocket handler for real-time notifications.
Manages WebSocket connections and broadcasts notifications to connected clients.
"""
from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, Set
import structlog
import json
from jose import jwt, JWTError

from ..config import settings
from ..models import User

logger = structlog.get_logger()

# Active WebSocket connections: user_id -> set of WebSocket connections
active_connections: Dict[int, Set[WebSocket]] = {}


async def verify_token(token: str) -> int:
    """
    Verify JWT token and return user_id.
    
    Args:
        token: JWT token string
    
    Returns:
        user_id: User ID from token
    
    Raises:
        ValueError: If token is invalid
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        email: str = payload.get("sub")
        if email is None:
            raise ValueError("Invalid token payload")
        
        # In production, you'd fetch user_id from database
        # For simplicity, we'll extract from token or use a mock value
        # This should be properly implemented with database lookup
        user_id = payload.get("user_id", 1)  # Mock implementation
        return user_id
    
    except JWTError as e:
        logger.error("token_verification_failed", error=str(e))
        raise ValueError("Invalid token")


async def handle_websocket_connection(websocket: WebSocket, token: str = None):
    """
    Handle WebSocket connection lifecycle.
    
    Args:
        websocket: WebSocket connection
        token: JWT authentication token
    """
    # Verify authentication
    if not token:
        await websocket.close(code=1008, reason="Missing authentication token")
        return
    
    try:
        user_id = await verify_token(token)
    except ValueError as e:
        await websocket.close(code=1008, reason=str(e))
        return
    
    # Accept connection
    await websocket.accept()
    
    # Register connection
    if user_id not in active_connections:
        active_connections[user_id] = set()
    active_connections[user_id].add(websocket)
    
    logger.info(
        "websocket_connected",
        user_id=user_id,
        total_connections=len(active_connections.get(user_id, set()))
    )
    
    try:
        # Keep connection alive and handle messages
        while True:
            # Wait for messages from client (ping/pong, etc.)
            data = await websocket.receive_text()
            
            # Echo back or handle client messages
            message = json.loads(data)
            if message.get("type") == "ping":
                await websocket.send_json({"type": "pong"})
            
    except WebSocketDisconnect:
        # Remove connection
        if user_id in active_connections:
            active_connections[user_id].discard(websocket)
            if not active_connections[user_id]:
                del active_connections[user_id]
        
        logger.info("websocket_disconnected", user_id=user_id)
    
    except Exception as e:
        logger.error("websocket_error", user_id=user_id, error=str(e))
        
        # Clean up connection
        if user_id in active_connections:
            active_connections[user_id].discard(websocket)
            if not active_connections[user_id]:
                del active_connections[user_id]


async def broadcast_to_user(user_id: int, message: dict):
    """
    Broadcast a message to all connections for a specific user.
    
    Args:
        user_id: User ID to send message to
        message: Message dictionary to send
    """
    if user_id not in active_connections:
        logger.debug("no_active_connections", user_id=user_id)
        return
    
    # Send to all user's connections
    disconnected = set()
    for websocket in active_connections[user_id]:
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(
                "broadcast_failed",
                user_id=user_id,
                error=str(e)
            )
            disconnected.add(websocket)
    
    # Clean up disconnected websockets
    for websocket in disconnected:
        active_connections[user_id].discard(websocket)
    
    if not active_connections[user_id]:
        del active_connections[user_id]
    
    logger.info(
        "message_broadcasted",
        user_id=user_id,
        connections=len(active_connections.get(user_id, set()))
    )


async def broadcast_to_all(message: dict):
    """
    Broadcast a message to all connected users.
    
    Args:
        message: Message dictionary to send
    """
    for user_id in list(active_connections.keys()):
        await broadcast_to_user(user_id, message)
    
    logger.info("message_broadcasted_to_all", total_users=len(active_connections))


def get_active_connections_count() -> int:
    """Get total number of active WebSocket connections."""
    return sum(len(connections) for connections in active_connections.values())


def get_active_users_count() -> int:
    """Get number of users with active connections."""
    return len(active_connections)
