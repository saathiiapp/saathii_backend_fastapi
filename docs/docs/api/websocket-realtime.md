---
sidebar_position: 9
title: WebSocket Real-time
description: Real-time WebSocket connections and live updates
---

# WebSocket Real-time

The WebSocket API provides real-time bidirectional communication for live updates, presence tracking, and instant notifications.

## Overview

- **Real-time Connection**: Persistent WebSocket connections
- **Live Updates**: Instant status and data updates
- **Presence Tracking**: Real-time user presence changes
- **Event Broadcasting**: System-wide event notifications

## WebSocket Endpoints

### Feed Updates

Real-time feed updates for listener discovery.

**Endpoint:** `WS /ws/feed`

**Connection:** `wss://your-api-domain.com/ws/feed?token=<access_token>`

**Message Types:**
- `listener_online` - User comes online
- `listener_offline` - User goes offline
- `listener_busy` - User becomes busy
- `listener_available` - User becomes available

**Example Message:**
```json
{
  "type": "listener_online",
  "data": {
    "user_id": 123,
    "username": "jane_smith",
    "is_online": true,
    "is_busy": false,
    "last_seen": "2024-01-15T10:30:00Z"
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### Presence Updates

Real-time presence status changes.

**Endpoint:** `WS /ws/presence`

**Connection:** `wss://your-api-domain.com/ws/presence?token=<access_token>`

**Message Types:**
- `presence_update` - User presence changed
- `status_change` - User status changed

**Example Message:**
```json
{
  "type": "presence_update",
  "data": {
    "user_id": 123,
    "is_online": true,
    "is_busy": false,
    "last_seen": "2024-01-15T10:30:00Z"
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### Call Updates

Real-time call status updates.

**Connection:** `wss://your-api-domain.com/ws/calls?token=<access_token>`

**Message Types:**
- `call_started` - New call initiated
- `call_ended` - Call completed
- `call_billing` - Call billing update

**Example Message:**
```json
{
  "type": "call_started",
  "data": {
    "call_id": 456,
    "user_id": 123,
    "listener_id": 789,
    "call_type": "audio",
    "status": "ongoing"
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### Notifications

Real-time system notifications.

**Connection:** `wss://your-api-domain.com/ws/notifications?token=<access_token>`

**Message Types:**
- `favorite_added` - Added to favorites
- `favorite_removed` - Removed from favorites
- `user_blocked` - User blocked you
- `user_unblocked` - User unblocked you

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

## Connection Management

### Authentication

All WebSocket connections require authentication via token:

```
wss://your-api-domain.com/ws/feed?token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### Connection Lifecycle

1. **Connect**: Establish WebSocket connection with token
2. **Authenticate**: Server validates token and user permissions
3. **Subscribe**: Client receives relevant real-time updates
4. **Heartbeat**: Send periodic ping to keep connection alive
5. **Reconnect**: Handle disconnections gracefully

### Error Handling

**Connection Errors:**
```json
{
  "type": "error",
  "data": {
    "code": "AUTH_FAILED",
    "message": "Invalid or expired token"
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

**Common Error Codes:**
- `AUTH_FAILED` - Invalid or expired token
- `PERMISSION_DENIED` - Insufficient permissions
- `RATE_LIMITED` - Too many requests
- `CONNECTION_LIMIT` - Maximum connections reached

## Message Format

### Standard Message Structure

```json
{
  "type": "message_type",
  "data": {
    // Message-specific data
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### Heartbeat Messages

**Client to Server:**
```json
{
  "type": "ping",
  "data": {},
  "timestamp": "2024-01-15T10:30:00Z"
}
```

**Server to Client:**
```json
{
  "type": "pong",
  "data": {},
  "timestamp": "2024-01-15T10:30:00Z"
}
```

## Integration Examples

### JavaScript/WebSocket

```javascript
class WebSocketManager {
  constructor(token) {
    this.token = token;
    this.ws = null;
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 5;
  }

  connect(endpoint) {
    const wsUrl = `wss://your-api-domain.com/ws/${endpoint}?token=${this.token}`;
    this.ws = new WebSocket(wsUrl);

    this.ws.onopen = () => {
      console.log('WebSocket connected');
      this.reconnectAttempts = 0;
      this.startHeartbeat();
    };

    this.ws.onmessage = (event) => {
      const message = JSON.parse(event.data);
      this.handleMessage(message);
    };

    this.ws.onclose = (event) => {
      console.log('WebSocket disconnected:', event.code);
      this.handleReconnect();
    };

    this.ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };
  }

  handleMessage(message) {
    switch (message.type) {
      case 'presence_update':
        this.onPresenceUpdate(message.data);
        break;
      case 'call_started':
        this.onCallStarted(message.data);
        break;
      case 'favorite_added':
        this.onFavoriteAdded(message.data);
        break;
      default:
        console.log('Unknown message type:', message.type);
    }
  }

  startHeartbeat() {
    setInterval(() => {
      if (this.ws && this.ws.readyState === WebSocket.OPEN) {
        this.ws.send(JSON.stringify({
          type: 'ping',
          data: {},
          timestamp: new Date().toISOString()
        }));
      }
    }, 30000); // Send every 30 seconds
  }

  handleReconnect() {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      const delay = Math.pow(2, this.reconnectAttempts) * 1000;
      
      setTimeout(() => {
        this.connect('feed'); // Reconnect to feed endpoint
      }, delay);
    }
  }

  disconnect() {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }
}

// Usage
const wsManager = new WebSocketManager('your-access-token');
wsManager.connect('feed');
```

### React Native WebSocket

```typescript
import { useEffect, useRef } from 'react';

interface WebSocketMessage {
  type: string;
  data: any;
  timestamp: string;
}

const useWebSocket = (token: string, endpoint: string) => {
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    const connect = () => {
      const wsUrl = `wss://your-api-domain.com/ws/${endpoint}?token=${token}`;
      wsRef.current = new WebSocket(wsUrl);

      wsRef.current.onopen = () => {
        console.log('WebSocket connected');
        startHeartbeat();
      };

      wsRef.current.onmessage = (event) => {
        const message: WebSocketMessage = JSON.parse(event.data);
        handleMessage(message);
      };

      wsRef.current.onclose = (event) => {
        console.log('WebSocket disconnected:', event.code);
        scheduleReconnect();
      };

      wsRef.current.onerror = (error) => {
        console.error('WebSocket error:', error);
      };
    };

    const startHeartbeat = () => {
      setInterval(() => {
        if (wsRef.current?.readyState === WebSocket.OPEN) {
          wsRef.current.send(JSON.stringify({
            type: 'ping',
            data: {},
            timestamp: new Date().toISOString()
          }));
        }
      }, 30000);
    };

    const handleMessage = (message: WebSocketMessage) => {
      // Handle different message types
      switch (message.type) {
        case 'presence_update':
          // Update presence in your app state
          break;
        case 'call_started':
          // Handle call started
          break;
        default:
          console.log('Unknown message type:', message.type);
      }
    };

    const scheduleReconnect = () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      
      reconnectTimeoutRef.current = setTimeout(() => {
        connect();
      }, 5000);
    };

    connect();

    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
    };
  }, [token, endpoint]);
};

export default useWebSocket;
```

## Best Practices

### Connection Management

1. **Authentication**: Always use valid access tokens
2. **Reconnection**: Implement exponential backoff for reconnection
3. **Heartbeat**: Send regular ping messages to keep connection alive
4. **Error Handling**: Handle all connection errors gracefully

### Performance

1. **Connection Pooling**: Reuse connections when possible
2. **Message Filtering**: Only process relevant message types
3. **Rate Limiting**: Respect server rate limits
4. **Memory Management**: Clean up unused connections

### Security

1. **Token Security**: Never expose tokens in client-side code
2. **HTTPS/WSS**: Always use secure connections
3. **Input Validation**: Validate all incoming messages
4. **Access Control**: Implement proper permission checks

## Next Steps

- Learn about [Presence & Status API](./presence-status) for user status management
- Explore [Feed System API](./feeds) for user discovery
- Check out [Call Management API](./call-management) for call operations
