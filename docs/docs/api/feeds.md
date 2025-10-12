---
sidebar_position: 5
title: Feeds API
description: User discovery and feed system
---

# Feeds API

The Feeds API provides user discovery functionality and feed management for finding and connecting with listeners.

## Overview

- **Listener Discovery**: Find and browse available listeners
- **Feed Filtering**: Filter listeners by various criteria
- **Feed Statistics**: Get insights about the feed system
- **Real-time Updates**: WebSocket support for live feed updates

## Endpoints

### Get Listeners Feed

Get paginated list of listeners with filtering options.

**Endpoint:** `GET /feed/listeners`

**Headers:**
```
Authorization: Bearer <access_token>
```

**Query Parameters:**
- `page`: Page number (default: 1)
- `per_page`: Items per page (default: 20, max: 100)
- `online_only`: Show only online listeners (default: false)
- `sex`: Filter by gender - "male", "female", "other" (optional)
- `min_rating`: Minimum rating filter (default: 0.0)
- `max_rating`: Maximum rating filter (default: 5.0)
- `interests`: Comma-separated list of interests to filter by (optional)
- `language`: Filter by preferred language (optional)
- `sort_by`: Sort order - "rating", "online", "recent" (default: "rating")
- `sort_order`: Sort direction - "asc", "desc" (default: "desc")

**Response:**
```json
{
  "listeners": [
    {
      "user_id": 123,
      "username": "alice_listener",
      "sex": "female",
      "bio": "Professional listener with 5 years experience...",
      "interests": ["music", "tech", "art"],
      "profile_image_url": "https://example.com/profile.jpg",
      "preferred_language": "en",
      "rating": 4.8,
      "is_online": true,
      "is_busy": false,
      "last_seen": "2024-01-15T10:30:00Z",
      "call_count": 150,
      "avg_call_duration": 25.5
    }
  ],
  "filters": {
    "online_only": false,
    "sex": null,
    "min_rating": 0.0,
    "max_rating": 5.0,
    "interests": [],
    "language": null,
    "sort_by": "rating",
    "sort_order": "desc"
  },
  "pagination": {
    "page": 1,
    "per_page": 20,
    "total": 150,
    "has_next": true,
    "has_previous": false
  }
}
```

**Fields:**
- `user_id`: Listener's user ID
- `username`: Listener's username
- `sex`: Listener's gender
- `bio`: Listener's biography
- `interests`: Array of listener's interests
- `profile_image_url`: Profile image URL
- `preferred_language`: Language preference
- `rating`: Listener's rating (0.0-5.0)
- `is_online`: Current online status
- `is_busy`: Current busy status
- `last_seen`: Last seen timestamp
- `call_count`: Total number of calls
- `avg_call_duration`: Average call duration in minutes

### Get Feed Statistics

Get statistics about the feed system and available listeners.

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
  "busy_listeners": 12,
  "available_listeners": 33,
  "average_rating": 4.2,
  "top_interests": [
    {
      "interest": "music",
      "count": 45
    },
    {
      "interest": "tech",
      "count": 38
    },
    {
      "interest": "art",
      "count": 32
    }
  ],
  "gender_distribution": {
    "female": 85,
    "male": 60,
    "other": 5
  },
  "language_distribution": {
    "en": 120,
    "es": 20,
    "fr": 10
  },
  "last_updated": "2024-01-15T10:30:00Z"
}
```

**Fields:**
- `total_listeners`: Total number of listeners
- `online_listeners`: Number of online listeners
- `busy_listeners`: Number of busy listeners
- `available_listeners`: Number of available listeners
- `average_rating`: Average rating across all listeners
- `top_interests`: Most popular interests
- `gender_distribution`: Distribution by gender
- `language_distribution`: Distribution by language
- `last_updated`: When statistics were last updated

## Filtering Options

### Gender Filter
- **Values**: "male", "female", "other"
- **Usage**: Filter listeners by gender
- **Example**: `?sex=female`

### Rating Filter
- **Values**: 0.0 to 5.0
- **Usage**: Filter by minimum and maximum rating
- **Example**: `?min_rating=4.0&max_rating=5.0`

### Interests Filter
- **Values**: Comma-separated list of interests
- **Usage**: Filter listeners who have specific interests
- **Example**: `?interests=music,tech`

### Language Filter
- **Values**: Language codes (en, es, fr, etc.)
- **Usage**: Filter by preferred language
- **Example**: `?language=en`

### Online Status Filter
- **Values**: true/false
- **Usage**: Show only online listeners
- **Example**: `?online_only=true`

### Sorting Options
- **rating**: Sort by listener rating
- **online**: Sort by online status
- **recent**: Sort by last seen time
- **Order**: "asc" or "desc"

## Error Handling

### Common Error Responses

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

**Invalid Gender (400):**
```json
{
  "detail": "Invalid gender. Must be 'male', 'female', or 'other'"
}
```

**Invalid Rating (400):**
```json
{
  "detail": "Rating must be between 0.0 and 5.0"
}
```

**Invalid Sort (400):**
```json
{
  "detail": "Invalid sort option. Must be 'rating', 'online', or 'recent'"
}
```

## Integration Examples

### React Native Integration

```typescript
// Get listeners feed
const getListenersFeed = async (token: string, filters: any = {}) => {
  const params = new URLSearchParams({
    page: filters.page?.toString() || '1',
    per_page: filters.per_page?.toString() || '20',
    online_only: filters.online_only?.toString() || 'false',
    sort_by: filters.sort_by || 'rating',
    sort_order: filters.sort_order || 'desc'
  });
  
  if (filters.sex) params.append('sex', filters.sex);
  if (filters.min_rating) params.append('min_rating', filters.min_rating.toString());
  if (filters.max_rating) params.append('max_rating', filters.max_rating.toString());
  if (filters.interests) params.append('interests', filters.interests.join(','));
  if (filters.language) params.append('language', filters.language);
  
  const response = await fetch(`https://saathiiapp.com/feed/listeners?${params}`, {
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    }
  });
  return response.json();
};

// Get feed statistics
const getFeedStats = async (token: string) => {
  const response = await fetch('https://saathiiapp.com/feed/stats', {
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    }
  });
  return response.json();
};
```

### cURL Examples

**Get Listeners Feed:**
```bash
curl -X GET 'https://saathiiapp.com/feed/listeners?page=1&per_page=20&online_only=true' \
  -H 'Authorization: Bearer <access_token>'
```

**Get Feed with Filters:**
```bash
curl -X GET 'https://saathiiapp.com/feed/listeners?sex=female&min_rating=4.0&interests=music,tech' \
  -H 'Authorization: Bearer <access_token>'
```

**Get Feed Statistics:**
```bash
curl -X GET 'https://saathiiapp.com/feed/stats' \
  -H 'Authorization: Bearer <access_token>'
```

## WebSocket Integration

### Real-time Feed Updates

Connect to the WebSocket endpoint for real-time feed updates:

```javascript
const ws = new WebSocket('wss://saathiiapp.com/ws/feed?token=<access_token>');

ws.onopen = () => {
  console.log('Connected to feed updates');
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  if (data.type === 'listener_online') {
    // Handle listener coming online
  } else if (data.type === 'listener_offline') {
    // Handle listener going offline
  }
};
```

## Best Practices

### Feed Management

1. **Pagination**: Always use pagination for large feeds
2. **Filtering**: Use appropriate filters to reduce data load
3. **Caching**: Cache feed data locally for better performance
4. **Real-time Updates**: Use WebSocket for live updates

### User Experience

1. **Loading States**: Show loading indicators during data fetch
2. **Empty States**: Handle empty feeds gracefully
3. **Filter UI**: Provide intuitive filter controls
4. **Refresh**: Implement pull-to-refresh functionality

### Performance

1. **Lazy Loading**: Load more items as needed
2. **Image Optimization**: Optimize profile images
3. **Data Caching**: Cache frequently accessed data
4. **Efficient Filtering**: Use server-side filtering

## Next Steps

- Learn about [Favorites API](./favorites) for managing favorite users
- Explore [Call Management API](./call-management) for call operations
- Check out [User Management API](./user-management) for profile management
