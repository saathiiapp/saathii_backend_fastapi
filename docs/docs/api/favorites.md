---
sidebar_position: 7
title: Favorites API
description: Manage favorite listeners and user preferences
---

# Favorites API

The Favorites API allows users to manage their favorite listeners and track their preferences.

## Overview

- **Favorite Management**: Add and remove favorite listeners
- **Favorites List**: Get paginated list of favorite users
- **Status Checking**: Check if a user is favorited
- **User Preferences**: Track user interaction patterns

## Endpoints

### Add Favorite

Add a listener to favorites list.

**Endpoint:** `POST /favorites/add`

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
- `listener_id`: ID of the listener to add to favorites (required)

**Response:**
```json
{
  "success": true,
  "message": "Listener added to favorites successfully",
  "listener_id": 123,
  "is_favorited": true
}
```

### Remove Favorite

Remove a listener from favorites list.

**Endpoint:** `DELETE /favorites/remove`

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
- `listener_id`: ID of the listener to remove from favorites (required)

**Response:**
```json
{
  "success": true,
  "message": "Listener removed from favorites successfully",
  "listener_id": 123,
  "is_favorited": false
}
```

### Get Favorites

Get paginated list of favorite listeners.

**Endpoint:** `GET /favorites`

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
  "favorites": [
    {
      "user_id": 123,
      "username": "alice_listener",
      "sex": "female",
      "bio": "Professional listener with 5 years experience...",
      "profile_image_url": "https://example.com/profile.jpg",
      "rating": 4.8,
      "is_online": true,
      "is_busy": false,
      "favorited_at": "2024-01-15T10:30:00Z"
    }
  ],
  "total_count": 5,
  "page": 1,
  "per_page": 20,
  "has_next": false,
  "has_previous": false
}
```

**Fields:**
- `user_id`: Listener's user ID
- `username`: Listener's username
- `sex`: Listener's gender
- `bio`: Listener's biography
- `profile_image_url`: Profile image URL
- `rating`: Listener's rating (0.0-5.0)
- `is_online`: Current online status
- `is_busy`: Current busy status
- `favorited_at`: When the listener was added to favorites

### Check Favorite Status

Check if a specific listener is in favorites.

**Endpoint:** `GET /favorites/check/{listener_id}`

**Headers:**
```
Authorization: Bearer <access_token>
```

**Path Parameters:**
- `listener_id`: ID of the listener to check

**Response:**
```json
{
  "success": true,
  "message": "Listener is in favorites",
  "listener_id": 123,
  "is_favorited": true
}
```

## Error Handling

### Common Error Responses

**Listener Not Found (404):**
```json
{
  "detail": "Listener not found"
}
```

**Already Favorited (400):**
```json
{
  "detail": "Listener is already in favorites"
}
```

**Not Favorited (400):**
```json
{
  "detail": "Listener is not in favorites"
}
```

**Invalid Page (400):**
```json
{
  "detail": "Page must be a positive integer"
}
```

**Invalid Per Page (400):**
```json
{
  "detail": "Per page must be between 1 and 100"
}
```

## Integration Examples

### React Native Integration

```typescript
// Add to favorites
const addFavorite = async (token: string, listenerId: number) => {
  const response = await fetch('https://saathiiapp.com/favorites/add', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ listener_id: listenerId })
  });
  return response.json();
};

// Remove from favorites
const removeFavorite = async (token: string, listenerId: number) => {
  const response = await fetch('https://saathiiapp.com/favorites/remove', {
    method: 'DELETE',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ listener_id: listenerId })
  });
  return response.json();
};

// Get favorites list
const getFavorites = async (token: string, page: number = 1) => {
  const response = await fetch(`https://saathiiapp.com/favorites?page=${page}&per_page=20`, {
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    }
  });
  return response.json();
};

// Check favorite status
const checkFavoriteStatus = async (token: string, listenerId: number) => {
  const response = await fetch(`https://saathiiapp.com/favorites/check/${listenerId}`, {
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    }
  });
  return response.json();
};
```

### cURL Examples

**Add Favorite:**
```bash
curl -X POST 'https://saathiiapp.com/favorites/add' \
  -H 'Authorization: Bearer <access_token>' \
  -H 'Content-Type: application/json' \
  -d '{
    "listener_id": 123
  }'
```

**Remove Favorite:**
```bash
curl -X DELETE 'https://saathiiapp.com/favorites/remove' \
  -H 'Authorization: Bearer <access_token>' \
  -H 'Content-Type: application/json' \
  -d '{
    "listener_id": 123
  }'
```

**Get Favorites:**
```bash
curl -X GET 'https://saathiiapp.com/favorites?page=1&per_page=20' \
  -H 'Authorization: Bearer <access_token>'
```

**Check Favorite Status:**
```bash
curl -X GET 'https://saathiiapp.com/favorites/check/123' \
  -H 'Authorization: Bearer <access_token>'
```

## Best Practices

### Favorites Management

1. **Check Status**: Always check favorite status before showing UI
2. **Optimistic Updates**: Update UI immediately, handle errors gracefully
3. **Pagination**: Use pagination for large favorites lists
4. **Caching**: Cache favorites list locally for better performance

### User Experience

1. **Visual Feedback**: Show clear visual indicators for favorite status
2. **Loading States**: Display loading indicators during operations
3. **Error Handling**: Show user-friendly error messages
4. **Confirmation**: Consider confirmation for remove actions

### Performance

1. **Lazy Loading**: Load favorites as needed
2. **Caching**: Cache favorite status for frequently accessed users
3. **Batch Operations**: Consider batch operations for multiple changes
4. **Real-time Updates**: Update UI when favorites change

## Next Steps

- Learn about [Blocking API](./blocking) for user blocking features
- Explore [Feed System API](./feed-system) for discovering users
- Check out [User Management API](./user-management) for profile management
