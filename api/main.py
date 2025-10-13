from fastapi import FastAPI
from api.routes import auth, user, websocket, call, wallet, verification, feed, favorites, block, badge, status
from api.clients.websocket_manager import manager
# Scheduler removed - using external cron jobs instead
import asyncio

app = FastAPI(
    title="Saathii Backend API",
    description="A scalable FastAPI backend for the Saathii application with authentication, user management, call management, presence features, and real-time WebSocket updates",
    version="1.0.0",
    tags_metadata=[
        {
            "name": "Authentication",
            "description": "Authentication and authorization endpoints including OTP verification, registration, and token management",
        },
        {
            "name": "User Management", 
            "description": "User profile management, presence tracking, favorites, blocking, verification, badge system, and administrative functions",
        },
        {
            "name": "Wallet Management",
            "description": "Wallet operations including balance management, coin transactions, earnings tracking, withdrawals, and bank details management",
        },
        {
            "name": "Call Management",
            "description": "Call management system with coin-based billing, call lifecycle, transactions, and real-time status updates",
        },
        {
            "name": "WebSocket",
            "description": "Real-time WebSocket connections for live updates and presence tracking",
        },
    ]
)

app.include_router(auth.router)
app.include_router(user.router)
app.include_router(block.router)
app.include_router(badge.router)
app.include_router(status.router)
app.include_router(favorites.router)
app.include_router(wallet.router)
app.include_router(websocket.router)
app.include_router(call.router)
app.include_router(verification.router)
app.include_router(feed.router)


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    # Start Redis subscriber for cross-instance communication
    await manager.start_redis_subscriber()
    
    # Background tasks handled by external cron jobs
    
    print("🚀 Saathii Backend API started with real-time WebSocket support!")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    # Background tasks handled by external cron jobs
    
    # Stop Redis subscriber
    if manager.redis_subscriber:
        await manager.redis_subscriber.unsubscribe("status_updates")
        await manager.redis_subscriber.close()
    
    print("👋 Saathii Backend API shutdown complete!")
