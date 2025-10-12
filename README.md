# Saathii Backend FastAPI

A scalable FastAPI backend for the Saathii application with authentication, user management, presence features, and real-time WebSocket updates.

## 🚀 Features

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
- **Comprehensive API Documentation** with Swagger UI

## 📋 Table of Contents

- [Base URL](#base-url)
- [Authentication](#authentication)
- [User Management](#user-management)
- [Presence & Status](#presence--status)
- [Feed System](#feed-system)
- [Listener Verification](#listener-verification)
- [S3 File Upload](#s3-file-upload)
- [Call Management](#call-management)
- [WebSocket Real-time Updates](#websocket-real-time-updates)
- [React Native Integration](#react-native-integration)
- [API Examples](#api-examples)
- [Swagger Documentation](#swagger-documentation)
- [Getting Started](#-getting-started)

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
- **Tags**: Authentication
- **Body**:
```json
{ "phone": "+919876543210" }
```
- **Responses**:
  - `200` - `{ "message": "OTP sent" }`
  - `429` - Too many requests (rate limit: 5 per 15 minutes)

#### 2. Resend OTP
- **Endpoint**: `POST /auth/resend_otp`
- **Tags**: Authentication
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
- **Tags**: Authentication
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
- **Tags**: Authentication
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
- **Tags**: Authentication
- **Body**:
```json
{ "refresh_token": "..." }
```
- **Response**: `200` - `{ "access_token": "...", "refresh_token": "..." }`
- **Notes**: Refresh tokens are single-use. If reused, server returns 401.

#### 6. Logout
- **Endpoint**: `POST /auth/logout`
- **Tags**: Authentication
- **Headers**: `Authorization: Bearer <access_token>`
- **Behavior**: Blacklists current access token and revokes all refresh tokens for the user
- **Response**: `200` - `{ "message": "Logged out" }`

## User Management

### Profile Endpoints

#### 1. Get Current User
- **Endpoint**: `GET /users/me`
- **Tags**: User Management
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
- **Tags**: User Management
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
- **Tags**: User Management
- **Headers**: `Authorization: Bearer <access_token>`
- **Response**: `200` - `{ "message": "User deleted" }`

## Presence & Status

### Status Endpoints

#### 1. Get My Status
- **Endpoint**: `GET /users/me/status`
- **Tags**: User Management
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
- **Tags**: User Management
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
- **Tags**: User Management
- **Headers**: `Authorization: Bearer <access_token>`
- **Response**: `200` - `{ "message": "Heartbeat received" }`
- **Note**: Updates last_seen and triggers real-time broadcast

#### 4. Get User Presence
- **Endpoint**: `GET /users/{user_id}/presence`
- **Tags**: User Management
- **Headers**: `Authorization: Bearer <access_token>`
- **Response**: `200` - User's presence status

#### 5. Get Multiple Users Presence
- **Endpoint**: `GET /users/presence`
- **Tags**: User Management
- **Headers**: `Authorization: Bearer <access_token>`
- **Query Parameters**:
  - `user_ids`: Comma-separated user IDs
- **Response**: `200` - Array of user presence data

## Feed System

### Feed Endpoints

#### 1. Get Listeners Feed
- **Endpoint**: `GET /feed/listeners`
- **Tags**: User Management
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
- **Tags**: User Management
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

## Listener Verification

### Overview
The listener verification system allows listeners to upload audio samples for verification before they can start working. This ensures quality control and authenticity of listeners on the platform.

### Verification Endpoints

#### 1. Upload Audio File (Direct Upload)
- **Endpoint**: `POST /verification/upload-audio-file`
- **Tags**: Listener Verification
- **Headers**: `Authorization: Bearer <access_token>`
- **Content-Type**: `multipart/form-data`
- **Body**: Audio file (mp3, wav, m4a, etc.)
- **Max file size**: 10MB
- **Response**: `200` - Verification record created
```json
{
  "sample_id": 1,
  "listener_id": 123,
  "audio_file_url": "https://bucket-name.s3.region.amazonaws.com/verification-audio/123/20240115_103000_abc12345.mp3",
  "status": "pending",
  "remarks": null,
  "uploaded_at": "2024-01-15T10:30:00Z",
  "reviewed_at": null
}
```

#### 2. Upload Audio URL (External Upload)
- **Endpoint**: `POST /verification/upload-audio-url`
- **Tags**: Listener Verification
- **Headers**: `Authorization: Bearer <access_token>`
- **Body**:
```json
{
  "audio_file_url": "https://bucket-name.s3.region.amazonaws.com/verification-audio/123/20240115_103000_abc12345.mp3"
}
```
- **Response**: `200` - Verification record created

#### 3. Check Verification Status
- **Endpoint**: `GET /verification/status`
- **Tags**: Listener Verification
- **Headers**: `Authorization: Bearer <access_token>`
- **Response**: `200` - Current verification status
```json
{
  "is_verified": false,
  "verification_status": "pending",
  "last_verification": {
    "sample_id": 1,
    "listener_id": 123,
    "audio_file_url": "https://bucket-name.s3.region.amazonaws.com/verification-audio/123/20240115_103000_abc12345.mp3",
    "status": "pending",
    "remarks": null,
    "uploaded_at": "2024-01-15T10:30:00Z",
    "reviewed_at": null
  },
  "message": "Verification status: pending"
}
```

#### 4. Get Verification History
- **Endpoint**: `GET /verification/history`
- **Tags**: Listener Verification
- **Headers**: `Authorization: Bearer <access_token>`
- **Response**: `200` - Array of verification records

### Admin Verification Endpoints

#### 1. Get Pending Verifications
- **Endpoint**: `GET /admin/verification/pending`
- **Tags**: Admin - Verification
- **Headers**: `Authorization: Bearer <access_token>`
- **Query Parameters**:
  - `page` (int): Page number (default: 1)
  - `per_page` (int): Items per page (default: 20, max: 100)
- **Response**: `200` - Array of pending verification requests

#### 2. Review Verification
- **Endpoint**: `POST /admin/verification/review`
- **Tags**: Admin - Verification
- **Headers**: `Authorization: Bearer <access_token>`
- **Body**:
```json
{
  "sample_id": 1,
  "status": "approved",
  "remarks": "Audio quality is good, voice is clear and professional"
}
```
- **Response**: `200` - Review completed
```json
{
  "success": true,
  "message": "Verification approved successfully with remarks: Audio quality is good, voice is clear and professional",
  "verification": {
    "sample_id": 1,
    "listener_id": 123,
    "audio_file_url": "https://bucket-name.s3.region.amazonaws.com/verification-audio/123/20240115_103000_abc12345.mp3",
    "status": "approved",
    "remarks": "Audio quality is good, voice is clear and professional",
    "uploaded_at": "2024-01-15T10:30:00Z",
    "reviewed_at": "2024-01-15T14:45:00Z"
  }
}
```

### Verification Statuses
- **pending**: Awaiting admin review
- **approved**: Verification approved, listener can work
- **rejected**: Verification rejected, needs new audio sample

### Security Features
- ✅ **Role-based access**: Only listeners can upload, only admins can review
- ✅ **File validation**: Audio files only, 10MB size limit
- ✅ **Pending prevention**: One pending verification per listener
- ✅ **S3 integration**: Secure file storage with metadata tracking

## S3 File Upload

### Overview
The system supports direct file uploads to AWS S3 for listener verification audio samples. Files are organized by user and include metadata for tracking.

### S3 Configuration

#### Environment Variables
```bash
AWS_ACCESS_KEY_ID=your-aws-access-key-id
AWS_SECRET_ACCESS_KEY=your-aws-secret-access-key
AWS_REGION=us-east-1
S3_BUCKET_NAME=your-s3-bucket-name
```

#### File Organization
```
S3 Bucket Structure:
bucket-name/
└── verification-audio/
    └── {user_id}/
        └── {timestamp}_{unique_id}.{extension}
```

Example: `verification-audio/123/20240115_103000_abc12345.mp3`

### Upload Methods

#### 1. Direct File Upload
- **Endpoint**: `POST /verification/upload-audio-file`
- **Method**: Multipart form data
- **Features**:
  - Automatic S3 upload
  - File type validation (audio only)
  - Size limit enforcement (10MB)
  - Unique file naming
  - Metadata tracking

#### 2. S3 URL Submission
- **Endpoint**: `POST /verification/upload-audio-url`
- **Method**: JSON with S3 URL
- **Use case**: External uploads or pre-uploaded files

### Security & Validation
- **File Type**: Only audio files (mp3, wav, m4a, etc.)
- **File Size**: Maximum 10MB per file
- **User Role**: Only users with 'listener' role can upload
- **Pending Check**: Prevents multiple pending verifications
- **S3 Metadata**: Includes user_id and upload metadata

### Error Handling
- **403 Forbidden**: User doesn't have listener role
- **400 Bad Request**: Invalid file type, size, or existing pending verification
- **500 Internal Server Error**: S3 configuration issues or upload failures

## Call Management

### Overview
- **Coin-based billing system** with real-time balance tracking
- **Call lifecycle management** with automatic status updates
- **User availability tracking** to prevent conflicts
- **Comprehensive edge case handling** for dropped calls and insufficient funds

### Call Endpoints

#### 1. Start Call
- **Endpoint**: `POST /calls/start`
- **Tags**: Call Management
- **Headers**: `Authorization: Bearer <access_token>`
- **Body**:
```json
{
  "listener_id": 123,
  "call_type": "audio",
  "estimated_duration_minutes": 30
}
```
- **Response**: `200` - Call started with cost estimation
```json
{
  "call_id": 456,
  "message": "Call started successfully",
  "estimated_cost": 300,
  "remaining_coins": 700,
  "call_type": "audio",
  "listener_id": 123,
  "status": "ongoing"
}
```

#### 2. End Call
- **Endpoint**: `POST /calls/end`
- **Tags**: Call Management
- **Headers**: `Authorization: Bearer <access_token>`
- **Body**:
```json
{
  "call_id": 456,
  "reason": "completed"
}
```
- **Response**: `200` - Call ended with final billing
```json
{
  "call_id": 456,
  "message": "Call ended successfully",
  "duration_seconds": 1800,
  "duration_minutes": 30,
  "coins_spent": 300,
  "user_money_spend": 300,
  "listener_money_earned": 240,
  "status": "completed"
}
```

#### 3. Get Ongoing Call
- **Endpoint**: `GET /calls/ongoing`
- **Tags**: Call Management
- **Headers**: `Authorization: Bearer <access_token>`
- **Response**: `200` - Current ongoing call details

#### 4. Get Call History
- **Endpoint**: `GET /calls/history`
- **Tags**: Call Management
- **Headers**: `Authorization: Bearer <access_token>`
- **Query Parameters**:
  - `page` (int): Page number (default: 1)
  - `per_page` (int): Items per page (default: 20, max: 100)
  - `call_type` (str): Filter by call type (audio, video)
  - `status` (str): Filter by status (ongoing, completed, dropped)
- **Response**: `200` - Paginated call history with statistics
```json
{
  "calls": [
    {
      "call_id": 456,
      "user_id": 123,
      "listener_id": 789,
      "call_type": "audio",
      "start_time": "2024-01-15T10:30:00Z",
      "end_time": "2024-01-15T11:00:00Z",
      "duration_seconds": 1800,
      "duration_minutes": 30,
      "coins_spent": 300,
      "user_money_spend": 300,
      "listener_money_earned": 450,
      "status": "completed",
      "caller_username": "john_doe",
      "listener_username": "jane_smith"
    }
  ],
  "total_calls": 25,
  "total_coins_spent": 1500,
  "total_money_spent": 1500,
  "total_earnings": 2250,
  "page": 1,
  "per_page": 20,
  "has_next": true,
  "has_previous": false
}
```

#### 5. Get Call History Summary
- **Endpoint**: `GET /calls/history/summary`
- **Tags**: Call Management
- **Headers**: `Authorization: Bearer <access_token>`
- **Response**: `200` - Call history summary with statistics
```json
{
  "summary": {
    "total_calls": 25,
    "calls_made": 15,
    "calls_received": 10,
    "completed_calls": 20,
    "dropped_calls": 3,
    "ongoing_calls": 2,
    "audio_calls": 18,
    "video_calls": 7,
    "total_coins_spent": 1500,
    "total_money_spent": 1500,
    "total_earnings": 2250,
    "total_duration_seconds": 54000,
    "avg_duration_seconds": 2160
  },
  "recent_calls": [...],
  "monthly_stats": [
    {
      "month": "2024-01-01T00:00:00Z",
      "calls_count": 8,
      "coins_spent": 400,
      "earnings": 600
    }
  ]
}
```

#### 6. Get Coin Balance
- **Endpoint**: `GET /calls/balance`
- **Tags**: Call Management
- **Headers**: `Authorization: Bearer <access_token>`
- **Response**: `200` - User's coin balance and transaction history
```json
{
  "user_id": 123,
  "current_balance": 500,
  "total_earned": 1000,
  "total_spent": 500
}
```

#### 7. Emergency End Call
- **Endpoint**: `POST /calls/emergency-end/{call_id}`
- **Tags**: Call Management
- **Headers**: `Authorization: Bearer <access_token>`
- **Response**: `200` - Emergency call termination

#### 8. Recharge Coins
- **Endpoint**: `POST /calls/recharge`
- **Tags**: Call Management
- **Headers**: `Authorization: Bearer <access_token>`
- **Body**:
```json
{
  "amount_rupees": 150,
  "payment_method": "upi"
}
```
- **Response**: `200` - Recharge successful
```json
{
  "transaction_id": "RCH_123_1640995200",
  "amount_rupees": 150,
  "coins_added": 300,
  "new_balance": 500,
  "message": "Successfully recharged 300 coins for ₹150"
}
```

#### 9. Get Recharge History
- **Endpoint**: `GET /calls/recharge/history`
- **Tags**: Call Management
- **Headers**: `Authorization: Bearer <access_token>`
- **Query Parameters**:
  - `page` (int): Page number (default: 1)
  - `per_page` (int): Items per page (default: 20, max: 100)
- **Response**: `200` - Paginated recharge history

#### 10. Bill Call Minute
- **Endpoint**: `POST /calls/bill-minute/{call_id}`
- **Tags**: Call Management
- **Headers**: `Authorization: Bearer <access_token>`
- **Response**: `200` - Successfully billed for 1 minute
```json
{
  "call_id": 456,
  "coins_deducted": 10,
  "remaining_coins": 290,
  "total_coins_spent": 20,
  "message": "Successfully billed for 1 minute"
}
```

#### 11. Cleanup Calls
- **Endpoint**: `POST /calls/cleanup`
- **Tags**: Call Management
- **Headers**: `Authorization: Bearer <access_token>`
- **Response**: `200` - Call cleanup completed
```json
{
  "message": "Call cleanup completed successfully"
}
```

#### 12. Get Call System Status
- **Endpoint**: `GET /calls/status`
- **Tags**: Call Management
- **Headers**: `Authorization: Bearer <access_token>`
- **Response**: `200` - System status and ongoing calls info
```json
{
  "ongoing_calls": 5,
  "busy_users": 10,
  "redis_call_keys": 5,
  "system_status": "healthy"
}
```

#### 13. Get Call Rates
- **Endpoint**: `GET /calls/rates`
- **Tags**: Call Management
- **Response**: `200` - Current call rates and recharge options
```json
{
  "call_rates": {
    "audio": {
      "rate_per_minute": 10,
      "minimum_charge": 10
    },
    "video": {
      "rate_per_minute": 50,
      "minimum_charge": 50
    }
  },
  "recharge_options": {
    "150": 300,
    "300": 600,
    "500": 1000,
    "1000": 2000
  },
  "listener_earnings": {
    "audio": 15,
    "video": 75
  }
}
```

### Call Lifecycle

1. **Call Start**:
   - Validates user and listener availability
   - Calculates maximum possible duration based on available coins
   - Reserves minimum charge (10 coins for audio, 50 for video)
   - **🔄 Auto-updates both users' presence status to busy**
   - **📡 Broadcasts status changes to all connected clients**
   - Creates call record in database
   - Stores call info in Redis for real-time tracking

2. **Call Duration**:
   - **Per-minute billing**: Frontend calls `/calls/bill-minute/{call_id}` every minute
   - **Automatic termination**: Call ends if insufficient coins
   - Real-time tracking via Redis
   - **📡 Continuous WebSocket broadcasts for presence changes**

3. **Call End**:
   - Calculates final duration and total cost
   - Updates listener earnings (1.5x rate per minute)
   - **🔄 Auto-updates both users' presence status to available**
   - **📡 Broadcasts status changes to all connected clients**
   - Creates transaction records
   - Removes from Redis tracking

### Automatic Presence Status Updates

The system automatically manages user presence status during calls:

- **Call Start**: Both caller and listener become `busy: true`
- **Call End**: Both users become `busy: false` and `available: true`
- **Real-time Broadcasting**: All status changes are broadcast via WebSocket
- **Parallel Updates**: Both users' status updated simultaneously for consistency
- **Automatic Cleanup**: Expired calls are cleaned up automatically

### Edge Cases Handled

#### 1. Insufficient Coins
- **During Call Start**: Returns error with required vs available coins
- **During Call**: Call automatically ends as "dropped" status
- **Response**: Clear error messages and call termination

#### 2. Call Dropped
- **Technical Issues**: Emergency end call endpoint
- **Network Problems**: Automatic cleanup after timeout
- **User Disconnection**: Graceful handling with proper status updates

#### 3. User Availability
- **Already in Call**: Prevents multiple simultaneous calls
- **Listener Busy**: Validates listener availability before starting
- **Status Conflicts**: Automatic resolution and cleanup

#### 4. Call Timeout
- **Maximum Duration**: 2-hour limit with automatic termination
- **Redis Cleanup**: Automatic removal of expired call data
- **Status Recovery**: Proper cleanup on system restart

### Coin Management

- **Wallet Integration**: Uses existing `user_wallets` table
- **Transaction Tracking**: All coin movements recorded in `user_transactions`
- **Real-time Balance**: Live balance updates during calls
- **Recharge System**: Users can add coins with real money
- **Per-minute Billing**: Coins deducted every minute during calls
- **Earnings Distribution**: Listeners earn 1.5x the call rate

### Call Rates

- **Audio Calls**: 10 coins per minute, 10 coin minimum
- **Video Calls**: 50 coins per minute, 50 coin minimum
- **Listener Earnings**: 15 coins/min (audio), 75 coins/min (video)
- **Configurable**: Rates can be updated via configuration
- **Transparent**: Rates exposed via API endpoint

### Recharge Options

- **₹150 = 300 coins** (2:1 ratio)
- **₹300 = 600 coins** (2:1 ratio)
- **₹500 = 1000 coins** (2:1 ratio)
- **₹1000 = 2000 coins** (2:1 ratio)
- **Transaction History**: Complete recharge tracking

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

interface UseWebSocketProps {
  url: string;
  onMessage?: (message: WebSocketMessage) => void;
  onConnect?: () => void;
  onDisconnect?: () => void;
  reconnectInterval?: number;
}

export const useWebSocket = ({
  url,
  onMessage,
  onConnect,
  onDisconnect,
  reconnectInterval = 5000
}: UseWebSocketProps) => {
  const [isConnected, setIsConnected] = useState(false);
  const [connectionError, setConnectionError] = useState<string | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  const connect = async () => {
    try {
      // Get access token from storage
      const token = await AsyncStorage.getItem('access_token');
      if (!token) {
        setConnectionError('No access token found');
        return;
      }

      const wsUrl = `${url}?token=${token}`;
      const ws = new WebSocket(wsUrl);
      
      ws.onopen = () => {
        console.log('WebSocket connected');
        setIsConnected(true);
        setConnectionError(null);
        onConnect?.();
      };

      ws.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data);
          console.log('WebSocket message received:', message);
          onMessage?.(message);
        } catch (error) {
          console.error('Error parsing WebSocket message:', error);
        }
      };

      ws.onclose = (event) => {
        console.log('WebSocket disconnected:', event.code, event.reason);
        setIsConnected(false);
        onDisconnect?.();
        
        // Attempt to reconnect if not a clean close
        if (event.code !== 1000) {
          reconnectTimeoutRef.current = setTimeout(() => {
            console.log('Attempting to reconnect...');
            connect();
          }, reconnectInterval);
        }
      };

      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        setConnectionError('WebSocket connection error');
      };

      wsRef.current = ws;
    } catch (error) {
      console.error('Error connecting to WebSocket:', error);
      setConnectionError('Failed to connect to WebSocket');
    }
  };

  const disconnect = () => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }
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

  const ping = () => {
    sendMessage({
      type: 'ping',
      timestamp: new Date().toISOString()
    });
  };

  useEffect(() => {
    connect();
    
    return () => {
      disconnect();
    };
  }, []);

  return {
    isConnected,
    connectionError,
    connect,
    disconnect,
    sendMessage,
    ping
  };
};
```

### Feed Page with Real-time Updates

```typescript
// screens/FeedScreen.tsx
import React, { useState, useEffect, useCallback } from 'react';
import { View, Text, FlatList, RefreshControl, Alert } from 'react-native';
import { useWebSocket } from '../hooks/useWebSocket';

interface Listener {
  user_id: number;
  username: string;
  profile_image_url?: string;
  is_online: boolean;
  is_available: boolean;
  is_busy: boolean;
  last_seen: string;
  rating?: number;
  bio?: string;
  interests?: string[];
}

interface FeedResponse {
  listeners: Listener[];
  total_count: number;
  online_count: number;
  available_count: number;
  page: number;
  per_page: number;
  has_next: boolean;
  has_previous: boolean;
}

const FeedScreen = () => {
  const [listeners, setListeners] = useState<Listener[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [feedStats, setFeedStats] = useState({
    total_count: 0,
    online_count: 0,
    available_count: 0
  });

  // WebSocket for real-time updates
  const { isConnected, connectionError, ping } = useWebSocket({
    url: 'ws://localhost:8000/ws/feed',
    onMessage: handleWebSocketMessage,
    onConnect: () => {
      console.log('Connected to feed updates');
      // Send ping to keep connection alive
      ping();
    },
    onDisconnect: () => {
      console.log('Disconnected from feed updates');
    }
  });

  // Handle incoming WebSocket messages
  function handleWebSocketMessage(message: any) {
    console.log('Received WebSocket message:', message);
    
    switch (message.type) {
      case 'user_status_update':
        handleUserStatusUpdate(message);
        break;
      case 'pong':
        // Connection is alive, schedule next ping
        setTimeout(ping, 30000); // Ping every 30 seconds
        break;
      case 'connection_established':
        console.log('Feed WebSocket connection established');
        break;
      default:
        console.log('Unknown message type:', message.type);
    }
  }

  // Handle user status updates
  const handleUserStatusUpdate = useCallback((message: any) => {
    const { user_id, status } = message;
    
    setListeners(prevListeners => {
      const updatedListeners = [...prevListeners];
      const index = updatedListeners.findIndex(listener => listener.user_id === user_id);
      
      if (index !== -1) {
        // Update existing listener
        updatedListeners[index] = {
          ...updatedListeners[index],
          ...status
        };
      } else if (status.is_online) {
        // Add new online listener to the top
        updatedListeners.unshift({
          user_id: status.user_id,
          username: status.username,
          profile_image_url: status.profile_image_url,
          is_online: status.is_online,
          is_available: status.is_available,
          is_busy: status.is_busy,
          last_seen: status.last_seen,
          rating: 0,
          bio: '',
          interests: []
        });
      }
      
      return updatedListeners;
    });

    // Update feed stats
    setFeedStats(prevStats => {
      const newStats = { ...prevStats };
      
      if (status.is_online) {
        newStats.online_count = Math.max(0, newStats.online_count + 1);
        if (status.is_available) {
          newStats.available_count = Math.max(0, newStats.available_count + 1);
        }
      } else {
        newStats.online_count = Math.max(0, newStats.online_count - 1);
        if (status.is_available) {
          newStats.available_count = Math.max(0, newStats.available_count - 1);
        }
      }
      
      return newStats;
    });
  }, []);

  // Load initial feed data
  const loadFeedData = async () => {
    try {
      const token = await AsyncStorage.getItem('access_token');
      const response = await fetch('http://localhost:8000/feed/listeners', {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });
      
      if (response.ok) {
        const data: FeedResponse = await response.json();
        setListeners(data.listeners);
        setFeedStats({
          total_count: data.total_count,
          online_count: data.online_count,
          available_count: data.available_count
        });
      } else {
        Alert.alert('Error', 'Failed to load feed data');
      }
    } catch (error) {
      console.error('Error loading feed data:', error);
      Alert.alert('Error', 'Network error');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  // Refresh feed data
  const onRefresh = () => {
    setRefreshing(true);
    loadFeedData();
  };

  useEffect(() => {
    loadFeedData();
  }, []);

  // Render listener item
  const renderListener = ({ item }: { item: Listener }) => (
    <View style={styles.listenerItem}>
      <View style={styles.listenerInfo}>
        <Text style={styles.username}>{item.username}</Text>
        <View style={styles.statusContainer}>
          <View style={[
            styles.statusDot, 
            { backgroundColor: item.is_available ? '#4CAF50' : item.is_online ? '#FF9800' : '#9E9E9E' }
          ]} />
          <Text style={styles.statusText}>
            {item.is_available ? 'Available' : item.is_online ? 'Online' : 'Offline'}
          </Text>
        </View>
        {item.bio && <Text style={styles.bio}>{item.bio}</Text>}
        {item.interests && item.interests.length > 0 && (
          <Text style={styles.interests}>
            Interests: {item.interests.join(', ')}
          </Text>
        )}
      </View>
    </View>
  );

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>Listeners Feed</Text>
        <View style={styles.statsContainer}>
          <Text style={styles.statsText}>
            {feedStats.available_count} available • {feedStats.online_count} online
          </Text>
          <View style={[
            styles.connectionStatus, 
            { backgroundColor: isConnected ? '#4CAF50' : '#F44336' }
          ]} />
        </View>
      </View>
      
      {connectionError && (
        <View style={styles.errorContainer}>
          <Text style={styles.errorText}>
            Connection Error: {connectionError}
          </Text>
        </View>
      )}
      
      <FlatList
        data={listeners}
        renderItem={renderListener}
        keyExtractor={(item) => item.user_id.toString()}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
        }
        ListEmptyComponent={
          <Text style={styles.emptyText}>No listeners available</Text>
        }
      />
    </View>
  );
};

const styles = {
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5'
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 16,
    backgroundColor: 'white',
    borderBottomWidth: 1,
    borderBottomColor: '#e0e0e0'
  },
  title: {
    fontSize: 20,
    fontWeight: 'bold'
  },
  statsContainer: {
    flexDirection: 'row',
    alignItems: 'center'
  },
  statsText: {
    fontSize: 12,
    color: '#666',
    marginRight: 8
  },
  connectionStatus: {
    width: 8,
    height: 8,
    borderRadius: 4
  },
  errorContainer: {
    backgroundColor: '#ffebee',
    padding: 12,
    margin: 16
  },
  errorText: {
    color: '#c62828',
    fontSize: 14
  },
  listenerItem: {
    backgroundColor: 'white',
    marginHorizontal: 16,
    marginVertical: 4,
    padding: 16,
    borderRadius: 8,
    elevation: 2
  },
  listenerInfo: {
    flex: 1
  },
  username: {
    fontSize: 16,
    fontWeight: 'bold',
    marginBottom: 4
  },
  statusContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8
  },
  statusDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    marginRight: 6
  },
  statusText: {
    fontSize: 12,
    color: '#666'
  },
  bio: {
    fontSize: 14,
    color: '#333',
    marginBottom: 4
  },
  interests: {
    fontSize: 12,
    color: '#666',
    fontStyle: 'italic'
  },
  emptyText: {
    textAlign: 'center',
    marginTop: 50,
    fontSize: 16,
    color: '#666'
  }
};

export default FeedScreen;
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
  
  // Send initial heartbeat
  sendHeartbeat();
  
  return () => clearInterval(interval);
};
```

### App Integration

```typescript
// App.tsx
import React, { useEffect } from 'react';
import { startHeartbeat } from './utils/heartbeat';
import FeedScreen from './screens/FeedScreen';

export default function App() {
  useEffect(() => {
    // Start heartbeat when app becomes active
    const stopHeartbeat = startHeartbeat();
    
    return () => {
      stopHeartbeat();
    };
  }, []);

  return <FeedScreen />;
}
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

**Start Call**
```bash
curl -X POST 'http://localhost:8000/calls/start' \
  -H 'Authorization: Bearer <ACCESS_TOKEN>' \
  -H 'Content-Type: application/json' \
  -d '{"listener_id": 123, "call_type": "audio", "estimated_duration_minutes": 30}'
```

**End Call**
```bash
curl -X POST 'http://localhost:8000/calls/end' \
  -H 'Authorization: Bearer <ACCESS_TOKEN>' \
  -H 'Content-Type: application/json' \
  -d '{"call_id": 456, "reason": "completed"}'
```

**Get Coin Balance**
```bash
curl -X GET 'http://localhost:8000/calls/balance' \
  -H 'Authorization: Bearer <ACCESS_TOKEN>'
```

**Get Call History**
```bash
curl -X GET 'http://localhost:8000/calls/history?page=1&per_page=10&call_type=audio&status=completed' \
  -H 'Authorization: Bearer <ACCESS_TOKEN>'
```

**Get Call History Summary**
```bash
curl -X GET 'http://localhost:8000/calls/history/summary' \
  -H 'Authorization: Bearer <ACCESS_TOKEN>'
```

**Recharge Coins**
```bash
curl -X POST 'http://localhost:8000/calls/recharge' \
  -H 'Authorization: Bearer <ACCESS_TOKEN>' \
  -H 'Content-Type: application/json' \
  -d '{"amount_rupees": 150, "payment_method": "upi"}'
```

**Bill Call Minute**
```bash
curl -X POST 'http://localhost:8000/calls/bill-minute/456' \
  -H 'Authorization: Bearer <ACCESS_TOKEN>'
```

**Get Call Rates**
```bash
curl -X GET 'http://localhost:8000/calls/rates'
```

**Cleanup Calls**
```bash
curl -X POST 'http://localhost:8000/calls/cleanup' \
  -H 'Authorization: Bearer <ACCESS_TOKEN>'
```

**Get Call System Status**
```bash
curl -X GET 'http://localhost:8000/calls/status' \
  -H 'Authorization: Bearer <ACCESS_TOKEN>'
```

**Upload Audio File for Verification**
```bash
curl -X POST 'http://localhost:8000/verification/upload-audio-file' \
  -H 'Authorization: Bearer <ACCESS_TOKEN>' \
  -F 'audio_file=@/path/to/audio.mp3'
```

**Upload Audio URL for Verification**
```bash
curl -X POST 'http://localhost:8000/verification/upload-audio-url' \
  -H 'Authorization: Bearer <ACCESS_TOKEN>' \
  -H 'Content-Type: application/json' \
  -d '{"audio_file_url": "https://bucket.s3.region.amazonaws.com/audio.mp3"}'
```

**Check Verification Status**
```bash
curl -X GET 'http://localhost:8000/verification/status' \
  -H 'Authorization: Bearer <ACCESS_TOKEN>'
```

**Get Verification History**
```bash
curl -X GET 'http://localhost:8000/verification/history' \
  -H 'Authorization: Bearer <ACCESS_TOKEN>'
```

**Get Pending Verifications (Admin)**
```bash
curl -X GET 'http://localhost:8000/admin/verification/pending?page=1&per_page=20' \
  -H 'Authorization: Bearer <ADMIN_ACCESS_TOKEN>'
```

**Review Verification (Admin)**
```bash
curl -X POST 'http://localhost:8000/admin/verification/review' \
  -H 'Authorization: Bearer <ADMIN_ACCESS_TOKEN>' \
  -H 'Content-Type: application/json' \
  -d '{"sample_id": 1, "status": "approved", "remarks": "Audio quality is good"}'
```

## Swagger Documentation

The API includes comprehensive Swagger documentation available at:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

### API Groups in Swagger

1. **Authentication** - OTP verification, registration, and token management
2. **User Management** - Profile management, presence tracking, and feed system
3. **Listener Verification** - Audio sample uploads and verification workflow
4. **Admin - Verification** - Admin review and approval of verification requests
5. **Call Management** - Call lifecycle, billing, and coin management
6. **WebSocket** - Real-time WebSocket connections for live updates

## 🚀 Getting Started

1. **Install Dependencies**
```bash
pip install -r requirements.txt
```

2. **Set Environment Variables**
```bash
export REDIS_URL="redis://localhost:6379"
export DATABASE_URL="postgresql://user:password@localhost/saathii"
export JWT_SECRET_KEY="your-secret-key"
export JWT_ALGORITHM="HS256"
export JWT_ACCESS_TOKEN_EXPIRE_MINUTES="30"
export JWT_REFRESH_TOKEN_EXPIRE_DAYS="7"

# AWS S3 Configuration (for file uploads)
export AWS_ACCESS_KEY_ID="your-aws-access-key-id"
export AWS_SECRET_ACCESS_KEY="your-aws-secret-access-key"
export AWS_REGION="us-east-1"
export S3_BUCKET_NAME="your-s3-bucket-name"
```

3. **Run the Server**
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

4. **Access Documentation**
- Open `http://localhost:8000/docs` for Swagger UI
- Open `http://localhost:8000/redoc` for ReDoc

5. **S3 Setup (Optional)**
- See `S3_SETUP.md` for detailed AWS S3 configuration
- Required for listener verification audio uploads

## 🔧 Features

- ✅ **Real-time Updates**: WebSocket support for instant status updates
- ✅ **Scalable Architecture**: Redis pub/sub for multiple server instances
- ✅ **Comprehensive API**: Full CRUD operations for users and presence
- ✅ **Feed System**: Advanced filtering and pagination for listener discovery
- ✅ **Listener Verification**: Audio sample uploads with admin review workflow
- ✅ **S3 File Upload**: Direct file uploads to AWS S3 with validation
- ✅ **Call Management**: Complete call lifecycle with coin-based billing
- ✅ **Coin System**: Wallet integration with transaction tracking
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

## Key Features

- ✅ **Real-time Updates**: Status changes are instantly reflected in the feed
- ✅ **Automatic Reconnection**: WebSocket reconnects on connection loss
- ✅ **Connection Status**: Visual indicator of WebSocket connection state
- ✅ **Efficient Updates**: Only updates changed user data
- ✅ **Heartbeat Integration**: Keeps user status active and triggers broadcasts
- ✅ **Error Handling**: Graceful handling of connection errors
- ✅ **Performance**: Optimized for mobile devices

This implementation ensures that when a listener goes on a call and their status is updated via the heartbeat endpoint, all connected feed pages will receive the real-time update without needing to refresh the app! 🚀