---
sidebar_position: 3
title: Presence & Status API
description: Real-time user presence tracking and status management
---

# Presence & Status API

The Presence & Status API provides real-time user presence tracking, status management, and heartbeat functionality for maintaining accurate user availability.

## Overview

- **Status Management**: Get and update user online/busy status
- **Presence Tracking**: Real-time presence information for users
- **Heartbeat System**: Keep users online with periodic heartbeats
- **Admin Functions**: Presence cleanup and maintenance

## Endpoints

### Get My Status

Retrieve the current user's presence status.

**Endpoint:** `GET /users/me/status`

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response:**
```json
{
  "user_id": 123,
  "is_online": true,
  "is_busy": false,
  "busy_until": null,
  "last_seen": "2024-01-15T10:30:00Z",
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z"
}
```

**Field Descriptions:**
- `user_id`: User identifier
- `is_online`: Current online status
- `is_busy`: Whether user is currently busy (in a call)
- `busy_until`: When busy status expires (if set)
- `last_seen`: Last activity timestamp
- `created_at`: Status record creation time
- `updated_at`: Last status update time

### Update My Status

Update the current user's presence status.

**Endpoint:** `PUT /users/me/status`

**Headers:**
```
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Request Body:**
```json
{
  "is_online": true,
  "is_busy": false,
  "busy_until": "2024-01-15T11:00:00Z"
}
```

**Field Descriptions:**
- `is_online` (optional): Set online status
- `is_busy` (optional): Set busy status
- `busy_until` (optional): Set busy status expiration time

**Response:**
```json
{
  "user_id": 123,
  "is_online": true,
  "is_busy": false,
  "busy_until": "2024-01-15T11:00:00Z",
  "last_seen": "2024-01-15T10:30:00Z",
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z"
}
```

### Send Heartbeat

Send a heartbeat to keep the user online and update last seen time.

**Endpoint:** `POST /users/me/heartbeat`

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response:**
```json
{
  "message": "Heartbeat received"
}
```

**Usage:**
- Send every 30-60 seconds to maintain online status
- Automatically updates `last_seen` timestamp
- Broadcasts status update to connected clients

### Get User Presence

Get another user's presence status.

**Endpoint:** `GET /users/{user_id}/presence`

**Headers:**
```
Authorization: Bearer <access_token>
```

**Path Parameters:**
- `user_id`: Target user's ID

**Response:**
```json
{
  "user_id": 456,
  "username": "jane_smith",
  "is_online": true,
  "is_busy": false,
  "busy_until": null,
  "last_seen": "2024-01-15T10:25:00Z"
}
```

### Get Multiple Users Presence

Get presence status for multiple users at once.

**Endpoint:** `GET /users/presence`

**Headers:**
```
Authorization: Bearer <access_token>
```

**Query Parameters:**
- `user_ids`: Comma-separated list of user IDs (max 50)

**Example Request:**
```
GET /users/presence?user_ids=123,456,789
```

**Response:**
```json
[
  {
    "user_id": 123,
    "username": "alice",
    "is_online": true,
    "is_busy": false,
    "busy_until": null,
    "last_seen": "2024-01-15T10:30:00Z"
  },
  {
    "user_id": 456,
    "username": "jane_smith",
    "is_online": true,
    "is_busy": true,
    "busy_until": "2024-01-15T11:00:00Z",
    "last_seen": "2024-01-15T10:25:00Z"
  }
]
```

### Cleanup Presence (Admin)

Manually trigger presence cleanup for inactive users.

**Endpoint:** `POST /admin/cleanup-presence`

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response:**
```json
{
  "message": "Presence cleanup completed",
  "users_marked_offline": 15,
  "busy_status_cleared": 3
}
```

**Cleanup Actions:**
- Marks users offline if inactive for 5+ minutes
- Clears expired busy status
- Updates last seen timestamps

## Status Types

### Online Status
- `is_online: true` - User is currently active
- `is_online: false` - User is offline or inactive

### Busy Status
- `is_busy: true` - User is in a call or unavailable
- `is_busy: false` - User is available for calls
- `busy_until` - Optional expiration time for busy status

## Real-time Updates

### WebSocket Integration

Presence updates are broadcast in real-time via WebSocket:

**Connection:**
```
wss://your-api-domain.com/ws/presence?token=<access_token>
```

**Message Format:**
```json
{
  "type": "presence_update",
  "data": {
    "user_id": 123,
    "is_online": true,
    "is_busy": false,
    "last_seen": "2024-01-15T10:30:00Z"
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### Update Triggers

Status updates are broadcast when:
- User goes online/offline
- User becomes busy/available
- Heartbeat is received
- Call starts/ends
- Manual status update

## Error Responses

### 400 Bad Request
```json
{
  "detail": "No status fields to update"
}
```

### 401 Unauthorized
```json
{
  "detail": "Invalid or expired token"
}
```

### 404 Not Found
```json
{
  "detail": "User status not found"
}
```

### 400 Too Many Users
```json
{
  "detail": "Too many user IDs requested"
}
```

## Integration Examples

### React Native Integration

```typescript
// services/PresenceService.ts
import ApiService from './ApiService';

export interface UserStatus {
  user_id: number;
  is_online: boolean;
  is_busy: boolean;
  busy_until?: string;
  last_seen: string;
  created_at: string;
  updated_at: string;
}

export interface UserPresence {
  user_id: number;
  username: string;
  is_online: boolean;
  is_busy: boolean;
  busy_until?: string;
  last_seen: string;
}

class PresenceService {
  // Get my status
  async getMyStatus(): Promise<UserStatus> {
    return ApiService.get<UserStatus>('/users/me/status');
  }

  // Update my status
  async updateMyStatus(data: Partial<UserStatus>): Promise<UserStatus> {
    return ApiService.put<UserStatus>('/users/me/status', data);
  }

  // Send heartbeat
  async sendHeartbeat(): Promise<{ message: string }> {
    return ApiService.post<{ message: string }>('/users/me/heartbeat');
  }

  // Get user presence
  async getUserPresence(userId: number): Promise<UserPresence> {
    return ApiService.get<UserPresence>(`/users/${userId}/presence`);
  }

  // Get multiple users presence
  async getMultipleUsersPresence(userIds: number[]): Promise<UserPresence[]> {
    const ids = userIds.join(',');
    return ApiService.get<UserPresence[]>(`/users/presence?user_ids=${ids}`);
  }
}

export default new PresenceService();
```

### cURL Examples

```bash
# Get my status
curl -X GET "http://localhost:8000/users/me/status" \
  -H "Authorization: Bearer <access_token>"

# Update my status
curl -X PUT "http://localhost:8000/users/me/status" \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{"is_online": true, "is_busy": false}'

# Send heartbeat
curl -X POST "http://localhost:8000/users/me/heartbeat" \
  -H "Authorization: Bearer <access_token>"

# Get user presence
curl -X GET "http://localhost:8000/users/456/presence" \
  -H "Authorization: Bearer <access_token>"

# Get multiple users presence
curl -X GET "http://localhost:8000/users/presence?user_ids=123,456,789" \
  -H "Authorization: Bearer <access_token>"
```

## Best Practices

### Status Management

1. **Heartbeat Frequency**: Send heartbeats every 30-60 seconds
2. **Status Updates**: Update status immediately when going busy/available
3. **Error Handling**: Handle network errors gracefully
4. **Offline Detection**: Implement proper offline detection

### Real-time Updates

1. **WebSocket Connection**: Maintain persistent WebSocket connection
2. **Reconnection Logic**: Implement automatic reconnection
3. **Status Broadcasting**: Listen for status updates from other users
4. **UI Updates**: Update UI immediately when status changes

### Performance

1. **Batch Requests**: Use multiple users presence for efficiency
2. **Caching**: Cache presence data locally
3. **Rate Limiting**: Respect API rate limits
4. **Background Handling**: Handle presence in background properly

## Next Steps

- Learn about [User Management API](./user-management) for profile operations
- Explore [Feed System API](./feeds) for discovering users
- Check out [WebSocket Integration](./websocket-realtime) for live updates
