---
sidebar_position: 1
title: Getting Started
description: Quick start guide for the Saathii Backend API
---

# Getting Started with Saathii Backend API

Welcome to the Saathii Backend API documentation! This guide will help you get up and running with our FastAPI-based backend service.

## 🚀 What is Saathii Backend API?

The Saathii Backend API is a scalable FastAPI backend designed for the Saathii application, providing:

- **OTP-based Authentication** with phone number verification
- **JWT Token Management** with refresh token rotation
- **User Profile Management** with comprehensive user data
- **Real-time Presence Tracking** with WebSocket support
- **Feed System** for discovering listeners with real-time updates
- **Listener Verification System** with audio sample uploads
- **S3 File Upload** for verification audio files
- **Call Management** with coin-based billing system
- **Wallet & Earnings** system for listeners
- **Favorites & Blocking** functionality
- **Scalable Architecture** with Redis pub/sub for multiple instances

## 📋 Quick Start

### Prerequisites

- Python 3.8+
- PostgreSQL 12+
- Redis 6+
- Node.js 16+ (for documentation)

### 1. Clone the Repository

```bash
git clone https://github.com/saathii/saathii-backend-api.git
cd saathii-backend-api
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Set Environment Variables

Create a `.env` file in the root directory:

```bash
# Database
DATABASE_URL="postgresql://user:password@localhost/saathii"

# Redis
REDIS_URL="redis://localhost:6379"

# JWT Configuration
JWT_SECRET_KEY="your-secret-key-here"
JWT_ALGORITHM="HS256"
JWT_ACCESS_TOKEN_EXPIRE_MINUTES="30"
JWT_REFRESH_TOKEN_EXPIRE_DAYS="7"

# AWS S3 (Optional - for file uploads)
AWS_ACCESS_KEY_ID="your-aws-access-key-id"
AWS_SECRET_ACCESS_KEY="your-aws-secret-access-key"
AWS_REGION="us-east-1"
S3_BUCKET_NAME="your-s3-bucket-name"
```

### 4. Run the Server

```bash
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

### 5. Access the API

Once the server is running, you can access:

- **Swagger API Documentation**: https://saathiiapp.com/docs
- **ReDoc API Documentation**: https://saathiiapp.com/redoc
- **API Base URL**: https://saathiiapp.com
- **WebSocket**: wss://saathiiapp.com

## 🔧 Configuration

### Database Setup

1. Create a PostgreSQL database named `saathii`
2. The application will automatically create tables on first run
3. For production, run migrations manually

### Redis Setup

1. Install and start Redis server
2. Default configuration uses `redis://localhost:6379`
3. For production, configure Redis with authentication

### S3 Setup (Optional)

If you need file upload functionality:

1. Create an AWS S3 bucket
2. Configure IAM user with S3 permissions
3. Set the environment variables above
4. See [S3 Setup Guide](./guides/s3-setup) for detailed instructions

## 📱 API Endpoints Overview

### 🔐 Authentication
- `POST /auth/request_otp` - Request OTP for phone number
- `POST /auth/resend_otp` - Resend OTP
- `POST /auth/verify` - Verify OTP and get tokens
- `POST /auth/register` - Complete user registration
- `POST /auth/refresh` - Refresh access token
- `POST /auth/logout` - Logout and invalidate tokens

### 👤 User Management
- `GET /users/me` - Get current user profile
- `PUT /users/me` - Update user profile
- `DELETE /users/me` - Delete user account

### 📡 Presence & Status
- `GET /users/me/status` - Get user presence status
- `PUT /users/me/status` - Update user presence status
- `POST /users/me/heartbeat` - Send heartbeat
- `GET /users/{user_id}/presence` - Get user presence
- `GET /users/presence` - Get multiple users presence
- `GET /both/users/me` - Get current user profile

### 📰 Feeds
- `GET /feed/listeners` - Get listeners feed with filters
- `GET /feed/stats` - Get feed statistics

### 💰 Wallets
- `GET /balance` - Get user wallet balance
- `POST /add_coin` - Add coins to wallet
- `GET /listener/balance` - Get listener withdrawable money
- `GET /listener/earnings` - Get listener earnings history
- `POST /listener/withdraw` - Request withdrawal
- `GET /listener/withdrawals` - Get withdrawal history
- `PUT /listener/bank-details` - Update bank details
- `GET /listener/bank-details` - Get bank details status

### 📞 Calls
- `POST /calls/start` - Start a new call
- `POST /calls/end` - End an ongoing call
- `GET /calls/ongoing` - Get ongoing call details
- `GET /calls/history` - Get call history

### ⭐ Favorites
- `POST /favorites/add` - Add favorite listener
- `DELETE /favorites/remove` - Remove favorite listener
- `GET /favorites` - Get favorites list
- `GET /favorites/check/{listener_id}` - Check favorite status

### 🚫 Blocking
- `POST /block` - Block user
- `DELETE /block` - Unblock user
- `GET /blocked` - Get blocked users list
- `GET /block/check/{user_id}` - Check block status

### ✅ Verification & Preferences
- `GET /listener/verification/status` - Get listener verification status
- `GET /listener/preferences` - Get listener call preferences
- `PUT /listener/preferences` - Update listener call preferences

### 🔌 WebSocket
- `wss://saathiiapp.com/ws/feed` - Real-time feed updates
- `wss://saathiiapp.com/ws/presence` - Real-time presence updates

## 🚀 Next Steps

1. **Explore the API**: Check out the [Swagger UI](https://saathiiapp.com/docs) to interact with the API
2. **Read the Guides**: Follow our [integration guides](./guides/installation) for specific use cases
3. **View Examples**: See [API examples](./guides/react-native-authentication) for common operations
4. **React Native Integration**: Learn how to integrate with [React Native apps](./guides/react-native-authentication)

## 📚 Documentation Structure

- **[API Reference](./api/authentication)**: Complete API endpoint documentation
- **[Guides](./guides/installation)**: Step-by-step integration guides
- **[Examples](./guides/react-native-authentication)**: Code examples and use cases
- **[Deployment](./guides/installation)**: Production deployment guides

## 🆘 Need Help?

- **GitHub Issues**: [Report bugs or request features](https://github.com/saathiiapp/saathii_backend_fastapi/issues)
- **Documentation**: Browse the comprehensive guides and API reference

---

Ready to dive deeper? Check out the [Authentication API](./api/authentication) to get started with user management!
