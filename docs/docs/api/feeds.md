---
sidebar_position: 4
title: Feed System API
description: User discovery and feed management for finding listeners
---

# Feed System API

The Feed System API provides comprehensive user discovery functionality, allowing users to find and connect with listeners based on various criteria including availability, interests, and preferences.

## Overview

- **User Discovery**: Find listeners based on multiple criteria
- **Real-time Status**: Live availability and presence information
- **Filtering Options**: Advanced filtering by interests, language, rating, and availability
- **Pagination**: Efficient pagination for large result sets
- **Statistics**: Counts and statistics

## Endpoints

### Get Listeners Feed

Get a paginated list of listeners with their details and real-time status.

**Endpoint:** `GET /customer/feed/listeners`

**Headers:**
```
Authorization: Bearer <access_token>
```

**Query Parameters:**

| Parameter | Type | Description | Default |
|-----------|------|-------------|---------|
| `online_only` | boolean | Show only online users | false |
| `available_only` | boolean | Show only available users (online and not busy) | false |
| `language` | string | Filter by preferred language | null |
| `interests` | string | Comma-separated interests to filter by | null |
| `min_rating` | integer | Minimum rating filter | null |
| `page` | integer | Page number (1-based) | 1 |
| `per_page` | integer | Items per page (max 100) | 20 |

**Example Request:**
```
GET /feed/listeners?online_only=true&interests=music,tech&page=1&per_page=10
```

**Response:**
```json
{
  "listeners": [
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
      "roles": ["listener"],
      "is_online": true,
      "last_seen": "2024-01-15T10:30:00Z",
      "is_busy": false,
      "wait_time": null,
      "is_available": true
    }
  ],
  "total_count": 150,
  "online_count": 45,
  "available_count": 38,
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
- `roles`: Array of user roles
- `is_online`: Current online status
- `last_seen`: Last activity timestamp
- `is_busy`: Whether user is currently busy (in a call)
- `wait_time`: Expected call duration in minutes (if on call)
- `is_available`: True if online and not busy

### Get Feed Statistics

Get statistics about listeners in the feed.

**Endpoint:** `GET /both/feed/stats`

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response:**
```json
{
  "total_listeners": 150,
  "online_listeners": 45,
  "available_listeners": 38,
  "busy_listeners": 7
}
```

**Field Descriptions:**
- `total_listeners`: Total number of listeners (excluding current user)
- `online_listeners`: Number of currently online listeners
- `available_listeners`: Number of available listeners (online and not busy)
- `busy_listeners`: Number of busy listeners (online but in calls)

## Filtering Options

### Online Only Filter

Show only users who are currently online:
```
GET /feed/listeners?online_only=true
```

### Available Only Filter

Show only users who are online and not busy (available for calls):
```
GET /feed/listeners?available_only=true
```

### Language Filter

Filter by preferred language:
```
GET /feed/listeners?language=en
```

### Interests Filter

Filter by interests (comma-separated):
```
GET /feed/listeners?interests=music,tech,art
```

### Rating Filter

Filter by minimum rating:
```
GET /feed/listeners?min_rating=4
```

### Combined Filters

Combine multiple filters:
```
GET /feed/listeners?online_only=true&interests=music&min_rating=4&page=1&per_page=20
```

## Sorting and Ordering

The feed is automatically sorted by:
1. **Online Status**: Online users appear first
2. **Availability**: Available users (not busy) appear before busy users
3. **Rating**: Higher rated users appear first
4. **Recent Activity**: More recently active users appear first

## Error Handling

### Common Error Responses

**Invalid Parameters (400):**
```json
{
  "detail": "Invalid user IDs format"
}
```

**Too Many Users (400):**
```json
{
  "detail": "Too many user IDs requested"
}
```

**Unauthorized (401):**
```json
{
  "detail": "Invalid or expired token"
}
```

## Integration Examples

### React Native Integration

```typescript
// services/FeedService.ts
import ApiService from './ApiService';

export interface ListenerFeedItem {
  user_id: number;
  username: string;
  sex: string;
  bio: string;
  interests: string[];
  profile_image_url: string;
  preferred_language: string;
  rating: number;
  country: string;
  roles: string[];
  is_online: boolean;
  last_seen: string;
  is_busy: boolean;
  wait_time: number | null;
  is_available: boolean;
}

export interface FeedResponse {
  listeners: ListenerFeedItem[];
  total_count: number;
  online_count: number;
  available_count: number;
  page: number;
  per_page: number;
  has_next: boolean;
  has_previous: boolean;
}

export interface FeedStats {
  total_listeners: number;
  online_listeners: number;
  available_listeners: number;
  busy_listeners: number;
}

class FeedService {
  // Get listeners feed
  async getListenersFeed(filters: {
    online_only?: boolean;
    available_only?: boolean;
    language?: string;
    interests?: string;
    min_rating?: number;
    page?: number;
    per_page?: number;
  } = {}): Promise<FeedResponse> {
    const params = new URLSearchParams();
    
    Object.entries(filters).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        params.append(key, value.toString());
      }
    });

    return ApiService.get<FeedResponse>(`/feed/listeners?${params.toString()}`);
  }

  // Get feed statistics
  async getFeedStats(): Promise<FeedStats> {
    return ApiService.get<FeedStats>('/feed/stats');
  }
}

export default new FeedService();
```

### JavaScript/WebSocket Integration

```javascript
class FeedWebSocketManager {
  constructor(token) {
    this.token = token;
    this.ws = null;
    this.listeners = new Map();
  }

  connect() {
    const wsUrl = `wss://your-api-domain.com/ws/feed?token=${this.token}`;
    this.ws = new WebSocket(wsUrl);

    this.ws.onopen = () => {
      console.log('Feed WebSocket connected');
    };

    this.ws.onmessage = (event) => {
      const message = JSON.parse(event.data);
      this.handleMessage(message);
    };

    this.ws.onclose = () => {
      console.log('Feed WebSocket disconnected');
      // Implement reconnection logic
    };
  }

  handleMessage(message) {
    switch (message.type) {
      case 'user_status_update':
        this.updateListenerStatus(message.user_id, message.status);
        break;
      case 'listener_online':
        this.addListener(message.data);
        break;
      case 'listener_offline':
        this.removeListener(message.data.user_id);
        break;
      default:
        console.log('Unknown message type:', message.type);
    }
  }

  updateListenerStatus(userId, status) {
    // Update listener status in your app state
    this.listeners.set(userId, status);
    // Trigger UI update
    this.onStatusUpdate?.(userId, status);
  }

  addListener(listener) {
    this.listeners.set(listener.user_id, listener);
    this.onListenerAdded?.(listener);
  }

  removeListener(userId) {
    this.listeners.delete(userId);
    this.onListenerRemoved?.(userId);
  }

  disconnect() {
    if (this.ws) {
      this.ws.close();
    }
  }
}
```

### cURL Examples

**Get Listeners Feed:**
```bash
curl -X GET 'https://saathiiapp.com/feed/listeners?online_only=true&interests=music,tech&page=1&per_page=10' \
  -H 'Authorization: Bearer <access_token>'
```

**Get Feed Statistics:**
```bash
curl -X GET 'https://saathiiapp.com/feed/stats' \
  -H 'Authorization: Bearer <access_token>'
```

## Best Practices

### Performance Optimization

1. **Pagination**: Always use pagination to limit result sets
2. **Filtering**: Use appropriate filters to reduce data transfer
3. **Caching**: Cache feed data locally for better performance
4. **Real-time Updates**: Use WebSocket for live updates instead of polling

### User Experience

1. **Loading States**: Show loading indicators during feed requests
2. **Error Handling**: Implement proper error handling and retry logic
3. **Refresh**: Provide pull-to-refresh functionality
4. **Infinite Scroll**: Implement infinite scroll for better UX

### Real-time Updates

1. **WebSocket Connection**: Maintain persistent WebSocket connection
2. **Status Updates**: Update UI immediately when user status changes
3. **Connection Management**: Handle disconnections and reconnections gracefully
4. **Message Filtering**: Only process relevant message types

## Next Steps

- Learn about [Favorites API](./favorites) for managing favorite listeners
- Explore [Blocking API](./blocking) for user blocking functionality
- Check out [Call Management API](./call-management) for making calls