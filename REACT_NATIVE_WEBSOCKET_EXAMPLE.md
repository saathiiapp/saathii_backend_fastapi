# React Native WebSocket Integration for Real-time Feed Updates

This guide shows how to integrate the real-time WebSocket system with your React Native app to receive live status updates on the feed page.

## WebSocket Endpoints

### Feed Updates WebSocket
- **URL**: `ws://localhost:8000/ws/feed?token=<access_token>`
- **Purpose**: Receive real-time updates for the feed page

### Presence Updates WebSocket  
- **URL**: `ws://localhost:8000/ws/presence?token=<access_token>`
- **Purpose**: Receive real-time presence updates

## React Native Implementation

### 1. Install Dependencies

```bash
npm install @react-native-async-storage/async-storage
# For Expo
expo install @react-native-async-storage/async-storage
```

### 2. WebSocket Hook

```typescript
// hooks/useWebSocket.ts
import { useEffect, useRef, useState } from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';

interface WebSocketMessage {
  type: string;
  user_id?: number;
  status?: any;
  message?: string;
  timestamp?: string;
}

interface UseWebSocketProps {
  url: string;
  onMessage?: (message: WebSocketMessage) => void;
  onConnect?: () => void;
  onDisconnect?: () => void;
  reconnectInterval?: number;
}

export const useWebSocket = ({
  url,
  onMessage,
  onConnect,
  onDisconnect,
  reconnectInterval = 5000
}: UseWebSocketProps) => {
  const [isConnected, setIsConnected] = useState(false);
  const [connectionError, setConnectionError] = useState<string | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  const connect = async () => {
    try {
      // Get access token from storage
      const token = await AsyncStorage.getItem('access_token');
      if (!token) {
        setConnectionError('No access token found');
        return;
      }

      const wsUrl = `${url}?token=${token}`;
      const ws = new WebSocket(wsUrl);
      
      ws.onopen = () => {
        console.log('WebSocket connected');
        setIsConnected(true);
        setConnectionError(null);
        onConnect?.();
      };

      ws.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data);
          console.log('WebSocket message received:', message);
          onMessage?.(message);
        } catch (error) {
          console.error('Error parsing WebSocket message:', error);
        }
      };

      ws.onclose = (event) => {
        console.log('WebSocket disconnected:', event.code, event.reason);
        setIsConnected(false);
        onDisconnect?.();
        
        // Attempt to reconnect if not a clean close
        if (event.code !== 1000) {
          reconnectTimeoutRef.current = setTimeout(() => {
            console.log('Attempting to reconnect...');
            connect();
          }, reconnectInterval);
        }
      };

      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        setConnectionError('WebSocket connection error');
      };

      wsRef.current = ws;
    } catch (error) {
      console.error('Error connecting to WebSocket:', error);
      setConnectionError('Failed to connect to WebSocket');
    }
  };

  const disconnect = () => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }
    if (wsRef.current) {
      wsRef.current.close(1000, 'User disconnected');
      wsRef.current = null;
    }
    setIsConnected(false);
  };

  const sendMessage = (message: any) => {
    if (wsRef.current && isConnected) {
      wsRef.current.send(JSON.stringify(message));
    }
  };

  const ping = () => {
    sendMessage({
      type: 'ping',
      timestamp: new Date().toISOString()
    });
  };

  useEffect(() => {
    connect();
    
    return () => {
      disconnect();
    };
  }, []);

  return {
    isConnected,
    connectionError,
    connect,
    disconnect,
    sendMessage,
    ping
  };
};
```

### 3. Feed Page with Real-time Updates

```typescript
// screens/FeedScreen.tsx
import React, { useState, useEffect, useCallback } from 'react';
import { View, Text, FlatList, RefreshControl, Alert } from 'react-native';
import { useWebSocket } from '../hooks/useWebSocket';

interface Listener {
  user_id: number;
  username: string;
  profile_image_url?: string;
  is_online: boolean;
  is_available: boolean;
  is_busy: boolean;
  last_seen: string;
  rating?: number;
  bio?: string;
  interests?: string[];
}

interface FeedResponse {
  listeners: Listener[];
  total_count: number;
  online_count: number;
  available_count: number;
  page: number;
  per_page: number;
  has_next: boolean;
  has_previous: boolean;
}

const FeedScreen = () => {
  const [listeners, setListeners] = useState<Listener[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [feedStats, setFeedStats] = useState({
    total_count: 0,
    online_count: 0,
    available_count: 0
  });

  // WebSocket for real-time updates
  const { isConnected, connectionError, ping } = useWebSocket({
    url: 'ws://localhost:8000/ws/feed',
    onMessage: handleWebSocketMessage,
    onConnect: () => {
      console.log('Connected to feed updates');
      // Send ping to keep connection alive
      ping();
    },
    onDisconnect: () => {
      console.log('Disconnected from feed updates');
    }
  });

  // Handle incoming WebSocket messages
  function handleWebSocketMessage(message: any) {
    console.log('Received WebSocket message:', message);
    
    switch (message.type) {
      case 'user_status_update':
        handleUserStatusUpdate(message);
        break;
      case 'pong':
        // Connection is alive, schedule next ping
        setTimeout(ping, 30000); // Ping every 30 seconds
        break;
      case 'connection_established':
        console.log('Feed WebSocket connection established');
        break;
      default:
        console.log('Unknown message type:', message.type);
    }
  }

  // Handle user status updates
  const handleUserStatusUpdate = useCallback((message: any) => {
    const { user_id, status } = message;
    
    setListeners(prevListeners => {
      const updatedListeners = [...prevListeners];
      const index = updatedListeners.findIndex(listener => listener.user_id === user_id);
      
      if (index !== -1) {
        // Update existing listener
        updatedListeners[index] = {
          ...updatedListeners[index],
          ...status
        };
      } else if (status.is_online) {
        // Add new online listener to the top
        updatedListeners.unshift({
          user_id: status.user_id,
          username: status.username,
          profile_image_url: status.profile_image_url,
          is_online: status.is_online,
          is_available: status.is_available,
          is_busy: status.is_busy,
          last_seen: status.last_seen,
          rating: 0,
          bio: '',
          interests: []
        });
      }
      
      return updatedListeners;
    });

    // Update feed stats
    setFeedStats(prevStats => {
      const newStats = { ...prevStats };
      
      if (status.is_online) {
        newStats.online_count = Math.max(0, newStats.online_count + 1);
        if (status.is_available) {
          newStats.available_count = Math.max(0, newStats.available_count + 1);
        }
      } else {
        newStats.online_count = Math.max(0, newStats.online_count - 1);
        if (status.is_available) {
          newStats.available_count = Math.max(0, newStats.available_count - 1);
        }
      }
      
      return newStats;
    });
  }, []);

  // Load initial feed data
  const loadFeedData = async () => {
    try {
      const token = await AsyncStorage.getItem('access_token');
      const response = await fetch('http://localhost:8000/feed/listeners', {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });
      
      if (response.ok) {
        const data: FeedResponse = await response.json();
        setListeners(data.listeners);
        setFeedStats({
          total_count: data.total_count,
          online_count: data.online_count,
          available_count: data.available_count
        });
      } else {
        Alert.alert('Error', 'Failed to load feed data');
      }
    } catch (error) {
      console.error('Error loading feed data:', error);
      Alert.alert('Error', 'Network error');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  // Refresh feed data
  const onRefresh = () => {
    setRefreshing(true);
    loadFeedData();
  };

  useEffect(() => {
    loadFeedData();
  }, []);

  // Render listener item
  const renderListener = ({ item }: { item: Listener }) => (
    <View style={styles.listenerItem}>
      <View style={styles.listenerInfo}>
        <Text style={styles.username}>{item.username}</Text>
        <View style={styles.statusContainer}>
          <View style={[
            styles.statusDot, 
            { backgroundColor: item.is_available ? '#4CAF50' : item.is_online ? '#FF9800' : '#9E9E9E' }
          ]} />
          <Text style={styles.statusText}>
            {item.is_available ? 'Available' : item.is_online ? 'Online' : 'Offline'}
          </Text>
        </View>
        {item.bio && <Text style={styles.bio}>{item.bio}</Text>}
        {item.interests && item.interests.length > 0 && (
          <Text style={styles.interests}>
            Interests: {item.interests.join(', ')}
          </Text>
        )}
      </View>
    </View>
  );

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>Listeners Feed</Text>
        <View style={styles.statsContainer}>
          <Text style={styles.statsText}>
            {feedStats.available_count} available • {feedStats.online_count} online
          </Text>
          <View style={[
            styles.connectionStatus, 
            { backgroundColor: isConnected ? '#4CAF50' : '#F44336' }
          ]} />
        </View>
      </View>
      
      {connectionError && (
        <View style={styles.errorContainer}>
          <Text style={styles.errorText}>
            Connection Error: {connectionError}
          </Text>
        </View>
      )}
      
      <FlatList
        data={listeners}
        renderItem={renderListener}
        keyExtractor={(item) => item.user_id.toString()}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
        }
        ListEmptyComponent={
          <Text style={styles.emptyText}>No listeners available</Text>
        }
      />
    </View>
  );
};

const styles = {
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5'
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 16,
    backgroundColor: 'white',
    borderBottomWidth: 1,
    borderBottomColor: '#e0e0e0'
  },
  title: {
    fontSize: 20,
    fontWeight: 'bold'
  },
  statsContainer: {
    flexDirection: 'row',
    alignItems: 'center'
  },
  statsText: {
    fontSize: 12,
    color: '#666',
    marginRight: 8
  },
  connectionStatus: {
    width: 8,
    height: 8,
    borderRadius: 4
  },
  errorContainer: {
    backgroundColor: '#ffebee',
    padding: 12,
    margin: 16
  },
  errorText: {
    color: '#c62828',
    fontSize: 14
  },
  listenerItem: {
    backgroundColor: 'white',
    marginHorizontal: 16,
    marginVertical: 4,
    padding: 16,
    borderRadius: 8,
    elevation: 2
  },
  listenerInfo: {
    flex: 1
  },
  username: {
    fontSize: 16,
    fontWeight: 'bold',
    marginBottom: 4
  },
  statusContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8
  },
  statusDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    marginRight: 6
  },
  statusText: {
    fontSize: 12,
    color: '#666'
  },
  bio: {
    fontSize: 14,
    color: '#333',
    marginBottom: 4
  },
  interests: {
    fontSize: 12,
    color: '#666',
    fontStyle: 'italic'
  },
  emptyText: {
    textAlign: 'center',
    marginTop: 50,
    fontSize: 16,
    color: '#666'
  }
};

export default FeedScreen;
```

### 4. Heartbeat Integration

```typescript
// utils/heartbeat.ts
import AsyncStorage from '@react-native-async-storage/async-storage';

export const startHeartbeat = async () => {
  const sendHeartbeat = async () => {
    try {
      const token = await AsyncStorage.getItem('access_token');
      if (!token) return;

      await fetch('http://localhost:8000/users/me/heartbeat', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });
    } catch (error) {
      console.error('Heartbeat error:', error);
    }
  };

  // Send heartbeat every 30 seconds
  const interval = setInterval(sendHeartbeat, 30000);
  
  // Send initial heartbeat
  sendHeartbeat();
  
  return () => clearInterval(interval);
};
```

### 5. App Integration

```typescript
// App.tsx
import React, { useEffect } from 'react';
import { startHeartbeat } from './utils/heartbeat';
import FeedScreen from './screens/FeedScreen';

export default function App() {
  useEffect(() => {
    // Start heartbeat when app becomes active
    const stopHeartbeat = startHeartbeat();
    
    return () => {
      stopHeartbeat();
    };
  }, []);

  return <FeedScreen />;
}
```

## Message Types

### Incoming Messages

1. **Connection Established**
```json
{
  "type": "connection_established",
  "message": "Connected to feed updates",
  "user_id": 123
}
```

2. **User Status Update**
```json
{
  "type": "user_status_update",
  "user_id": 456,
  "status": {
    "user_id": 456,
    "username": "john_doe",
    "profile_image_url": "https://...",
    "is_online": true,
    "last_seen": "2024-01-15T10:30:00Z",
    "is_busy": false,
    "busy_until": null,
    "is_available": true
  }
}
```

3. **Pong Response**
```json
{
  "type": "pong",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### Outgoing Messages

1. **Ping**
```json
{
  "type": "ping",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

2. **Subscribe**
```json
{
  "type": "subscribe",
  "subscription": "feed"
}
```

## Key Features

- ✅ **Real-time Updates**: Status changes are instantly reflected in the feed
- ✅ **Automatic Reconnection**: WebSocket reconnects on connection loss
- ✅ **Connection Status**: Visual indicator of WebSocket connection state
- ✅ **Efficient Updates**: Only updates changed user data
- ✅ **Heartbeat Integration**: Keeps user status active and triggers broadcasts
- ✅ **Error Handling**: Graceful handling of connection errors
- ✅ **Performance**: Optimized for mobile devices

This implementation ensures that when a listener goes on a call and their status is updated via the heartbeat endpoint, all connected feed pages will receive the real-time update without needing to refresh the app! 🚀
