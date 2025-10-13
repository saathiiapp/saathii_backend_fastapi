---
sidebar_position: 6
title: Favorites API
description: Manage favorite listeners and user preferences
---

# Favorites API

The Favorites API allows users to manage their favorite listeners, providing quick access to preferred users and enhanced discovery features.

## Overview

- **Add/Remove Favorites**: Add or remove listeners from favorites
- **Favorites List**: Get paginated list of favorite listeners
- **Status Checking**: Check if a listener is favorited
- **Filtering**: Filter favorites by availability and status

## Endpoints

### Add to Favorites

Add a listener to your favorites list.

**Endpoint:** `POST /customer/favorites`

**Headers:**
```
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Request Body:**
```json
{
  "listener_id": 123
}
```

**Fields:**
- `listener_id`: ID of the listener to add to favorites

**Response:**
```json
{
  "success": true,
  "message": "Successfully added jane_smith to favorites",
  "listener_id": 123,
  "is_favorited": true
}
```

**Error Responses:**
- `400 Bad Request` - Cannot favorite yourself
- `404 Not Found` - Listener not found
- `409 Conflict` - Already favorited (returns success with message)

### Remove from Favorites

Note: There is no delete endpoint; removing favorites is not implemented in current routes.

### Get Favorites

Get a paginated list of your favorite listeners.

**Endpoint:** `GET /customer/favorites`

**Headers:**
```
Authorization: Bearer <access_token>
```

**Query Parameters:**

| Parameter | Type | Description | Default |
|-----------|------|-------------|---------|
| `page` | integer | Page number (1-based) | 1 |
| `per_page` | integer | Items per page (max 100) | 20 |
| `online_only` | boolean | Show only online favorites | false |
| `available_only` | boolean | Show only available favorites (online and not busy) | false |

**Example Request:**
```
GET /favorites?page=1&per_page=10&online_only=true
```

**Response:**
```json
{
  "favorites": [
    {
      "user_id": 123,
      "username": "jane_smith",
      "sex": "female",
      "bio": "Professional listener with 5 years experience...",
      "interests": ["music", "tech", "art"],
      "profile_image_url": "https://example.com/profile.jpg",
      "preferred_language": "en",
      "rating": 4.8,
      "country": "US",
      "is_online": true,
      "last_seen": "2024-01-15T10:30:00Z",
      "is_busy": false,
      "wait_time": null,
      "is_available": true,
      "favorited_at": "2024-01-15T09:00:00Z"
    }
  ],
  "total_count": 25,
  "online_count": 8,
  "available_count": 6,
  "page": 1,
  "per_page": 10,
  "has_next": true,
  "has_previous": false
}
```

**Field Descriptions:**
- `user_id`: Unique user identifier
- `username`: User's display name
- `sex`: Gender ("male", "female")
- `bio`: User biography/description
- `interests`: Array of interest tags
- `profile_image_url`: Profile image URL
- `preferred_language`: Language preference
- `rating`: User rating (0.0-5.0)
- `country`: Country code
- `is_online`: Current online status
- `last_seen`: Last activity timestamp
- `is_busy`: Whether user is currently busy (in a call)
- `wait_time`: Expected call duration in minutes (if on call)
- `is_available`: True if online and not busy
- `favorited_at`: When the user was added to favorites

### Check Favorite Status

Note: There is no explicit "check" endpoint; clients should use `GET /customer/favorites` and infer.

## Best Practices

### User Experience

1. **Immediate Feedback**: Show immediate UI feedback when adding favorites
2. **Error Handling**: Handle all error cases gracefully
3. **Loading States**: Show loading indicators during operations
4. **Confirmation**: Consider confirmation for removing favorites

### Performance

1. **Pagination**: Use pagination for large favorites lists
2. **Caching**: Cache favorites data locally
3. **Optimistic Updates**: Update UI optimistically for better UX

### Data Management

1. **State Synchronization**: Keep local state in sync with server
2. **Conflict Resolution**: Handle conflicts when favorites change
3. **Offline Support**: Consider offline functionality
4. **Data Validation**: Validate data before sending to API