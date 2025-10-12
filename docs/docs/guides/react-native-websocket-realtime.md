# React Native Integration - WebSocket Real-time Updates

This guide covers WebSocket integration for real-time presence updates, feed updates, and live status tracking in your React Native app.

## WebSocket Real-time System

### 1. WebSocket Connection Manager

**Business Purpose**: Manage WebSocket connections for real-time updates across the app.

```typescript
// services/websocketService.ts
import AsyncStorage from '@react-native-async-storage/async-storage';

export interface WebSocketMessage {
  type: string;
  data?: any;
  timestamp?: number;
}

export interface PresenceUpdate {
  user_id: number;
  username: string;
  is_online: boolean;
  last_seen: string;
  is_busy: boolean;
  busy_until: string | null;
}

export interface FeedUpdate {
  type: 'user_online' | 'user_offline' | 'user_busy' | 'user_available';
  user_id: number;
  username: string;
  is_online: boolean;
  is_busy: boolean;
  last_seen: string;
}

class WebSocketManager {
  private feedConnection: WebSocket | null = null;
  private presenceConnection: WebSocket | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000;
  private heartbeatInterval: NodeJS.Timeout | null = null;
  private messageHandlers: Map<string, Function[]> = new Map();

  async connect() {
    try {
      const token = await AsyncStorage.getItem('access_token');
      if (!token) {
        throw new Error('No access token found');
      }

      await this.connectFeed(token);
      await this.connectPresence(token);
      this.startHeartbeat();
    } catch (error) {
      console.error('WebSocket connection failed:', error);
      this.scheduleReconnect();
    }
  }

  private async connectFeed(token: string) {
    return new Promise<void>((resolve, reject) => {
      const wsUrl = `ws://localhost:8000/ws/feed?token=${token}`;
      this.feedConnection = new WebSocket(wsUrl);

      this.feedConnection.onopen = () => {
        console.log('Feed WebSocket connected');
        this.reconnectAttempts = 0;
        resolve();
      };

      this.feedConnection.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data);
          this.handleMessage('feed', message);
        } catch (error) {
          console.error('Failed to parse feed message:', error);
        }
      };

      this.feedConnection.onclose = () => {
        console.log('Feed WebSocket disconnected');
        this.scheduleReconnect();
      };

      this.feedConnection.onerror = (error) => {
        console.error('Feed WebSocket error:', error);
        reject(error);
      };
    });
  }

  private async connectPresence(token: string) {
    return new Promise<void>((resolve, reject) => {
      const wsUrl = `ws://localhost:8000/ws/presence?token=${token}`;
      this.presenceConnection = new WebSocket(wsUrl);

      this.presenceConnection.onopen = () => {
        console.log('Presence WebSocket connected');
        resolve();
      };

      this.presenceConnection.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data);
          this.handleMessage('presence', message);
        } catch (error) {
          console.error('Failed to parse presence message:', error);
        }
      };

      this.presenceConnection.onclose = () => {
        console.log('Presence WebSocket disconnected');
        this.scheduleReconnect();
      };

      this.presenceConnection.onerror = (error) => {
        console.error('Presence WebSocket error:', error);
        reject(error);
      };
    });
  }

  private handleMessage(channel: string, message: WebSocketMessage) {
    const handlers = this.messageHandlers.get(channel) || [];
    handlers.forEach(handler => {
      try {
        handler(message);
      } catch (error) {
        console.error('Error in message handler:', error);
      }
    });
  }

  private startHeartbeat() {
    this.heartbeatInterval = setInterval(() => {
      this.sendPing();
    }, 30000); // Send ping every 30 seconds
  }

  private sendPing() {
    const pingMessage = {
      type: 'ping',
      timestamp: Date.now(),
    };

    if (this.feedConnection?.readyState === WebSocket.OPEN) {
      this.feedConnection.send(JSON.stringify(pingMessage));
    }

    if (this.presenceConnection?.readyState === WebSocket.OPEN) {
      this.presenceConnection.send(JSON.stringify(pingMessage));
    }
  }

  private scheduleReconnect() {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);
      
      setTimeout(() => {
        console.log(`Attempting to reconnect (${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
        this.connect();
      }, delay);
    } else {
      console.error('Max reconnection attempts reached');
    }
  }

  subscribe(channel: 'feed' | 'presence', handler: (message: WebSocketMessage) => void) {
    if (!this.messageHandlers.has(channel)) {
      this.messageHandlers.set(channel, []);
    }
    this.messageHandlers.get(channel)!.push(handler);
  }

  unsubscribe(channel: 'feed' | 'presence', handler: (message: WebSocketMessage) => void) {
    const handlers = this.messageHandlers.get(channel) || [];
    const index = handlers.indexOf(handler);
    if (index > -1) {
      handlers.splice(index, 1);
    }
  }

  disconnect() {
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval);
      this.heartbeatInterval = null;
    }

    if (this.feedConnection) {
      this.feedConnection.close();
      this.feedConnection = null;
    }

    if (this.presenceConnection) {
      this.presenceConnection.close();
      this.presenceConnection = null;
    }

    this.messageHandlers.clear();
  }

  isConnected(): boolean {
    return (
      this.feedConnection?.readyState === WebSocket.OPEN &&
      this.presenceConnection?.readyState === WebSocket.OPEN
    );
  }
}

export const websocketManager = new WebSocketManager();
```

### 2. Real-time Presence Updates

**Business Purpose**: Receive real-time updates when users come online, go offline, or change their busy status.

```typescript
// hooks/usePresenceUpdates.ts
import { useEffect, useState } from 'react';
import { websocketManager, PresenceUpdate } from '../services/websocketService';

export const usePresenceUpdates = () => {
  const [presenceUpdates, setPresenceUpdates] = useState<PresenceUpdate[]>([]);

  useEffect(() => {
    const handlePresenceMessage = (message: any) => {
      if (message.type === 'presence_update') {
        setPresenceUpdates(prev => {
          const existingIndex = prev.findIndex(update => update.user_id === message.data.user_id);
          if (existingIndex > -1) {
            // Update existing user
            const updated = [...prev];
            updated[existingIndex] = message.data;
            return updated;
          } else {
            // Add new user
            return [...prev, message.data];
          }
        });
      }
    };

    websocketManager.subscribe('presence', handlePresenceMessage);

    return () => {
      websocketManager.unsubscribe('presence', handlePresenceMessage);
    };
  }, []);

  return presenceUpdates;
};
```

**React Native Component Example**:

```typescript
// components/RealTimePresenceList.tsx
import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  FlatList,
  TouchableOpacity,
  StyleSheet,
} from 'react-native';
import { usePresenceUpdates } from '../hooks/usePresenceUpdates';
import { websocketManager } from '../services/websocketService';

const RealTimePresenceList = () => {
  const [isConnected, setIsConnected] = useState(false);
  const presenceUpdates = usePresenceUpdates();

  useEffect(() => {
    // Connect to WebSocket when component mounts
    websocketManager.connect();
    setIsConnected(websocketManager.isConnected());

    // Check connection status periodically
    const interval = setInterval(() => {
      setIsConnected(websocketManager.isConnected());
    }, 5000);

    return () => {
      clearInterval(interval);
      websocketManager.disconnect();
    };
  }, []);

  const getStatusColor = (isOnline: boolean, isBusy: boolean) => {
    if (!isOnline) return '#9E9E9E';
    if (isBusy) return '#FF9800';
    return '#4CAF50';
  };

  const getStatusText = (isOnline: boolean, isBusy: boolean) => {
    if (!isOnline) return 'Offline';
    if (isBusy) return 'Busy';
    return 'Available';
  };

  const renderUser = ({ item }: { item: any }) => (
    <View style={styles.userCard}>
      <View style={styles.userInfo}>
        <Text style={styles.username}>{item.username}</Text>
        <View style={styles.statusContainer}>
          <View style={[
            styles.statusDot,
            { backgroundColor: getStatusColor(item.is_online, item.is_busy) }
          ]} />
          <Text style={styles.statusText}>
            {getStatusText(item.is_online, item.is_busy)}
          </Text>
        </View>
        <Text style={styles.lastSeen}>
          Last seen: {new Date(item.last_seen).toLocaleString()}
        </Text>
      </View>
    </View>
  );

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>Live Presence Updates</Text>
        <View style={styles.connectionStatus}>
          <View style={[
            styles.connectionDot,
            { backgroundColor: isConnected ? '#4CAF50' : '#F44336' }
          ]} />
          <Text style={styles.connectionText}>
            {isConnected ? 'Connected' : 'Disconnected'}
          </Text>
        </View>
      </View>

      <FlatList
        data={presenceUpdates}
        renderItem={renderUser}
        keyExtractor={(item) => item.user_id.toString()}
        ListEmptyComponent={() => (
          <Text style={styles.emptyText}>No presence updates yet</Text>
        )}
      />
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 15,
    backgroundColor: 'white',
    borderBottomWidth: 1,
    borderBottomColor: '#eee',
  },
  title: {
    fontSize: 18,
    fontWeight: 'bold',
  },
  connectionStatus: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  connectionDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    marginRight: 5,
  },
  connectionText: {
    fontSize: 12,
    color: '#666',
  },
  userCard: {
    backgroundColor: 'white',
    margin: 10,
    padding: 15,
    borderRadius: 10,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  userInfo: {
    flex: 1,
  },
  username: {
    fontSize: 16,
    fontWeight: 'bold',
    marginBottom: 5,
  },
  statusContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 5,
  },
  statusDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    marginRight: 5,
  },
  statusText: {
    fontSize: 14,
    color: '#666',
  },
  lastSeen: {
    fontSize: 12,
    color: '#999',
  },
  emptyText: {
    textAlign: 'center',
    padding: 40,
    color: '#666',
    fontSize: 16,
  },
});

export default RealTimePresenceList;
```

### 3. Real-time Feed Updates

**Business Purpose**: Receive real-time updates when listeners come online, go offline, or change their availability status.

```typescript
// hooks/useFeedUpdates.ts
import { useEffect, useState } from 'react';
import { websocketManager, FeedUpdate } from '../services/websocketService';

export const useFeedUpdates = () => {
  const [feedUpdates, setFeedUpdates] = useState<FeedUpdate[]>([]);

  useEffect(() => {
    const handleFeedMessage = (message: any) => {
      if (message.type === 'feed_update') {
        setFeedUpdates(prev => {
          const existingIndex = prev.findIndex(update => update.user_id === message.data.user_id);
          if (existingIndex > -1) {
            // Update existing user
            const updated = [...prev];
            updated[existingIndex] = message.data;
            return updated;
          } else {
            // Add new user
            return [...prev, message.data];
          }
        });
      }
    };

    websocketManager.subscribe('feed', handleFeedMessage);

    return () => {
      websocketManager.unsubscribe('feed', handleFeedMessage);
    };
  }, []);

  return feedUpdates;
};
```

**React Native Component Example**:

```typescript
// components/LiveFeedScreen.tsx
import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  FlatList,
  TouchableOpacity,
  StyleSheet,
  Animated,
} from 'react-native';
import { useFeedUpdates } from '../hooks/useFeedUpdates';
import { websocketManager } from '../services/websocketService';

const LiveFeedScreen = () => {
  const [isConnected, setIsConnected] = useState(false);
  const [notifications, setNotifications] = useState<string[]>([]);
  const feedUpdates = useFeedUpdates();
  const fadeAnim = new Animated.Value(0);

  useEffect(() => {
    websocketManager.connect();
    setIsConnected(websocketManager.isConnected());

    const interval = setInterval(() => {
      setIsConnected(websocketManager.isConnected());
    }, 5000);

    return () => {
      clearInterval(interval);
      websocketManager.disconnect();
    };
  }, []);

  useEffect(() => {
    // Show notification when feed updates
    if (feedUpdates.length > 0) {
      const latestUpdate = feedUpdates[feedUpdates.length - 1];
      const notification = `${latestUpdate.username} is now ${getStatusText(latestUpdate.is_online, latestUpdate.is_busy)}`;
      
      setNotifications(prev => [...prev, notification]);
      
      // Animate notification
      Animated.sequence([
        Animated.timing(fadeAnim, {
          toValue: 1,
          duration: 300,
          useNativeDriver: true,
        }),
        Animated.delay(2000),
        Animated.timing(fadeAnim, {
          toValue: 0,
          duration: 300,
          useNativeDriver: true,
        }),
      ]).start(() => {
        setNotifications(prev => prev.slice(1));
      });
    }
  }, [feedUpdates]);

  const getStatusText = (isOnline: boolean, isBusy: boolean) => {
    if (!isOnline) return 'offline';
    if (isBusy) return 'busy';
    return 'available';
  };

  const getStatusColor = (isOnline: boolean, isBusy: boolean) => {
    if (!isOnline) return '#9E9E9E';
    if (isBusy) return '#FF9800';
    return '#4CAF50';
  };

  const renderUser = ({ item }: { item: any }) => (
    <View style={styles.userCard}>
      <View style={styles.userInfo}>
        <Text style={styles.username}>{item.username}</Text>
        <View style={styles.statusContainer}>
          <View style={[
            styles.statusDot,
            { backgroundColor: getStatusColor(item.is_online, item.is_busy) }
          ]} />
          <Text style={styles.statusText}>
            {getStatusText(item.is_online, item.is_busy)}
          </Text>
        </View>
        <Text style={styles.lastSeen}>
          Last seen: {new Date(item.last_seen).toLocaleString()}
        </Text>
      </View>
      
      <TouchableOpacity style={styles.callButton}>
        <Text style={styles.callButtonText}>Call</Text>
      </TouchableOpacity>
    </View>
  );

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>Live Feed</Text>
        <View style={styles.connectionStatus}>
          <View style={[
            styles.connectionDot,
            { backgroundColor: isConnected ? '#4CAF50' : '#F44336' }
          ]} />
          <Text style={styles.connectionText}>
            {isConnected ? 'Live' : 'Offline'}
          </Text>
        </View>
      </View>

      {notifications.length > 0 && (
        <Animated.View style={[styles.notification, { opacity: fadeAnim }]}>
          <Text style={styles.notificationText}>
            {notifications[0]}
          </Text>
        </Animated.View>
      )}

      <FlatList
        data={feedUpdates}
        renderItem={renderUser}
        keyExtractor={(item) => item.user_id.toString()}
        ListEmptyComponent={() => (
          <Text style={styles.emptyText}>No live updates yet</Text>
        )}
      />
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 15,
    backgroundColor: 'white',
    borderBottomWidth: 1,
    borderBottomColor: '#eee',
  },
  title: {
    fontSize: 18,
    fontWeight: 'bold',
  },
  connectionStatus: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  connectionDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    marginRight: 5,
  },
  connectionText: {
    fontSize: 12,
    color: '#666',
  },
  notification: {
    backgroundColor: '#4CAF50',
    padding: 10,
    margin: 10,
    borderRadius: 5,
  },
  notificationText: {
    color: 'white',
    textAlign: 'center',
    fontWeight: 'bold',
  },
  userCard: {
    backgroundColor: 'white',
    margin: 10,
    padding: 15,
    borderRadius: 10,
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  userInfo: {
    flex: 1,
  },
  username: {
    fontSize: 16,
    fontWeight: 'bold',
    marginBottom: 5,
  },
  statusContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 5,
  },
  statusDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    marginRight: 5,
  },
  statusText: {
    fontSize: 14,
    color: '#666',
  },
  lastSeen: {
    fontSize: 12,
    color: '#999',
  },
  callButton: {
    backgroundColor: '#007AFF',
    paddingHorizontal: 15,
    paddingVertical: 8,
    borderRadius: 15,
  },
  callButtonText: {
    color: 'white',
    fontSize: 12,
    fontWeight: 'bold',
  },
  emptyText: {
    textAlign: 'center',
    padding: 40,
    color: '#666',
    fontSize: 16,
  },
});

export default LiveFeedScreen;
```

### 4. WebSocket Connection Status Indicator

**Business Purpose**: Show real-time connection status and handle reconnection.

```typescript
// components/ConnectionStatusIndicator.tsx
import React, { useState, useEffect } from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';
import { websocketManager } from '../services/websocketService';

const ConnectionStatusIndicator = () => {
  const [isConnected, setIsConnected] = useState(false);
  const [reconnecting, setReconnecting] = useState(false);

  useEffect(() => {
    const checkConnection = () => {
      setIsConnected(websocketManager.isConnected());
    };

    checkConnection();
    const interval = setInterval(checkConnection, 2000);

    return () => clearInterval(interval);
  }, []);

  const handleReconnect = async () => {
    setReconnecting(true);
    try {
      await websocketManager.connect();
      setIsConnected(true);
    } catch (error) {
      console.error('Reconnection failed:', error);
    } finally {
      setReconnecting(false);
    }
  };

  if (isConnected) {
    return (
      <View style={styles.connectedContainer}>
        <View style={styles.connectedDot} />
        <Text style={styles.connectedText}>Connected</Text>
      </View>
    );
  }

  return (
    <TouchableOpacity
      style={styles.disconnectedContainer}
      onPress={handleReconnect}
      disabled={reconnecting}
    >
      <View style={styles.disconnectedDot} />
      <Text style={styles.disconnectedText}>
        {reconnecting ? 'Reconnecting...' : 'Tap to reconnect'}
      </Text>
    </TouchableOpacity>
  );
};

const styles = StyleSheet.create({
  connectedContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 10,
    paddingVertical: 5,
    backgroundColor: '#E8F5E8',
    borderRadius: 15,
  },
  connectedDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: '#4CAF50',
    marginRight: 5,
  },
  connectedText: {
    fontSize: 12,
    color: '#4CAF50',
    fontWeight: '500',
  },
  disconnectedContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 10,
    paddingVertical: 5,
    backgroundColor: '#FFEBEE',
    borderRadius: 15,
  },
  disconnectedDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: '#F44336',
    marginRight: 5,
  },
  disconnectedText: {
    fontSize: 12,
    color: '#F44336',
    fontWeight: '500',
  },
});

export default ConnectionStatusIndicator;
```

### 5. App-wide WebSocket Integration

**Business Purpose**: Initialize WebSocket connections when the app starts and manage them throughout the app lifecycle.

```typescript
// hooks/useWebSocket.ts
import { useEffect, useState } from 'react';
import { AppState } from 'react-native';
import { websocketManager } from '../services/websocketService';
import AsyncStorage from '@react-native-async-storage/async-storage';

export const useWebSocket = () => {
  const [isConnected, setIsConnected] = useState(false);
  const [isInitialized, setIsInitialized] = useState(false);

  useEffect(() => {
    const initializeWebSocket = async () => {
      try {
        const token = await AsyncStorage.getItem('access_token');
        if (token) {
          await websocketManager.connect();
          setIsConnected(true);
        }
      } catch (error) {
        console.error('Failed to initialize WebSocket:', error);
      } finally {
        setIsInitialized(true);
      }
    };

    initializeWebSocket();

    // Handle app state changes
    const handleAppStateChange = (nextAppState: string) => {
      if (nextAppState === 'active' && !isConnected) {
        // Reconnect when app becomes active
        websocketManager.connect().then(() => {
          setIsConnected(true);
        });
      } else if (nextAppState === 'background') {
        // Disconnect when app goes to background to save battery
        websocketManager.disconnect();
        setIsConnected(false);
      }
    };

    const subscription = AppState.addEventListener('change', handleAppStateChange);

    return () => {
      subscription?.remove();
      websocketManager.disconnect();
    };
  }, []);

  return { isConnected, isInitialized };
};
```

**React Native App Integration**:

```typescript
// App.tsx
import React from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { useWebSocket } from './hooks/useWebSocket';
import ConnectionStatusIndicator from './components/ConnectionStatusIndicator';
import LiveFeedScreen from './components/LiveFeedScreen';
import RealTimePresenceList from './components/RealTimePresenceList';

const Tab = createBottomTabNavigator();

const App = () => {
  const { isConnected, isInitialized } = useWebSocket();

  if (!isInitialized) {
    return (
      <View style={{ flex: 1, justifyContent: 'center', alignItems: 'center' }}>
        <Text>Initializing...</Text>
      </View>
    );
  }

  return (
    <NavigationContainer>
      <Tab.Navigator
        screenOptions={{
          headerRight: () => <ConnectionStatusIndicator />,
        }}
      >
        <Tab.Screen name="LiveFeed" component={LiveFeedScreen} />
        <Tab.Screen name="Presence" component={RealTimePresenceList} />
      </Tab.Navigator>
    </NavigationContainer>
  );
};

export default App;
```

This documentation covers the complete WebSocket integration for real-time updates in your React Native app. The examples show how to implement live presence tracking, feed updates, connection management, and proper error handling.

The system provides:
- Real-time presence updates
- Live feed updates
- Connection status monitoring
- Automatic reconnection
- App lifecycle management
- Battery optimization

Would you like me to continue with the remaining features like Favorites, Blocking, and Listener Verification?
