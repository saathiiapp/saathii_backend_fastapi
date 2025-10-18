---
sidebar_position: 6
title: Favorites API
description: Manage favorite listeners and user preferences
---

# Favorites API

The Favorites API allows users to manage their favorite listeners, providing quick access to preferred users and enhanced discovery features.

## Overview

- **Add Favorites**: Add listeners to favorites list
- **Remove Favorites**: Remove listeners from favorites list
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
- `400 Bad Request` - Cannot favorite yourself, Listener account is inactive, Listener account is not verified
- `401 Unauthorized` - Invalid or expired token, Access token required
- `403 Forbidden` - Access denied. Customer role required, User account is inactive
- `404 Not Found` - Listener not found

### Remove from Favorites

Remove a listener from your favorites list.

**Endpoint:** `DELETE /customer/favorites`

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
- `listener_id`: ID of the listener to remove from favorites

**Response:**
```json
{
  "success": true,
  "message": "Successfully removed jane_smith from favorites",
  "listener_id": 123,
  "is_favorited": false
}
```

**Error Responses:**
- `400 Bad Request` - Cannot unfavorite yourself, Listener account is inactive, Listener account is not verified
- `401 Unauthorized` - Invalid or expired token, Access token required
- `403 Forbidden` - Access denied. Customer role required, User account is inactive
- `404 Not Found` - Listener not found

**Note:** The endpoint is idempotent - calling it multiple times with the same listener_id will return success even if the listener was not in favorites.

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

**Example Request:**
```
GET /customer/favorites?page=1&per_page=10
```

**Note:** The API automatically filters to show only active and verified listeners. Inactive or unverified listeners are excluded from the results.

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

Note: There is no explicit "check" endpoint; clients should use `GET /customer/favorites` and infer the status from the returned list.

## Authentication & Authorization

All favorites endpoints require:

1. **Valid JWT Token**: Must be a valid access token in the Authorization header
2. **Customer Role**: Only users with the "customer" role can access favorites
3. **Active Status**: The customer account must be active
4. **Listener Validation**: When adding/removing favorites, the target listener must be:
   - Active (not deactivated)
   - Verified (approved by admin)

## Error Handling

The API uses standard HTTP status codes:

- **200 OK**: Successful operation
- **400 Bad Request**: Invalid request data or business logic violations
- **401 Unauthorized**: Invalid or missing authentication
- **403 Forbidden**: Insufficient permissions or inactive account
- **404 Not Found**: Resource not found

## Best Practices

### User Experience

1. **Immediate Feedback**: Show immediate UI feedback when adding/removing favorites
2. **Error Handling**: Handle all error cases gracefully with user-friendly messages
3. **Loading States**: Show loading indicators during operations
4. **Confirmation**: Consider confirmation dialogs for removing favorites
5. **Optimistic Updates**: Update UI immediately, then sync with server

### Performance

1. **Pagination**: Use pagination for large favorites lists
2. **Caching**: Cache favorites data locally
3. **Optimistic Updates**: Update UI optimistically for better UX

### Data Management

1. **State Synchronization**: Keep local state in sync with server
2. **Conflict Resolution**: Handle conflicts when favorites change
3. **Offline Support**: Consider offline functionality
4. **Data Validation**: Validate data before sending to API
5. **Idempotent Operations**: Both add and remove operations are safe to retry

## API Examples

### Complete Workflow

```bash
# 1. Add a listener to favorites
curl -X POST "https://api.example.com/customer/favorites" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"listener_id": 123}'

# 2. Get favorites list
curl -X GET "https://api.example.com/customer/favorites?page=1&per_page=20" \
  -H "Authorization: Bearer <token>"

# 3. Remove a listener from favorites
curl -X DELETE "https://api.example.com/customer/favorites" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"listener_id": 123}'
```