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

**Endpoint:** `POST /both/block`

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

**Endpoint:** `DELETE /both/block`

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

**Endpoint:** `GET /both/blocked`

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

Note: There is no explicit "check" endpoint; clients should use `GET /both/blocked` and filter locally if needed.

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
3. **Efficient Queries**: Optimize database queries for block checks