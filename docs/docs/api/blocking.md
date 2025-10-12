---
sidebar_position: 8
title: Blocking API
description: User blocking and safety features
---

# Blocking API

The Blocking API provides user blocking functionality and safety features to help users manage their interactions.

## Overview

- **User Blocking**: Block and unblock other users
- **Blocked Users List**: Manage list of blocked users
- **Status Checking**: Check if a user is blocked
- **Safety Features**: Report and block inappropriate behavior

## Endpoints

### Block User

Block a user to prevent them from contacting you.

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
- `blocked_id`: ID of the user to block (required)
- `action_type`: Type of action - "block" or "report" (optional, default: "block")
- `reason`: Optional reason for blocking (optional)

**Response:**
```json
{
  "success": true,
  "message": "User blocked successfully",
  "blocked_id": 123,
  "action_type": "block",
  "is_blocked": true
}
```

### Unblock User

Unblock a previously blocked user.

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
- `blocked_id`: ID of the user to unblock (required)

**Response:**
```json
{
  "success": true,
  "message": "User unblocked successfully",
  "blocked_id": 123,
  "action_type": "unblock",
  "is_blocked": false
}
```

### Get Blocked Users

Get paginated list of blocked users.

**Endpoint:** `GET /blocked`

**Headers:**
```
Authorization: Bearer <access_token>
```

**Query Parameters:**
- `page`: Page number (default: 1)
- `per_page`: Items per page (default: 20, max: 100)

**Response:**
```json
{
  "blocked_users": [
    {
      "user_id": 123,
      "username": "inappropriate_user",
      "sex": "male",
      "bio": "User bio...",
      "profile_image_url": "https://example.com/profile.jpg",
      "action_type": "block",
      "reason": "Inappropriate behavior",
      "blocked_at": "2024-01-15T10:30:00Z"
    }
  ],
  "total_count": 3,
  "page": 1,
  "per_page": 20,
  "has_next": false,
  "has_previous": false
}
```

**Fields:**
- `user_id`: Blocked user's ID
- `username`: Blocked user's username
- `sex`: Blocked user's gender
- `bio`: Blocked user's biography
- `profile_image_url`: Profile image URL
- `action_type`: Type of action taken
- `reason`: Reason for blocking
- `blocked_at`: When the user was blocked

### Check Block Status

Check if a specific user is blocked.

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
  "message": "User is blocked",
  "blocked_id": 123,
  "is_blocked": true
}
```

## Action Types

### Block Action
- **Type**: `"block"`
- **Description**: Block user from contacting you
- **Effect**: User cannot call, message, or see you in feeds
- **Reversible**: Yes, can be unblocked

### Report Action
- **Type**: `"report"`
- **Description**: Report user for inappropriate behavior
- **Effect**: User is blocked and reported to moderators
- **Reversible**: Yes, can be unblocked

## Error Handling

### Common Error Responses

**User Not Found (404):**
```json
{
  "detail": "User not found"
}
```

**Already Blocked (400):**
```json
{
  "detail": "User is already blocked"
}
```

**Not Blocked (400):**
```json
{
  "detail": "User is not blocked"
}
```

**Cannot Block Self (400):**
```json
{
  "detail": "Cannot block yourself"
}
```

**Invalid Action Type (400):**
```json
{
  "detail": "Invalid action type. Must be 'block' or 'report'"
}
```

## Integration Examples

### React Native Integration

```typescript
// Block user
const blockUser = async (token: string, userId: number, reason?: string) => {
  const response = await fetch('https://saathiiapp.com/block', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      blocked_id: userId,
      action_type: 'block',
      reason: reason
    })
  });
  return response.json();
};

// Unblock user
const unblockUser = async (token: string, userId: number) => {
  const response = await fetch('https://saathiiapp.com/block', {
    method: 'DELETE',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ blocked_id: userId })
  });
  return response.json();
};

// Get blocked users
const getBlockedUsers = async (token: string, page: number = 1) => {
  const response = await fetch(`https://saathiiapp.com/blocked?page=${page}&per_page=20`, {
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    }
  });
  return response.json();
};

// Check block status
const checkBlockStatus = async (token: string, userId: number) => {
  const response = await fetch(`https://saathiiapp.com/block/check/${userId}`, {
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    }
  });
  return response.json();
};
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
  -d '{
    "blocked_id": 123
  }'
```

**Get Blocked Users:**
```bash
curl -X GET 'https://saathiiapp.com/blocked?page=1&per_page=20' \
  -H 'Authorization: Bearer <access_token>'
```

**Check Block Status:**
```bash
curl -X GET 'https://saathiiapp.com/block/check/123' \
  -H 'Authorization: Bearer <access_token>'
```

## Best Practices

### Blocking Management

1. **Check Status**: Always check block status before showing user interactions
2. **Confirmation**: Ask for confirmation before blocking users
3. **Reason Tracking**: Encourage users to provide reasons for blocking
4. **Regular Review**: Allow users to review and manage blocked users

### User Experience

1. **Clear Indicators**: Show clear visual indicators for blocked users
2. **Easy Access**: Make blocking/unblocking easily accessible
3. **Feedback**: Provide clear feedback for blocking actions
4. **Privacy**: Respect user privacy in blocked user lists

### Safety

1. **Immediate Effect**: Blocking should take effect immediately
2. **No Contact**: Blocked users should not be able to contact you
3. **Feed Filtering**: Blocked users should not appear in feeds
4. **Call Prevention**: Blocked users should not be able to call you

## Next Steps

- Learn about [Favorites API](./favorites) for managing favorite users
- Explore [User Management API](./user-management) for profile management
- Check out [Feed System API](./feed-system) for user discovery
