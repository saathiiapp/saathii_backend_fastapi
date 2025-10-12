---
sidebar_position: 8
title: React Native WebSocket
description: Complete real-time WebSocket integration for React Native apps
---

# React Native WebSocket

Complete guide for integrating real-time WebSocket connections, presence tracking, and live updates into React Native applications.

## Overview

- **Real-time Connection**: WebSocket connection management
- **Presence Tracking**: Live user presence updates
- **Event Handling**: Real-time event processing
- **Connection Management**: Automatic reconnection and error handling

## WebSocket Service

### WebSocket Service Implementation

```typescript
// services/WebSocketService.ts
import { EventEmitter } from 'events';

export interface WebSocketMessage {
  type: string;
  data: any;
  timestamp: string;
}

export interface PresenceUpdate {
  user_id: number;
  is_online: boolean;
  is_busy: boolean;
  last_seen: string;
}

export interface CallUpdate {
  call_id: number;
  status: 'started' | 'ended' | 'billing';
  user_id: number;
  listener_id: number;
  duration?: number;
  coins_charged?: number;
}

export interface FeedUpdate {
  type: 'listener_online' | 'listener_offline' | 'listener_busy' | 'listener_available';
  user_id: number;
  data: any;
}

export interface NotificationUpdate {
  type: 'favorite_added' | 'favorite_removed' | 'user_blocked' | 'user_unblocked';
  user_id: number;
  data: any;
}

class WebSocketService extends EventEmitter {
  private ws: WebSocket | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000;
  private isConnecting = false;
  private heartbeatInterval: NodeJS.Timeout | null = null;
  private token: string | null = null;

  constructor() {
    super();
  }

  // Connect to WebSocket
  async connect(token: string): Promise<void> {
    if (this.isConnecting || (this.ws && this.ws.readyState === WebSocket.OPEN)) {
      return;
    }

    this.token = token;
    this.isConnecting = true;

    try {
      const wsUrl = `ws://localhost:8000/ws/feed?token=${token}`;
      this.ws = new WebSocket(wsUrl);

      this.ws.onopen = () => {
        console.log('WebSocket connected');
        this.isConnecting = false;
        this.reconnectAttempts = 0;
        this.startHeartbeat();
        this.emit('connected');
      };

      this.ws.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data);
          this.handleMessage(message);
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error);
        }
      };

      this.ws.onclose = (event) => {
        console.log('WebSocket disconnected:', event.code, event.reason);
        this.isConnecting = false;
        this.stopHeartbeat();
        this.emit('disconnected', event);
        this.handleReconnect();
      };

      this.ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        this.isConnecting = false;
        this.emit('error', error);
      };

    } catch (error) {
      console.error('Failed to connect WebSocket:', error);
      this.isConnecting = false;
      this.emit('error', error);
    }
  }

  // Disconnect WebSocket
  disconnect(): void {
    this.stopHeartbeat();
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
    this.emit('disconnected');
  }

  // Send message
  send(type: string, data: any): void {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      const message: WebSocketMessage = {
        type,
        data,
        timestamp: new Date().toISOString(),
      };
      this.ws.send(JSON.stringify(message));
    } else {
      console.warn('WebSocket not connected, cannot send message');
    }
  }

  // Send heartbeat
  private startHeartbeat(): void {
    this.heartbeatInterval = setInterval(() => {
      this.send('heartbeat', {});
    }, 30000); // Send heartbeat every 30 seconds
  }

  // Stop heartbeat
  private stopHeartbeat(): void {
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval);
      this.heartbeatInterval = null;
    }
  }

  // Handle reconnection
  private handleReconnect(): void {
    if (this.reconnectAttempts < this.maxReconnectAttempts && this.token) {
      this.reconnectAttempts++;
      const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);
      
      console.log(`Attempting to reconnect in ${delay}ms (attempt ${this.reconnectAttempts})`);
      
      setTimeout(() => {
        this.connect(this.token!);
      }, delay);
    } else {
      console.log('Max reconnection attempts reached');
      this.emit('maxReconnectAttemptsReached');
    }
  }

  // Handle incoming messages
  private handleMessage(message: WebSocketMessage): void {
    switch (message.type) {
      case 'presence_update':
        this.emit('presenceUpdate', message.data as PresenceUpdate);
        break;
      case 'call_update':
        this.emit('callUpdate', message.data as CallUpdate);
        break;
      case 'feed_update':
        this.emit('feedUpdate', message.data as FeedUpdate);
        break;
      case 'notification':
        this.emit('notification', message.data as NotificationUpdate);
        break;
      case 'heartbeat_response':
        // Heartbeat response received
        break;
      default:
        console.log('Unknown message type:', message.type);
    }
  }

  // Get connection status
  get isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN;
  }

  // Get connection state
  get connectionState(): string {
    if (!this.ws) return 'disconnected';
    switch (this.ws.readyState) {
      case WebSocket.CONNECTING: return 'connecting';
      case WebSocket.OPEN: return 'connected';
      case WebSocket.CLOSING: return 'closing';
      case WebSocket.CLOSED: return 'disconnected';
      default: return 'unknown';
    }
  }
}

export default new WebSocketService();
```

## WebSocket Context

### WebSocket Context Implementation

```typescript
// contexts/WebSocketContext.tsx
import React, { createContext, useContext, useEffect, useState } from 'react';
import WebSocketService, { PresenceUpdate, CallUpdate, FeedUpdate, NotificationUpdate } from '../services/WebSocketService';
import { useAuth } from './AuthContext';

interface WebSocketContextType {
  isConnected: boolean;
  connectionState: string;
  presenceUpdates: PresenceUpdate[];
  callUpdates: CallUpdate[];
  feedUpdates: FeedUpdate[];
  notifications: NotificationUpdate[];
  connect: () => Promise<void>;
  disconnect: () => void;
  sendMessage: (type: string, data: any) => void;
  clearNotifications: () => void;
}

const WebSocketContext = createContext<WebSocketContextType | undefined>(undefined);

export const useWebSocket = () => {
  const context = useContext(WebSocketContext);
  if (!context) {
    throw new Error('useWebSocket must be used within a WebSocketProvider');
  }
  return context;
};

interface WebSocketProviderProps {
  children: React.ReactNode;
}

export const WebSocketProvider: React.FC<WebSocketProviderProps> = ({ children }) => {
  const { token, isAuthenticated } = useAuth();
  const [isConnected, setIsConnected] = useState(false);
  const [connectionState, setConnectionState] = useState('disconnected');
  const [presenceUpdates, setPresenceUpdates] = useState<PresenceUpdate[]>([]);
  const [callUpdates, setCallUpdates] = useState<CallUpdate[]>([]);
  const [feedUpdates, setFeedUpdates] = useState<FeedUpdate[]>([]);
  const [notifications, setNotifications] = useState<NotificationUpdate[]>([]);

  useEffect(() => {
    if (isAuthenticated && token) {
      connect();
    } else {
      disconnect();
    }

    return () => {
      disconnect();
    };
  }, [isAuthenticated, token]);

  useEffect(() => {
    // Listen to WebSocket events
    const handleConnected = () => {
      setIsConnected(true);
      setConnectionState('connected');
    };

    const handleDisconnected = () => {
      setIsConnected(false);
      setConnectionState('disconnected');
    };

    const handlePresenceUpdate = (update: PresenceUpdate) => {
      setPresenceUpdates(prev => [update, ...prev.slice(0, 99)]); // Keep last 100 updates
    };

    const handleCallUpdate = (update: CallUpdate) => {
      setCallUpdates(prev => [update, ...prev.slice(0, 99)]);
    };

    const handleFeedUpdate = (update: FeedUpdate) => {
      setFeedUpdates(prev => [update, ...prev.slice(0, 99)]);
    };

    const handleNotification = (notification: NotificationUpdate) => {
      setNotifications(prev => [notification, ...prev.slice(0, 99)]);
    };

    const handleError = (error: any) => {
      console.error('WebSocket error:', error);
    };

    const handleMaxReconnectAttempts = () => {
      setConnectionState('failed');
    };

    // Add event listeners
    WebSocketService.on('connected', handleConnected);
    WebSocketService.on('disconnected', handleDisconnected);
    WebSocketService.on('presenceUpdate', handlePresenceUpdate);
    WebSocketService.on('callUpdate', handleCallUpdate);
    WebSocketService.on('feedUpdate', handleFeedUpdate);
    WebSocketService.on('notification', handleNotification);
    WebSocketService.on('error', handleError);
    WebSocketService.on('maxReconnectAttemptsReached', handleMaxReconnectAttempts);

    // Cleanup
    return () => {
      WebSocketService.off('connected', handleConnected);
      WebSocketService.off('disconnected', handleDisconnected);
      WebSocketService.off('presenceUpdate', handlePresenceUpdate);
      WebSocketService.off('callUpdate', handleCallUpdate);
      WebSocketService.off('feedUpdate', handleFeedUpdate);
      WebSocketService.off('notification', handleNotification);
      WebSocketService.off('error', handleError);
      WebSocketService.off('maxReconnectAttemptsReached', handleMaxReconnectAttempts);
    };
  }, []);

  const connect = async () => {
    if (token) {
      await WebSocketService.connect(token);
    }
  };

  const disconnect = () => {
    WebSocketService.disconnect();
  };

  const sendMessage = (type: string, data: any) => {
    WebSocketService.send(type, data);
  };

  const clearNotifications = () => {
    setNotifications([]);
  };

  const value: WebSocketContextType = {
    isConnected,
    connectionState,
    presenceUpdates,
    callUpdates,
    feedUpdates,
    notifications,
    connect,
    disconnect,
    sendMessage,
    clearNotifications,
  };

  return (
    <WebSocketContext.Provider value={value}>
      {children}
    </WebSocketContext.Provider>
  );
};
```

## Real-time Components

### Connection Status Indicator

```typescript
// components/ConnectionStatusIndicator.tsx
import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity } from 'react-native';
import { useWebSocket } from '../contexts/WebSocketContext';

const ConnectionStatusIndicator: React.FC = () => {
  const { isConnected, connectionState, connect } = useWebSocket();

  const getStatusColor = () => {
    switch (connectionState) {
      case 'connected': return '#4CAF50';
      case 'connecting': return '#FF9800';
      case 'disconnected': return '#F44336';
      case 'failed': return '#9E9E9E';
      default: return '#9E9E9E';
    }
  };

  const getStatusText = () => {
    switch (connectionState) {
      case 'connected': return 'Connected';
      case 'connecting': return 'Connecting...';
      case 'disconnected': return 'Disconnected';
      case 'failed': return 'Connection Failed';
      default: return 'Unknown';
    }
  };

  const handleReconnect = () => {
    if (connectionState === 'disconnected' || connectionState === 'failed') {
      connect();
    }
  };

  return (
    <TouchableOpacity
      style={[styles.container, { backgroundColor: getStatusColor() }]}
      onPress={handleReconnect}
      disabled={isConnected}
    >
      <View style={styles.indicator} />
      <Text style={styles.text}>{getStatusText()}</Text>
    </TouchableOpacity>
  );
};

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 15,
    marginHorizontal: 10,
    marginVertical: 5,
  },
  indicator: {
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: '#fff',
    marginRight: 6,
  },
  text: {
    color: '#fff',
    fontSize: 12,
    fontWeight: 'bold',
  },
});

export default ConnectionStatusIndicator;
```

### Live Presence Indicator

```typescript
// components/LivePresenceIndicator.tsx
import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { useWebSocket } from '../contexts/WebSocketContext';

interface LivePresenceIndicatorProps {
  userId: number;
  username: string;
}

const LivePresenceIndicator: React.FC<LivePresenceIndicatorProps> = ({
  userId,
  username,
}) => {
  const { presenceUpdates } = useWebSocket();
  const [currentPresence, setCurrentPresence] = useState<{
    is_online: boolean;
    is_busy: boolean;
    last_seen: string;
  } | null>(null);

  useEffect(() => {
    // Find the latest presence update for this user
    const userPresence = presenceUpdates.find(update => update.user_id === userId);
    if (userPresence) {
      setCurrentPresence({
        is_online: userPresence.is_online,
        is_busy: userPresence.is_busy,
        last_seen: userPresence.last_seen,
      });
    }
  }, [presenceUpdates, userId]);

  if (!currentPresence) {
    return null;
  }

  const getStatusColor = () => {
    if (currentPresence.is_busy) return '#FF9800';
    if (currentPresence.is_online) return '#4CAF50';
    return '#9E9E9E';
  };

  const getStatusText = () => {
    if (currentPresence.is_busy) return 'Busy';
    if (currentPresence.is_online) return 'Online';
    return 'Offline';
  };

  const formatLastSeen = (lastSeen: string) => {
    const date = new Date(lastSeen);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    
    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffMins < 1440) return `${Math.floor(diffMins / 60)}h ago`;
    return `${Math.floor(diffMins / 1440)}d ago`;
  };

  return (
    <View style={styles.container}>
      <View style={[styles.indicator, { backgroundColor: getStatusColor() }]} />
      <Text style={styles.statusText}>{getStatusText()}</Text>
      {!currentPresence.is_online && (
        <Text style={styles.lastSeenText}>
          Last seen {formatLastSeen(currentPresence.last_seen)}
        </Text>
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    alignItems: 'center',
    marginVertical: 2,
  },
  indicator: {
    width: 8,
    height: 8,
    borderRadius: 4,
    marginRight: 6,
  },
  statusText: {
    fontSize: 12,
    fontWeight: 'bold',
    color: '#333',
  },
  lastSeenText: {
    fontSize: 10,
    color: '#666',
    marginLeft: 4,
  },
});

export default LivePresenceIndicator;
```

### Real-time Notifications

```typescript
// components/RealTimeNotifications.tsx
import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  Animated,
  Dimensions,
} from 'react-native';
import { useWebSocket } from '../contexts/WebSocketContext';

const { width } = Dimensions.get('window');

const RealTimeNotifications: React.FC = () => {
  const { notifications, clearNotifications } = useWebSocket();
  const [visibleNotifications, setVisibleNotifications] = useState<any[]>([]);
  const [slideAnim] = useState(new Animated.Value(-width));

  useEffect(() => {
    if (notifications.length > 0) {
      const latestNotification = notifications[0];
      setVisibleNotifications(prev => [latestNotification, ...prev.slice(0, 4)]);
      
      // Animate slide in
      Animated.timing(slideAnim, {
        toValue: 0,
        duration: 300,
        useNativeDriver: true,
      }).start();

      // Auto hide after 5 seconds
      setTimeout(() => {
        hideNotification(latestNotification);
      }, 5000);
    }
  }, [notifications]);

  const hideNotification = (notification: any) => {
    Animated.timing(slideAnim, {
      toValue: -width,
      duration: 300,
      useNativeDriver: true,
    }).start(() => {
      setVisibleNotifications(prev => prev.filter(n => n !== notification));
    });
  };

  const getNotificationIcon = (type: string) => {
    switch (type) {
      case 'favorite_added': return '❤️';
      case 'favorite_removed': return '💔';
      case 'user_blocked': return '🚫';
      case 'user_unblocked': return '✅';
      default: return '📢';
    }
  };

  const getNotificationText = (notification: any) => {
    switch (notification.type) {
      case 'favorite_added':
        return `${notification.data.username} added you to favorites`;
      case 'favorite_removed':
        return `${notification.data.username} removed you from favorites`;
      case 'user_blocked':
        return `${notification.data.username} blocked you`;
      case 'user_unblocked':
        return `${notification.data.username} unblocked you`;
      default:
        return 'New notification';
    }
  };

  if (visibleNotifications.length === 0) {
    return null;
  }

  return (
    <View style={styles.container}>
      {visibleNotifications.map((notification, index) => (
        <Animated.View
          key={`${notification.user_id}-${notification.timestamp}-${index}`}
          style={[
            styles.notification,
            {
              transform: [{ translateX: slideAnim }],
              zIndex: 1000 - index,
            },
          ]}
        >
          <TouchableOpacity
            style={styles.notificationContent}
            onPress={() => hideNotification(notification)}
          >
            <Text style={styles.notificationIcon}>
              {getNotificationIcon(notification.type)}
            </Text>
            <Text style={styles.notificationText}>
              {getNotificationText(notification)}
            </Text>
          </TouchableOpacity>
        </Animated.View>
      ))}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    position: 'absolute',
    top: 50,
    left: 0,
    right: 0,
    zIndex: 1000,
  },
  notification: {
    backgroundColor: '#fff',
    marginHorizontal: 10,
    marginVertical: 2,
    borderRadius: 8,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.25,
    shadowRadius: 4,
    elevation: 5,
  },
  notificationContent: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 15,
  },
  notificationIcon: {
    fontSize: 20,
    marginRight: 10,
  },
  notificationText: {
    flex: 1,
    fontSize: 14,
    color: '#333',
  },
});

export default RealTimeNotifications;
```

## Integration Examples

### Using WebSocket in App Root

```typescript
// App.tsx
import React from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { WebSocketProvider } from './contexts/WebSocketContext';
import { AuthProvider } from './contexts/AuthContext';
import { FavoritesProvider } from './contexts/FavoritesContext';
import { BlockingProvider } from './contexts/BlockingProvider';
import AppNavigator from './navigation/AppNavigator';
import RealTimeNotifications from './components/RealTimeNotifications';

const App: React.FC = () => {
  return (
    <AuthProvider>
      <WebSocketProvider>
        <FavoritesProvider>
          <BlockingProvider>
            <NavigationContainer>
              <AppNavigator />
              <RealTimeNotifications />
            </NavigationContainer>
          </BlockingProvider>
        </FavoritesProvider>
      </WebSocketProvider>
    </AuthProvider>
  );
};

export default App;
```

### Using WebSocket in Screens

```typescript
// screens/HomeScreen.tsx
import React, { useEffect, useState } from 'react';
import { View, Text, StyleSheet, FlatList } from 'react-native';
import { useWebSocket } from '../contexts/WebSocketContext';
import ConnectionStatusIndicator from '../components/ConnectionStatusIndicator';
import LivePresenceIndicator from '../components/LivePresenceIndicator';

const HomeScreen: React.FC = () => {
  const { isConnected, presenceUpdates, callUpdates, feedUpdates } = useWebSocket();
  const [recentActivity, setRecentActivity] = useState<any[]>([]);

  useEffect(() => {
    // Combine all updates for recent activity
    const allUpdates = [
      ...presenceUpdates.map(update => ({ ...update, type: 'presence' })),
      ...callUpdates.map(update => ({ ...update, type: 'call' })),
      ...feedUpdates.map(update => ({ ...update, type: 'feed' })),
    ].sort((a, b) => new Date(b.timestamp || 0).getTime() - new Date(a.timestamp || 0).getTime());

    setRecentActivity(allUpdates.slice(0, 20));
  }, [presenceUpdates, callUpdates, feedUpdates]);

  const renderActivityItem = ({ item }: { item: any }) => (
    <View style={styles.activityItem}>
      <Text style={styles.activityText}>
        {item.type === 'presence' && `${item.user_id} is now ${item.is_online ? 'online' : 'offline'}`}
        {item.type === 'call' && `Call ${item.call_id} ${item.status}`}
        {item.type === 'feed' && `Feed update: ${item.type}`}
      </Text>
    </View>
  );

  return (
    <View style={styles.container}>
      <ConnectionStatusIndicator />
      
      <Text style={styles.title}>Real-time Activity</Text>
      <Text style={styles.subtitle}>
        {isConnected ? 'Connected to live updates' : 'Disconnected'}
      </Text>

      <FlatList
        data={recentActivity}
        renderItem={renderActivityItem}
        keyExtractor={(item, index) => `${item.type}-${index}`}
        style={styles.activityList}
      />
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    margin: 20,
  },
  subtitle: {
    fontSize: 16,
    color: '#666',
    marginHorizontal: 20,
    marginBottom: 20,
  },
  activityList: {
    flex: 1,
    paddingHorizontal: 20,
  },
  activityItem: {
    backgroundColor: '#fff',
    padding: 15,
    marginBottom: 10,
    borderRadius: 8,
  },
  activityText: {
    fontSize: 14,
    color: '#333',
  },
});

export default HomeScreen;
```

## Best Practices

### WebSocket Management

1. **Connection Lifecycle**: Properly manage connection lifecycle
2. **Reconnection Logic**: Implement exponential backoff for reconnection
3. **Heartbeat**: Send regular heartbeats to keep connection alive
4. **Error Handling**: Handle connection errors gracefully

### Performance

1. **Message Filtering**: Filter messages by type and relevance
2. **Memory Management**: Limit stored updates to prevent memory leaks
3. **Efficient Updates**: Use efficient data structures for updates
4. **Background Handling**: Handle WebSocket in background properly

### User Experience

1. **Connection Status**: Show clear connection status to users
2. **Graceful Degradation**: Handle offline scenarios gracefully
3. **Real-time Feedback**: Provide immediate feedback for user actions
4. **Notification Management**: Manage notifications effectively

## Next Steps

- Learn about [React Native Authentication](./react-native-authentication)
- Explore [React Native User Management](./react-native-user-management)
- Check out [React Native Calls](./react-native-calls)
