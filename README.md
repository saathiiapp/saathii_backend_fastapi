# Saathii Backend FastAPI

A scalable FastAPI backend for the Saathii application with authentication, user management, presence features, and real-time WebSocket updates.

## 🚀 Features

- **OTP-based Authentication** with phone number verification
- **JWT Token Management** with refresh token rotation
- **User Profile Management** with comprehensive user data
- **Real-time Presence Tracking** with WebSocket support
- **Feed System** for discovering listeners with real-time updates
- **Scalable Architecture** with Redis pub/sub for multiple instances
- **Comprehensive API Documentation** with Swagger UI

## 📋 Table of Contents

- [Base URL](#base-url)
- [Authentication](#authentication)
- [User Management](#user-management)
- [Presence & Status](#presence--status)
- [Feed System](#feed-system)
- [WebSocket Real-time Updates](#websocket-real-time-updates)
- [React Native Integration](#react-native-integration)
- [API Examples](#api-examples)
- [Swagger Documentation](#swagger-documentation)

## Base URL

- **Local Development**: `http://localhost:8000`
- **WebSocket**: `ws://localhost:8000`
- **API Documentation**: `http://localhost:8000/docs`

## Authentication

### Overview
- OTP-based login with optional registration step
- Token model:
  - **Access token**: short-lived (~30m), used in `Authorization: Bearer <access>`
  - **Refresh token**: long-lived (~30d), rotated on refresh, stored server-side in Redis by `jti`
  - **Registration token**: short-lived (~10m), used only to finalize registration

### Authentication Endpoints

#### 1. Request OTP
- **Endpoint**: `POST /auth/request_otp`
- **Tags**: Authentication, OTP
- **Body**:
```json
{ "phone": "+919876543210" }
```
- **Responses**:
  - `200` - `{ "message": "OTP sent" }`
  - `429` - Too many requests (rate limit: 5 per 15 minutes)

#### 2. Resend OTP
- **Endpoint**: `POST /auth/resend_otp`
- **Tags**: Authentication, OTP
- **Body**:
```json
{ "phone": "+919876543210" }
```
- **Behavior**:
  - Throttle: 1 resend per 60 seconds per phone
  - If an OTP is active, re-sends the same code without changing its TTL
  - If no OTP is active, generates and sends a new code (5 minute TTL)
- **Responses**:
  - `200` - `{ "message": "OTP re-sent" }` or `{ "message": "OTP sent" }`
  - `429` - On throttle

#### 3. Verify OTP
- **Endpoint**: `POST /auth/verify`
- **Tags**: Authentication, OTP
- **Body**:
```json
{ "phone": "+919876543210", "otp": "123456" }
```
- **Responses**:
  - `200` - Registered user:
```json
{ "status": "registered", "access_token": "...", "refresh_token": "..." }
```
  - `200` - Needs registration:
```json
{ "status": "needs_registration", "registration_token": "..." }
```
  - `400` - Invalid/expired OTP

#### 4. Register User
- **Endpoint**: `POST /auth/register`
- **Tags**: Authentication, Registration
- **Body**:
```json
{
  "registration_token": "...",
  "username": "alice",
  "sex": "female",
  "dob": "2000-01-01",
  "bio": "Professional listener...",
  "interests": ["music", "tech"],
  "profile_image_url": "https://...",
  "preferred_language": "en",
  "role": "listener"
}
```
- **Response**: `200` - `{ "access_token": "...", "refresh_token": "..." }`

#### 5. Refresh Tokens
- **Endpoint**: `POST /auth/refresh`
- **Tags**: Authentication, Token Management
- **Body**:
```json
{ "refresh_token": "..." }
```
- **Response**: `200` - `{ "access_token": "...", "refresh_token": "..." }`
- **Notes**: Refresh tokens are single-use. If reused, server returns 401.

#### 6. Logout
- **Endpoint**: `POST /auth/logout`
- **Tags**: Authentication, Token Management
- **Headers**: `Authorization: Bearer <access_token>`
- **Behavior**: Blacklists current access token and revokes all refresh tokens for the user
- **Response**: `200` - `{ "message": "Logged out" }`

## User Management

### Profile Endpoints

#### 1. Get Current User
- **Endpoint**: `GET /users/me`
- **Tags**: User Management, Profile
- **Headers**: `Authorization: Bearer <access_token>`
- **Response**: `200` - User profile with active roles
```json
{
  "user_id": 123,
  "phone": "+919876543210",
  "username": "alice",
  "sex": "female",
  "dob": "2000-01-01",
  "bio": "Professional listener...",
  "interests": ["music", "tech"],
  "profile_image_url": "https://...",
  "preferred_language": "en",
  "rating": 4.8,
  "country": "US",
  "roles": ["listener"]
}
```

#### 2. Update Current User
- **Endpoint**: `PUT /users/me`
- **Tags**: User Management, Profile
- **Headers**: `Authorization: Bearer <access_token>`
- **Body** (any subset):
```json
{
  "username": "newname",
  "bio": "Updated bio...",
  "rating": 4.8,
  "interests": ["music", "tech", "art"],
  "profile_image_url": "https://...",
  "preferred_language": "en"
}
```
- **Response**: `200` - Updated user profile

#### 3. Delete Current User
- **Endpoint**: `DELETE /users/me`
- **Tags**: User Management, Profile
- **Headers**: `Authorization: Bearer <access_token>`
- **Response**: `200` - `{ "message": "User deleted" }`

## Presence & Status

### Status Endpoints

#### 1. Get My Status
- **Endpoint**: `GET /users/me/status`
- **Tags**: User Management, Presence
- **Headers**: `Authorization: Bearer <access_token>`
- **Response**: `200` - Current user's status
```json
{
  "user_id": 123,
  "is_online": true,
  "last_seen": "2024-01-15T10:30:00Z",
  "is_busy": false,
  "busy_until": null
}
```

#### 2. Update My Status
- **Endpoint**: `PUT /users/me/status`
- **Tags**: User Management, Presence
- **Headers**: `Authorization: Bearer <access_token>`
- **Body**:
```json
{
  "is_online": true,
  "is_busy": false,
  "busy_until": "2024-01-15T11:00:00Z"
}
```
- **Response**: `200` - Updated status
- **Note**: Triggers real-time broadcast to all connected clients

#### 3. Heartbeat
- **Endpoint**: `POST /users/me/heartbeat`
- **Tags**: User Management, Presence
- **Headers**: `Authorization: Bearer <access_token>`
- **Response**: `200` - `{ "message": "Heartbeat received" }`
- **Note**: Updates last_seen and triggers real-time broadcast

#### 4. Get User Presence
- **Endpoint**: `GET /users/{user_id}/presence`
- **Tags**: User Management, Presence
- **Headers**: `Authorization: Bearer <access_token>`
- **Response**: `200` - User's presence status

#### 5. Get Multiple Users Presence
- **Endpoint**: `GET /users/presence`
- **Tags**: User Management, Presence
- **Headers**: `Authorization: Bearer <access_token>`
- **Query Parameters**:
  - `user_ids`: Comma-separated user IDs
- **Response**: `200` - Array of user presence data

## Feed System

### Feed Endpoints

#### 1. Get Listeners Feed
- **Endpoint**: `GET /feed/listeners`
- **Tags**: User Management, Feed
- **Headers**: `Authorization: Bearer <access_token>`
- **Query Parameters**:
  - `online_only` (bool): Show only online users
  - `available_only` (bool): Show only available users (online + not busy)
  - `language` (str): Filter by preferred language
  - `interests` (str): Comma-separated interests filter
  - `min_rating` (int): Minimum rating filter
  - `page` (int): Page number (default: 1)
  - `per_page` (int): Items per page (default: 20, max: 100)

- **Response**: `200` - Feed data with pagination
```json
{
  "listeners": [
    {
      "user_id": 123,
      "username": "john_doe",
      "sex": "male",
      "bio": "Professional listener...",
      "interests": ["music", "tech"],
      "profile_image_url": "https://...",
      "preferred_language": "en",
      "rating": 4.5,
      "country": "US",
      "roles": ["listener"],
      "is_online": true,
      "last_seen": "2024-01-15T10:30:00Z",
      "is_busy": false,
      "busy_until": null,
      "is_available": true
    }
  ],
  "total_count": 150,
  "online_count": 45,
  "available_count": 38,
  "page": 1,
  "per_page": 20,
  "has_next": true,
  "has_previous": false
}
```

#### 2. Get Feed Statistics
- **Endpoint**: `GET /feed/stats`
- **Tags**: User Management, Feed
- **Headers**: `Authorization: Bearer <access_token>`
- **Response**: `200` - Feed statistics
```json
{
  "total_listeners": 150,
  "online_listeners": 45,
  "available_listeners": 38,
  "busy_listeners": 7
}
```

## WebSocket Real-time Updates

### WebSocket Endpoints

#### 1. Feed Updates WebSocket
- **Endpoint**: `ws://localhost:8000/ws/feed?token=<access_token>`
- **Purpose**: Receive real-time updates for the feed page
- **Authentication**: JWT access token as query parameter

#### 2. Presence Updates WebSocket
- **Endpoint**: `ws://localhost:8000/ws/presence?token=<access_token>`
- **Purpose**: Receive real-time presence updates
- **Authentication**: JWT access token as query parameter

### WebSocket Message Types

#### Incoming Messages

**Connection Established**
```json
{
  "type": "connection_established",
  "message": "Connected to feed updates",
  "user_id": 123
}
```

**User Status Update**
```json
{
  "type": "user_status_update",
  "user_id": 456,
  "status": {
    "user_id": 456,
    "username": "john_doe",
    "profile_image_url": "https://...",
    "is_online": true,
    "last_seen": "2024-01-15T10:30:00Z",
    "is_busy": false,
    "busy_until": null,
    "is_available": true
  }
}
```

**Pong Response**
```json
{
  "type": "pong",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

#### Outgoing Messages

**Ping**
```json
{
  "type": "ping",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

**Subscribe**
```json
{
  "type": "subscribe",
  "subscription": "feed"
}
```

### Real-time Flow

1. **Listener goes on call** → Status updated via React Native heartbeat
2. **Backend broadcasts update** → All connected WebSocket clients receive real-time notification
3. **Feed page updates instantly** → No app refresh needed!

## React Native Integration

### Dependencies

```bash
npm install @react-native-async-storage/async-storage
# For Expo
expo install @react-native-async-storage/async-storage
```

### Axios Setup with Token Management

```typescript
import axios from 'axios';
import * as SecureStore from 'expo-secure-store';

export const api = axios.create({ baseURL: 'http://localhost:8000' });

let accessToken: string | null = null;

export function setTokens(access: string, refresh: string) {
  accessToken = access;
  SecureStore.setItemAsync('refresh_token', refresh);
}

api.interceptors.request.use(async (config) => {
  if (accessToken) {
    config.headers = config.headers || {};
    config.headers.Authorization = `Bearer ${accessToken}`;
  }
  return config;
});

let isRefreshing = false;
let pending: Array<(t: string|null) => void> = [];

api.interceptors.response.use(
  (res) => res,
  async (error) => {
    if (error.response?.status === 401) {
      const refresh = await SecureStore.getItemAsync('refresh_token');
      if (!refresh) throw error;

      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          pending.push((t) => {
            if (t) {
              error.config.headers.Authorization = `Bearer ${t}`;
              resolve(api.request(error.config));
            } else {
              reject(error);
            }
          });
        });
      }

      isRefreshing = true;
      try {
        const { data } = await api.post('/auth/refresh', { refresh_token: refresh });
        setTokens(data.access_token, data.refresh_token);
        pending.forEach((cb) => cb(data.access_token));
        pending = [];
        error.config.headers.Authorization = `Bearer ${data.access_token}`;
        return api.request(error.config);
      } catch (e) {
        pending.forEach((cb) => cb(null));
        pending = [];
        accessToken = null;
        await SecureStore.deleteItemAsync('refresh_token');
        // TODO: navigate to login
        throw e;
      } finally {
        isRefreshing = false;
      }
    }
    throw error;
  }
);
```

### WebSocket Hook

```typescript
// hooks/useWebSocket.ts
import { useEffect, useRef, useState } from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';

interface WebSocketMessage {
  type: string;
  user_id?: number;
  status?: any;
  message?: string;
  timestamp?: string;
}

export const useWebSocket = ({
  url,
  onMessage,
  onConnect,
  onDisconnect,
  reconnectInterval = 5000
}: {
  url: string;
  onMessage?: (message: WebSocketMessage) => void;
  onConnect?: () => void;
  onDisconnect?: () => void;
  reconnectInterval?: number;
}) => {
  const [isConnected, setIsConnected] = useState(false);
  const [connectionError, setConnectionError] = useState<string | null>(null);
  const wsRef = useRef<WebSocket | null>(null);

  const connect = async () => {
    try {
      const token = await AsyncStorage.getItem('access_token');
      if (!token) {
        setConnectionError('No access token found');
        return;
      }

      const wsUrl = `${url}?token=${token}`;
      const ws = new WebSocket(wsUrl);
      
      ws.onopen = () => {
        setIsConnected(true);
        setConnectionError(null);
        onConnect?.();
      };

      ws.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data);
          onMessage?.(message);
        } catch (error) {
          console.error('Error parsing WebSocket message:', error);
        }
      };

      ws.onclose = (event) => {
        setIsConnected(false);
        onDisconnect?.();
        
        if (event.code !== 1000) {
          setTimeout(() => connect(), reconnectInterval);
        }
      };

      ws.onerror = (error) => {
        setConnectionError('WebSocket connection error');
      };

      wsRef.current = ws;
    } catch (error) {
      setConnectionError('Failed to connect to WebSocket');
    }
  };

  const disconnect = () => {
    if (wsRef.current) {
      wsRef.current.close(1000, 'User disconnected');
      wsRef.current = null;
    }
    setIsConnected(false);
  };

  const sendMessage = (message: any) => {
    if (wsRef.current && isConnected) {
      wsRef.current.send(JSON.stringify(message));
    }
  };

  useEffect(() => {
    connect();
    return () => disconnect();
  }, []);

  return { isConnected, connectionError, connect, disconnect, sendMessage };
};
```

### Heartbeat Integration

```typescript
// utils/heartbeat.ts
import AsyncStorage from '@react-native-async-storage/async-storage';

export const startHeartbeat = async () => {
  const sendHeartbeat = async () => {
    try {
      const token = await AsyncStorage.getItem('access_token');
      if (!token) return;

      await fetch('http://localhost:8000/users/me/heartbeat', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });
    } catch (error) {
      console.error('Heartbeat error:', error);
    }
  };

  // Send heartbeat every 30 seconds
  const interval = setInterval(sendHeartbeat, 30000);
  sendHeartbeat(); // Send initial heartbeat
  
  return () => clearInterval(interval);
};
```

### Authentication Flow

1. **Request OTP** → `POST /auth/request_otp`
2. **Verify OTP** → `POST /auth/verify`
   - If `status=needs_registration`, navigate to Registration
   - Else call `setTokens(access_token, refresh_token)` and go to app
3. **Registration** → `POST /auth/register` then `setTokens(...)`
4. **On app start**: if a refresh token exists, call `POST /auth/refresh` to bootstrap session
5. **On 401 at any time**: interceptor refreshes and retries; if refresh fails, navigate to login
6. **Logout** → `POST /auth/logout`, then clear tokens

## API Examples

### cURL Examples

**Request OTP**
```bash
curl -X POST 'http://localhost:8000/auth/request_otp' \
  -H 'Content-Type: application/json' \
  -d '{"phone":"+919876543210"}'
```

**Verify OTP**
```bash
curl -X POST 'http://localhost:8000/auth/verify' \
  -H 'Content-Type: application/json' \
  -d '{"phone":"+919876543210","otp":"123456"}'
```

**Register User**
```bash
curl -X POST 'http://localhost:8000/auth/register' \
  -H 'Content-Type: application/json' \
  -d '{"registration_token":"...","username":"alice","sex":"female"}'
```

**Get Feed**
```bash
curl -X GET 'http://localhost:8000/feed/listeners?online_only=true' \
  -H 'Authorization: Bearer <ACCESS_TOKEN>'
```

**Update Status**
```bash
curl -X PUT 'http://localhost:8000/users/me/status' \
  -H 'Authorization: Bearer <ACCESS_TOKEN>' \
  -H 'Content-Type: application/json' \
  -d '{"is_busy":true,"busy_until":"2024-01-15T11:00:00Z"}'
```

**Send Heartbeat**
```bash
curl -X POST 'http://localhost:8000/users/me/heartbeat' \
  -H 'Authorization: Bearer <ACCESS_TOKEN>'
```

## Swagger Documentation

The API includes comprehensive Swagger documentation available at:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

### API Groups in Swagger

1. **Authentication** - OTP verification, registration, and token management
2. **User Management** - Profile management, presence tracking, and feed system
3. **WebSocket** - Real-time WebSocket connections for live updates

## 🚀 Getting Started

1. **Install Dependencies**
```bash
pip install -r requirements.txt
```

2. **Set Environment Variables**
```bash
export REDIS_URL="redis://localhost:6379"
export DATABASE_URL="postgresql://user:password@localhost/saathii"
export SECRET_KEY="your-secret-key"
```

3. **Run the Server**
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

4. **Access Documentation**
- Open `http://localhost:8000/docs` for Swagger UI
- Open `http://localhost:8000/redoc` for ReDoc

## 🔧 Features

- ✅ **Real-time Updates**: WebSocket support for instant status updates
- ✅ **Scalable Architecture**: Redis pub/sub for multiple server instances
- ✅ **Comprehensive API**: Full CRUD operations for users and presence
- ✅ **Feed System**: Advanced filtering and pagination for listener discovery
- ✅ **Token Management**: Secure JWT with refresh token rotation
- ✅ **Rate Limiting**: Built-in rate limiting for OTP requests
- ✅ **Database Integration**: PostgreSQL with async support
- ✅ **Caching**: Redis for session management and caching
- ✅ **Documentation**: Auto-generated Swagger/OpenAPI documentation

## 📱 Mobile Integration

The API is designed specifically for React Native/Expo applications with:
- **WebSocket support** for real-time updates
- **Token management** with automatic refresh
- **Heartbeat system** for presence tracking
- **Feed system** with real-time listener discovery
- **Comprehensive error handling** and reconnection logic

For detailed React Native integration examples, see the `REACT_NATIVE_WEBSOCKET_EXAMPLE.md` file.