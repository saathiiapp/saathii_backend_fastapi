---
sidebar_position: 9
title: Badges API
description: Listener badges and current rates
---

# Badges API

The Badges API provides the current daily badge for listeners, which determines earning rates per minute.

## Endpoint

### Get Current Badge (Listener)

Get the authenticated listener's current badge for today.

**Endpoint:** `GET /listener/badge/current`

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response:**
```json
{
  "listener_id": 123,
  "username": "jane_smith",
  "current_badge": "Basic",
  "audio_rate_per_minute": 1,
  "video_rate_per_minute": 6,
  "assigned_date": "2024-01-15",
  "assigned_at": "2024-01-15T00:00:00Z"
}
```

**Notes:**
- Only users with the listener role can fetch a badge.
- Rates are in rupees per minute and can vary by badge.

## Integration Example

```typescript
// Get current badge
const getCurrentBadge = async (token: string) => {
  const response = await fetch('https://saathiiapp.com/listener/badge/current', {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });
  return response.json();
};
```


