from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
from api.routes import auth, user, call, wallet, feed, favorites, block, badge, status

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
    ]
)

# Security middleware
app.add_middleware(
    TrustedHostMiddleware, 
    allowed_hosts=["saathiiapp.com", "*.saathiiapp.com", "localhost", "127.0.0.1"]
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://saathiiapp.com",
        "https://docs.saathiiapp.com", 
        "https://logs.saathiiapp.com",
        "http://localhost:3000",  # For development
        "http://localhost:8080",  # For development
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(user.router)
app.include_router(block.router)
app.include_router(badge.router)
app.include_router(status.router)
app.include_router(favorites.router)
app.include_router(wallet.router)
app.include_router(call.router)
app.include_router(feed.router)