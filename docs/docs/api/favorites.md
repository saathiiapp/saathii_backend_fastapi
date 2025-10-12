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
- **Real-time Updates**: Live updates when favorites change
- **Filtering**: Filter favorites by availability and status

## Endpoints

### Add to Favorites

Add a listener to your favorites list.

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

Remove a listener from your favorites list.

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
- `404 Not Found` - Listener not found
- `409 Conflict` - Not in favorites (returns success with message)

### Get Favorites

Get a paginated list of your favorite listeners.

**Endpoint:** `GET /favorites`

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

Check if a specific listener is in your favorites.

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
  "message": "jane_smith is in favorites",
  "listener_id": 123,
  "is_favorited": true
}
```

**Error Responses:**
- `404 Not Found` - Listener not found

## Filtering Options

### Online Only Filter

Show only online favorites:
```
GET /favorites?online_only=true
```

### Available Only Filter

Show only available favorites (online and not busy):
```
GET /favorites?available_only=true
```

### Combined Filters

Combine multiple filters:
```
GET /favorites?online_only=true&page=1&per_page=20
```

## Real-time Updates

### WebSocket Integration

Favorites updates are broadcast in real-time via WebSocket:

**Connection:**
```
wss://your-api-domain.com/ws/feed?token=<access_token>
```

**Message Types:**
- `favorite_added` - User added you to favorites
- `favorite_removed` - User removed you from favorites

**Example Message:**
```json
{
  "type": "favorite_added",
  "data": {
    "user_id": 123,
    "username": "jane_smith",
    "action": "added_you_to_favorites"
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

## Error Handling

### Common Error Responses

**Cannot Favorite Self (400):**
```json
{
  "detail": "Cannot favorite yourself"
}
```

**Listener Not Found (404):**
```json
{
  "detail": "Listener not found"
}
```

**Already Favorited (200):**
```json
{
  "success": true,
  "message": "Already favorited jane_smith",
  "listener_id": 123,
  "is_favorited": true
}
```

**Not in Favorites (200):**
```json
{
  "success": true,
  "message": "jane_smith was not in favorites",
  "listener_id": 123,
  "is_favorited": false
}
```

## Integration Examples

### React Native Integration

```typescript
// services/FavoritesService.ts
import ApiService from './ApiService';

export interface FavoriteUser {
  user_id: number;
  username: string;
  sex: string;
  bio: string;
  interests: string[];
  profile_image_url: string;
  preferred_language: string;
  rating: number;
  country: string;
  is_online: boolean;
  last_seen: string;
  is_busy: boolean;
  wait_time: number | null;
  is_available: boolean;
  favorited_at: string;
}

export interface FavoritesResponse {
  favorites: FavoriteUser[];
  total_count: number;
  online_count: number;
  available_count: number;
  page: number;
  per_page: number;
  has_next: boolean;
  has_previous: boolean;
}

export interface FavoriteActionResponse {
  success: boolean;
  message: string;
  listener_id: number;
  is_favorited: boolean;
}

class FavoritesService {
  // Add to favorites
  async addFavorite(listenerId: number): Promise<FavoriteActionResponse> {
    return ApiService.post<FavoriteActionResponse>('/favorites/add', {
      listener_id: listenerId
    });
  }

  // Remove from favorites
  async removeFavorite(listenerId: number): Promise<FavoriteActionResponse> {
    return ApiService.delete<FavoriteActionResponse>('/favorites/remove', {
      listener_id: listenerId
    });
  }

  // Get favorites
  async getFavorites(filters: {
    page?: number;
    per_page?: number;
    online_only?: boolean;
    available_only?: boolean;
  } = {}): Promise<FavoritesResponse> {
    const params = new URLSearchParams();
    
    Object.entries(filters).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        params.append(key, value.toString());
      }
    });

    return ApiService.get<FavoritesResponse>(`/favorites?${params.toString()}`);
  }

  // Check favorite status
  async checkFavoriteStatus(listenerId: number): Promise<FavoriteActionResponse> {
    return ApiService.get<FavoriteActionResponse>(`/favorites/check/${listenerId}`);
  }
}

export default new FavoritesService();
```

### JavaScript/WebSocket Integration

```javascript
class FavoritesWebSocketManager {
  constructor(token) {
    this.token = token;
    this.ws = null;
  }

  connect() {
    const wsUrl = `wss://your-api-domain.com/ws/feed?token=${this.token}`;
    this.ws = new WebSocket(wsUrl);

    this.ws.onopen = () => {
      console.log('Favorites WebSocket connected');
    };

    this.ws.onmessage = (event) => {
      const message = JSON.parse(event.data);
      this.handleMessage(message);
    };

    this.ws.onclose = () => {
      console.log('Favorites WebSocket disconnected');
    };
  }

  handleMessage(message) {
    switch (message.type) {
      case 'favorite_added':
        this.onFavoriteAdded?.(message.data);
        break;
      case 'favorite_removed':
        this.onFavoriteRemoved?.(message.data);
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

**Add to Favorites:**
```bash
curl -X POST 'https://saathiiapp.com/favorites/add' \
  -H 'Authorization: Bearer <access_token>' \
  -H 'Content-Type: application/json' \
  -d '{"listener_id": 123}'
```

**Remove from Favorites:**
```bash
curl -X DELETE 'https://saathiiapp.com/favorites/remove' \
  -H 'Authorization: Bearer <access_token>' \
  -H 'Content-Type: application/json' \
  -d '{"listener_id": 123}'
```

**Get Favorites:**
```bash
curl -X GET 'https://saathiiapp.com/favorites?page=1&per_page=10&online_only=true' \
  -H 'Authorization: Bearer <access_token>'
```

**Check Favorite Status:**
```bash
curl -X GET 'https://saathiiapp.com/favorites/check/123' \
  -H 'Authorization: Bearer <access_token>'
```

## Best Practices

### User Experience

1. **Immediate Feedback**: Show immediate UI feedback when adding/removing favorites
2. **Error Handling**: Handle all error cases gracefully
3. **Loading States**: Show loading indicators during operations
4. **Confirmation**: Consider confirmation for removing favorites

### Performance

1. **Pagination**: Use pagination for large favorites lists
2. **Caching**: Cache favorites data locally
3. **Real-time Updates**: Use WebSocket for live updates
4. **Optimistic Updates**: Update UI optimistically for better UX

### Data Management

1. **State Synchronization**: Keep local state in sync with server
2. **Conflict Resolution**: Handle conflicts when favorites change
3. **Offline Support**: Consider offline functionality
4. **Data Validation**: Validate data before sending to API

## Next Steps

- Learn about [Blocking API](./blocking) for user blocking functionality
- Explore [Call Management API](./call-management) for making calls to favorites
- Check out [Feed System API](./feeds) for discovering new listeners
- Access the [WebSocket Integration](./websocket-realtime) for real-time updates