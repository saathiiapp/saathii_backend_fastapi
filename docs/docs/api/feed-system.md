---
sidebar_position: 4
title: Feed System API
description: User discovery and feed management with real-time updates
---

# Feed System API

The Feed System API provides user discovery functionality with advanced filtering, pagination, and real-time updates for finding and connecting with other users.

## Overview

- **User Discovery**: Find users based on various criteria
- **Advanced Filtering**: Filter by online status, availability, language, interests
- **Real-time Updates**: Live feed updates via WebSocket
- **Pagination**: Efficient pagination for large user bases
- **Statistics**: Feed statistics and analytics

## Feed Types

### Listeners Feed

Primary feed for discovering listeners who can provide services.

**Features:**
- Filter by online status
- Filter by availability (online + not busy)
- Filter by language preference
- Filter by interests
- Filter by minimum rating
- Pagination support

## Endpoints

### Get Listeners Feed

Retrieve a paginated list of listeners with filtering options.

**Endpoint:** `GET /feed/listeners`

**Headers:**
```
Authorization: Bearer <access_token>
```

**Query Parameters:**

| Parameter | Type | Description | Default |
|-----------|------|-------------|---------|
| `online_only` | boolean | Show only online users | false |
| `available_only` | boolean | Show only available users (online + not busy) | false |
| `language` | string | Filter by preferred language | null |
| `interests` | string | Comma-separated interests filter | null |
| `min_rating` | number | Minimum rating filter | null |
| `page` | integer | Page number (1-based) | 1 |
| `per_page` | integer | Items per page (max 100) | 20 |

**Example Request:**
```
GET /feed/listeners?online_only=true&available_only=true&language=en&interests=music,tech&min_rating=4.0&page=1&per_page=20
```

**Response:**
```json
{
  "listeners": [
    {
      "user_id": 123,
      "username": "john_doe",
      "sex": "male",
      "bio": "Professional listener with 5 years experience...",
      "interests": ["music", "tech", "art"],
      "profile_image_url": "https://example.com/profile.jpg",
      "preferred_language": "en",
      "rating": 4.5,
      "country": "US",
      "roles": ["listener"],
      "is_online": true,
      "last_seen": "2024-01-15T10:30:00Z",
      "is_busy": false,
      "busy_until": null,
      "is_available": true
    },
    {
      "user_id": 456,
      "username": "jane_smith",
      "sex": "female",
      "bio": "Experienced listener specializing in music...",
      "interests": ["music", "art"],
      "profile_image_url": "https://example.com/jane.jpg",
      "preferred_language": "en",
      "rating": 4.8,
      "country": "CA",
      "roles": ["listener"],
      "is_online": true,
      "last_seen": "2024-01-15T10:25:00Z",
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

**Response Fields:**
- `listeners`: Array of listener objects with full profile and status info
- `total_count`: Total number of listeners matching filters
- `online_count`: Number of online listeners
- `available_count`: Number of available listeners (online + not busy)
- `page`: Current page number
- `per_page`: Items per page
- `has_next`: Whether there are more pages
- `has_previous`: Whether there are previous pages

### Get Feed Statistics

Get overall feed statistics and counts.

**Endpoint:** `GET /feed/stats`

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
  "busy_listeners": 7,
  "offline_listeners": 105
}
```

**Statistics:**
- `total_listeners`: Total number of listeners in the system
- `online_listeners`: Number of currently online listeners
- `available_listeners`: Number of available listeners (online + not busy)
- `busy_listeners`: Number of busy listeners (online but occupied)
- `offline_listeners`: Number of offline listeners

## Filtering Options

### Online Status Filtering

**Online Only:**
```
GET /feed/listeners?online_only=true
```
Shows only users who are currently online.

**Available Only:**
```
GET /feed/listeners?available_only=true
```
Shows only users who are online and not busy (available for calls).

### Language Filtering

**Filter by Language:**
```
GET /feed/listeners?language=en
```
Shows only users with the specified language preference.

**Supported Languages:**
- `en` - English
- `es` - Spanish
- `fr` - French
- `de` - German
- `it` - Italian
- `pt` - Portuguese
- `ru` - Russian
- `ja` - Japanese
- `ko` - Korean
- `zh` - Chinese

### Interest Filtering

**Filter by Interests:**
```
GET /feed/listeners?interests=music,tech,art
```
Shows only users who have any of the specified interests.

**Interest Matching:**
- Case-insensitive matching
- Partial matching (e.g., "mus" matches "music")
- Multiple interests are OR-ed together

### Rating Filtering

**Filter by Minimum Rating:**
```
GET /feed/listeners?min_rating=4.0
```
Shows only users with a rating of 4.0 or higher.

**Rating Range:**
- Minimum: 0.0
- Maximum: 5.0
- Precision: 1 decimal place

### Combined Filtering

**Complex Filter Example:**
```
GET /feed/listeners?online_only=true&available_only=true&language=en&interests=music,tech&min_rating=4.0&page=1&per_page=10
```

This query finds:
- Online and available listeners
- English language preference
- Interested in music or tech
- Rating 4.0 or higher
- First page with 10 results

## Pagination

### Basic Pagination

**Page Navigation:**
```
GET /feed/listeners?page=1&per_page=20  # First page
GET /feed/listeners?page=2&per_page=20  # Second page
GET /feed/listeners?page=3&per_page=20  # Third page
```

### Pagination Limits

- **Minimum page**: 1
- **Maximum per_page**: 100
- **Default per_page**: 20
- **Page numbering**: 1-based (not 0-based)

### Pagination Response

```json
{
  "listeners": [...],
  "total_count": 150,
  "page": 2,
  "per_page": 20,
  "has_next": true,
  "has_previous": true
}
```

**Navigation Logic:**
- `has_next`: `page * per_page < total_count`
- `has_previous`: `page > 1`

## Real-time Updates

### WebSocket Integration

Feed updates are broadcast via WebSocket for real-time updates.

**WebSocket Endpoint:** `ws://localhost:8000/ws/feed?token=<access_token>`

**Message Types:**

**User Status Update:**
```json
{
  "type": "user_status_update",
  "user_id": 456,
  "status": {
    "user_id": 456,
    "username": "jane_smith",
    "profile_image_url": "https://...",
    "is_online": true,
    "last_seen": "2024-01-15T10:30:00Z",
    "is_busy": false,
    "busy_until": null,
    "is_available": true
  }
}
```

**Connection Established:**
```json
{
  "type": "connection_established",
  "message": "Connected to feed updates",
  "user_id": 123
}
```

### Real-time Feed Updates

When a user's status changes, the feed is automatically updated:

1. **User goes online**: Added to online feed
2. **User goes offline**: Removed from online feed
3. **User becomes busy**: Removed from available feed
4. **User becomes available**: Added to available feed

## Performance Optimization

### Caching

- **Redis Caching**: Feed results are cached for 30 seconds
- **User Status Caching**: User status cached for 5 minutes
- **Statistics Caching**: Statistics cached for 1 minute

### Database Optimization

- **Indexed Queries**: All filter fields are indexed
- **Query Optimization**: Efficient SQL queries with proper joins
- **Pagination**: Database-level pagination for large datasets

### Rate Limiting

- **Feed Requests**: 100 requests per minute per user
- **Statistics Requests**: 20 requests per minute per user
- **WebSocket Connections**: 5 concurrent connections per user

## Error Handling

### Common Error Responses

**Invalid Parameters (400):**
```json
{
  "detail": "Invalid query parameters"
}
```

**Rate Limit Exceeded (429):**
```json
{
  "detail": "Rate limit exceeded. Try again later."
}
```

**Unauthorized (401):**
```json
{
  "detail": "Could not validate credentials"
}
```

**Invalid Page (400):**
```json
{
  "detail": "Page number must be greater than 0"
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
// Get listeners feed
const getListenersFeed = async (token: string, filters: any) => {
  const params = new URLSearchParams();
  Object.entries(filters).forEach(([key, value]) => {
    if (value !== null && value !== undefined) {
      params.append(key, value.toString());
    }
  });

  const response = await fetch(`http://localhost:8000/feed/listeners?${params}`, {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });
  return response.json();
};

// Get feed statistics
const getFeedStats = async (token: string) => {
  const response = await fetch('http://localhost:8000/feed/stats', {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });
  return response.json();
};

// WebSocket integration
const useFeedWebSocket = (token: string) => {
  const [isConnected, setIsConnected] = useState(false);
  const [feedUpdates, setFeedUpdates] = useState([]);

  useEffect(() => {
    const ws = new WebSocket(`ws://localhost:8000/ws/feed?token=${token}`);
    
    ws.onopen = () => setIsConnected(true);
    ws.onclose = () => setIsConnected(false);
    
    ws.onmessage = (event) => {
      const message = JSON.parse(event.data);
      if (message.type === 'user_status_update') {
        setFeedUpdates(prev => [...prev, message]);
      }
    };

    return () => ws.close();
  }, [token]);

  return { isConnected, feedUpdates };
};
```

### cURL Examples

**Get Listeners Feed:**
```bash
curl -X GET 'http://localhost:8000/feed/listeners?online_only=true&available_only=true' \
  -H 'Authorization: Bearer <access_token>'
```

**Get Feed with Filters:**
```bash
curl -X GET 'http://localhost:8000/feed/listeners?language=en&interests=music,tech&min_rating=4.0&page=1&per_page=10' \
  -H 'Authorization: Bearer <access_token>'
```

**Get Feed Statistics:**
```bash
curl -X GET 'http://localhost:8000/feed/stats' \
  -H 'Authorization: Bearer <access_token>'
```

## Best Practices

### Feed Management

1. **Caching**: Cache feed results locally for better performance
2. **Pagination**: Implement proper pagination for large datasets
3. **Filtering**: Use appropriate filters to reduce data transfer
4. **Real-time Updates**: Implement WebSocket for live updates

### Performance

1. **Lazy Loading**: Load more items as user scrolls
2. **Debouncing**: Debounce filter changes to avoid excessive requests
3. **Error Handling**: Handle network errors gracefully
4. **Loading States**: Show loading indicators during requests

### User Experience

1. **Filter UI**: Provide intuitive filter controls
2. **Search**: Implement search functionality
3. **Sorting**: Allow users to sort by different criteria
4. **Refresh**: Provide pull-to-refresh functionality

## Next Steps

- Learn about [Call Management API](./call-management) for making calls
- Explore [WebSocket Real-time API](./websocket-realtime) for live updates
- Check out [Listener Verification API](./listener-verification) for verification process
