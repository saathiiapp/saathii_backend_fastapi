---
sidebar_position: 7
title: Blocking API
description: User blocking and reporting functionality
---

# Blocking API

The Blocking API provides comprehensive user blocking and reporting functionality, allowing users to block other users and manage their blocked list.

## Overview

- **Block Users**: Block users with optional reasons
- **Unblock Users**: Remove users from blocked list
- **Blocked List**: View paginated list of blocked users
- **Status Checking**: Check if a user is blocked
- **Reporting**: Report users with different action types
- **Filtering**: Filter blocked users by action type

## Endpoints

### Block User

Block a user with optional reason.

**Endpoint:** `POST /block`

**Headers:**
```
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Request Body:**
```json
{
  "blocked_id": 123,
  "action_type": "block",
  "reason": "Inappropriate behavior"
}
```

**Fields:**
- `blocked_id`: ID of the user to block
- `action_type`: Type of action ("block" or "report")
- `reason`: Optional reason for blocking

**Response:**
```json
{
  "success": true,
  "message": "Successfully blocked jane_smith",
  "blocked_id": 123,
  "action_type": "block",
  "is_blocked": true
}
```

**Error Responses:**
- `400 Bad Request` - Cannot block yourself
- `404 Not Found` - User not found
- `409 Conflict` - Already blocked (returns success with message)

### Unblock User

Remove a user from your blocked list.

**Endpoint:** `DELETE /block`

**Headers:**
```
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Request Body:**
```json
{
  "blocked_id": 123
}
```

**Fields:**
- `blocked_id`: ID of the user to unblock

**Response:**
```json
{
  "success": true,
  "message": "Successfully unblocked jane_smith",
  "blocked_id": 123,
  "action_type": "unblock",
  "is_blocked": false
}
```

**Error Responses:**
- `404 Not Found` - User not found
- `409 Conflict` - Not blocked (returns success with message)

### Get Blocked Users

Get a paginated list of users you have blocked.

**Endpoint:** `GET /blocked`

**Headers:**
```
Authorization: Bearer <access_token>
```

**Query Parameters:**

| Parameter | Type | Description | Default |
|-----------|------|-------------|---------|
| `page` | integer | Page number (1-based) | 1 |
| `per_page` | integer | Items per page (max 100) | 20 |
| `action_type` | string | Filter by action type ("block", "report") | null |

**Example Request:**
```
GET /blocked?page=1&per_page=10&action_type=block
```

**Response:**
```json
{
  "blocked_users": [
    {
      "user_id": 123,
      "username": "jane_smith",
      "sex": "female",
      "bio": "Professional listener...",
      "profile_image_url": "https://example.com/profile.jpg",
      "action_type": "block",
      "reason": "Inappropriate behavior",
      "blocked_at": "2024-01-15T10:30:00Z"
    }
  ],
  "total_count": 5,
  "page": 1,
  "per_page": 10,
  "has_next": false,
  "has_previous": false
}
```

**Field Descriptions:**
- `user_id`: Unique user identifier
- `username`: User's display name
- `sex`: Gender ("male", "female")
- `bio`: User biography/description
- `profile_image_url`: Profile image URL
- `action_type`: Type of action taken ("block", "report")
- `reason`: Reason for blocking (if provided)
- `blocked_at`: When the user was blocked

### Check Block Status

Check if a specific user is blocked by you.

**Endpoint:** `GET /block/check/{user_id}`

**Headers:**
```
Authorization: Bearer <access_token>
```

**Path Parameters:**
- `user_id`: ID of the user to check

**Response:**
```json
{
  "success": true,
  "message": "jane_smith is blocked",
  "blocked_id": 123,
  "action_type": "block",
  "is_blocked": true
}
```

**Error Responses:**
- `404 Not Found` - User not found

## Action Types

### Block Action

**Type:** `"block"`
**Description:** Block the user from appearing in feeds and prevent communication
**Usage:** Use when you want to completely block a user

### Report Action

**Type:** `"report"`
**Description:** Report the user for review by moderators
**Usage:** Use when you want to report inappropriate behavior

## Filtering Options

### Action Type Filter

Filter blocked users by action type:
```
GET /blocked?action_type=block
GET /blocked?action_type=report
```

### Combined Filters

Combine multiple filters:
```
GET /blocked?action_type=block&page=1&per_page=20
```

## Real-time Updates

### WebSocket Integration

Blocking updates are broadcast in real-time via WebSocket:

**Connection:**
```
wss://your-api-domain.com/ws/feed?token=<access_token>
```

**Message Types:**
- `user_blocked` - User blocked you
- `user_unblocked` - User unblocked you

**Example Message:**
```json
{
  "type": "user_blocked",
  "data": {
    "user_id": 123,
    "username": "jane_smith",
    "action": "blocked_you"
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

## Error Handling

### Common Error Responses

**Cannot Block Self (400):**
```json
{
  "detail": "Cannot block yourself"
}
```

**User Not Found (404):**
```json
{
  "detail": "User not found"
}
```

**Already Blocked (200):**
```json
{
  "success": true,
  "message": "Already blocked jane_smith",
  "blocked_id": 123,
  "action_type": "block",
  "is_blocked": true
}
```

**Not Blocked (200):**
```json
{
  "success": true,
  "message": "jane_smith was not blocked",
  "blocked_id": 123,
  "action_type": "unblock",
  "is_blocked": false
}
```

## Integration Examples

### React Native Integration

```typescript
// services/BlockingService.ts
import ApiService from './ApiService';

export interface BlockedUser {
  user_id: number;
  username: string;
  sex: string;
  bio: string;
  profile_image_url: string;
  action_type: string;
  reason: string | null;
  blocked_at: string;
}

export interface BlockedUsersResponse {
  blocked_users: BlockedUser[];
  total_count: number;
  page: number;
  per_page: number;
  has_next: boolean;
  has_previous: boolean;
}

export interface BlockActionResponse {
  success: boolean;
  message: string;
  blocked_id: number;
  action_type: string;
  is_blocked: boolean;
}

class BlockingService {
  // Block user
  async blockUser(blockedId: number, actionType: string = 'block', reason?: string): Promise<BlockActionResponse> {
    return ApiService.post<BlockActionResponse>('/block', {
      blocked_id: blockedId,
      action_type: actionType,
      reason: reason
    });
  }

  // Unblock user
  async unblockUser(blockedId: number): Promise<BlockActionResponse> {
    return ApiService.delete<BlockActionResponse>('/block', {
      blocked_id: blockedId
    });
  }

  // Get blocked users
  async getBlockedUsers(filters: {
    page?: number;
    per_page?: number;
    action_type?: string;
  } = {}): Promise<BlockedUsersResponse> {
    const params = new URLSearchParams();
    
    Object.entries(filters).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        params.append(key, value.toString());
      }
    });

    return ApiService.get<BlockedUsersResponse>(`/blocked?${params.toString()}`);
  }

  // Check block status
  async checkBlockStatus(userId: number): Promise<BlockActionResponse> {
    return ApiService.get<BlockActionResponse>(`/block/check/${userId}`);
  }
}

export default new BlockingService();
```

### JavaScript/WebSocket Integration

```javascript
class BlockingWebSocketManager {
  constructor(token) {
    this.token = token;
    this.ws = null;
  }

  connect() {
    const wsUrl = `wss://your-api-domain.com/ws/feed?token=${this.token}`;
    this.ws = new WebSocket(wsUrl);

    this.ws.onopen = () => {
      console.log('Blocking WebSocket connected');
    };

    this.ws.onmessage = (event) => {
      const message = JSON.parse(event.data);
      this.handleMessage(message);
    };

    this.ws.onclose = () => {
      console.log('Blocking WebSocket disconnected');
    };
  }

  handleMessage(message) {
    switch (message.type) {
      case 'user_blocked':
        this.onUserBlocked?.(message.data);
        break;
      case 'user_unblocked':
        this.onUserUnblocked?.(message.data);
        break;
      default:
        // Handle other message types
        break;
    }
  }

  disconnect() {
    if (this.ws) {
      this.ws.close();
    }
  }
}
```

### cURL Examples

**Block User:**
```bash
curl -X POST 'https://saathiiapp.com/block' \
  -H 'Authorization: Bearer <access_token>' \
  -H 'Content-Type: application/json' \
  -d '{
    "blocked_id": 123,
    "action_type": "block",
    "reason": "Inappropriate behavior"
  }'
```

**Unblock User:**
```bash
curl -X DELETE 'https://saathiiapp.com/block' \
  -H 'Authorization: Bearer <access_token>' \
  -H 'Content-Type: application/json' \
  -d '{"blocked_id": 123}'
```

**Get Blocked Users:**
```bash
curl -X GET 'https://saathiiapp.com/blocked?page=1&per_page=10&action_type=block' \
  -H 'Authorization: Bearer <access_token>'
```

**Check Block Status:**
```bash
curl -X GET 'https://saathiiapp.com/block/check/123' \
  -H 'Authorization: Bearer <access_token>'
```

## Best Practices

### User Experience

1. **Confirmation**: Always confirm before blocking users
2. **Clear Feedback**: Provide clear feedback about blocking actions
3. **Easy Unblocking**: Make it easy to unblock users
4. **Reason Tracking**: Track reasons for better moderation

### Privacy and Safety

1. **Immediate Effect**: Blocking should take effect immediately
2. **Data Protection**: Protect blocked user data appropriately
3. **Moderation**: Use reporting for serious issues
4. **Appeal Process**: Consider appeal process for blocked users

### Performance

1. **Pagination**: Use pagination for blocked users list
2. **Caching**: Cache block status for better performance
3. **Real-time Updates**: Use WebSocket for live updates
4. **Efficient Queries**: Optimize database queries for block checks

## Next Steps

- Learn about [Favorites API](./favorites) for managing favorite listeners
- Explore [Call Management API](./call-management) for making calls
- Check out [Feed System API](./feeds) for discovering users
- Access the [WebSocket Integration](./websocket-realtime) for real-time updates