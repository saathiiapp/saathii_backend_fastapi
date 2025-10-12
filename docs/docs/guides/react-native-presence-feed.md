# React Native Integration - Presence & Feed System

This guide covers the presence tracking system and feed functionality for discovering listeners in your React Native app.

## Presence & Status System

### 1. Get User Status

**Business Purpose**: Get current user's online status, busy status, and last seen information.

```typescript
// services/presenceService.ts
export interface UserStatusResponse {
  user_id: number;
  is_online: boolean;
  last_seen: string;
  is_busy: boolean;
  busy_until: string | null;
  updated_at: string;
}

export const getUserStatus = async (): Promise<UserStatusResponse> => {
  try {
    const response = await httpClient.get('/users/me/status');
    return response.data;
  } catch (error) {
    throw new Error(`Failed to get user status: ${error.response?.data?.detail || error.message}`);
  }
};
```

### 2. Update User Status

**Business Purpose**: Update user's online/offline status and busy status.

```typescript
// services/presenceService.ts
export interface UpdateStatusRequest {
  is_online?: boolean;
  is_busy?: boolean;
  busy_until?: string; // ISO datetime string
}

export const updateUserStatus = async (data: UpdateStatusRequest): Promise<UserStatusResponse> => {
  try {
    const response = await httpClient.put('/users/me/status', data);
    return response.data;
  } catch (error) {
    throw new Error(`Failed to update status: ${error.response?.data?.detail || error.message}`);
  }
};
```

**React Native Component Example**:

```typescript
// components/StatusToggle.tsx
import React, { useState, useEffect } from 'react';
import { View, Text, TouchableOpacity, Switch } from 'react-native';
import { getUserStatus, updateUserStatus } from '../services/presenceService';

const StatusToggle = () => {
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadStatus();
  }, []);

  const loadStatus = async () => {
    try {
      const userStatus = await getUserStatus();
      setStatus(userStatus);
    } catch (error) {
      console.error('Failed to load status:', error);
    }
  };

  const handleOnlineToggle = async (isOnline: boolean) => {
    setLoading(true);
    try {
      const updatedStatus = await updateUserStatus({ is_online: isOnline });
      setStatus(updatedStatus);
    } catch (error) {
      console.error('Failed to update online status:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleBusyToggle = async (isBusy: boolean) => {
    setLoading(true);
    try {
      const busyUntil = isBusy ? new Date(Date.now() + 2 * 60 * 60 * 1000).toISOString() : null;
      const updatedStatus = await updateUserStatus({ 
        is_busy: isBusy, 
        busy_until: busyUntil 
      });
      setStatus(updatedStatus);
    } catch (error) {
      console.error('Failed to update busy status:', error);
    } finally {
      setLoading(false);
    }
  };

  if (!status) {
    return <View><Text>Loading status...</Text></View>;
  }

  return (
    <View style={styles.container}>
      <View style={styles.statusItem}>
        <Text style={styles.label}>Online Status</Text>
        <Switch
          value={status.is_online}
          onValueChange={handleOnlineToggle}
          disabled={loading}
        />
      </View>
      
      <View style={styles.statusItem}>
        <Text style={styles.label}>Busy Status</Text>
        <Switch
          value={status.is_busy}
          onValueChange={handleBusyToggle}
          disabled={loading || !status.is_online}
        />
      </View>
      
      <Text style={styles.lastSeen}>
        Last seen: {new Date(status.last_seen).toLocaleString()}
      </Text>
    </View>
  );
};

const styles = {
  container: {
    padding: 20,
    backgroundColor: 'white',
    borderRadius: 10,
    margin: 10,
  },
  statusItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 15,
  },
  label: {
    fontSize: 16,
    fontWeight: '500',
  },
  lastSeen: {
    fontSize: 12,
    color: '#666',
    textAlign: 'center',
    marginTop: 10,
  },
};

export default StatusToggle;
```

### 3. Heartbeat System

**Business Purpose**: Send periodic heartbeat to keep user online and update last_seen timestamp.

```typescript
// services/presenceService.ts
export const sendHeartbeat = async (): Promise<{ message: string }> => {
  try {
    const response = await httpClient.post('/users/me/heartbeat');
    return response.data;
  } catch (error) {
    throw new Error(`Failed to send heartbeat: ${error.response?.data?.detail || error.message}`);
  }
};
```

**React Native Hook for Heartbeat**:

```typescript
// hooks/useHeartbeat.ts
import { useEffect, useRef } from 'react';
import { AppState } from 'react-native';
import { sendHeartbeat } from '../services/presenceService';

export const useHeartbeat = (isOnline: boolean) => {
  const intervalRef = useRef(null);

  useEffect(() => {
    if (isOnline) {
      // Send heartbeat every 30 seconds
      intervalRef.current = setInterval(async () => {
        try {
          await sendHeartbeat();
        } catch (error) {
          console.error('Heartbeat failed:', error);
        }
      }, 30000);
    } else {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    }

    // Handle app state changes
    const handleAppStateChange = (nextAppState: string) => {
      if (nextAppState === 'active' && isOnline) {
        // Send immediate heartbeat when app becomes active
        sendHeartbeat().catch(console.error);
      }
    };

    const subscription = AppState.addEventListener('change', handleAppStateChange);

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
      subscription?.remove();
    };
  }, [isOnline]);
};
```

### 4. Get User Presence

**Business Purpose**: Get another user's presence status.

```typescript
// services/presenceService.ts
export interface UserPresenceResponse {
  user_id: number;
  username: string;
  is_online: boolean;
  last_seen: string;
  is_busy: boolean;
  busy_until: string | null;
}

export const getUserPresence = async (userId: number): Promise<UserPresenceResponse> => {
  try {
    const response = await httpClient.get(`/users/${userId}/presence`);
    return response.data;
  } catch (error) {
    throw new Error(`Failed to get user presence: ${error.response?.data?.detail || error.message}`);
  }
};

export const getMultipleUsersPresence = async (userIds: number[]): Promise<UserPresenceResponse[]> => {
  try {
    const response = await httpClient.get('/users/presence', {
      params: { user_ids: userIds.join(',') }
    });
    return response.data;
  } catch (error) {
    throw new Error(`Failed to get users presence: ${error.response?.data?.detail || error.message}`);
  }
};
```

## Feed System

### 1. Get Listeners Feed

**Business Purpose**: Get paginated list of listeners with filtering options for discovery.

```typescript
// services/feedService.ts
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
  busy_until: string | null;
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

export interface FeedFilters {
  online_only?: boolean;
  available_only?: boolean;
  language?: string;
  interests?: string;
  min_rating?: number;
  page?: number;
  per_page?: number;
}

export const getListenersFeed = async (filters: FeedFilters = {}): Promise<FeedResponse> => {
  try {
    const response = await httpClient.get('/feed/listeners', { params: filters });
    return response.data;
  } catch (error) {
    throw new Error(`Failed to get listeners feed: ${error.response?.data?.detail || error.message}`);
  }
};
```

**React Native Component Example**:

```typescript
// components/ListenersFeedScreen.tsx
import React, { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  FlatList,
  TouchableOpacity,
  Image,
  RefreshControl,
  TextInput,
  Picker,
} from 'react-native';
import { getListenersFeed, ListenerFeedItem } from '../services/feedService';

const ListenersFeedScreen = () => {
  const [listeners, setListeners] = useState<ListenerFeedItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [page, setPage] = useState(1);
  const [hasNext, setHasNext] = useState(false);
  const [filters, setFilters] = useState({
    online_only: false,
    available_only: false,
    language: '',
    interests: '',
    min_rating: 0,
  });

  useEffect(() => {
    loadListeners(true);
  }, [filters]);

  const loadListeners = async (reset = false) => {
    if (loading) return;
    
    setLoading(true);
    try {
      const currentPage = reset ? 1 : page;
      const response = await getListenersFeed({
        ...filters,
        page: currentPage,
        per_page: 20,
      });
      
      if (reset) {
        setListeners(response.listeners);
        setPage(1);
      } else {
        setListeners(prev => [...prev, ...response.listeners]);
      }
      
      setHasNext(response.has_next);
      if (!reset) setPage(prev => prev + 1);
    } catch (error) {
      console.error('Failed to load listeners:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleRefresh = useCallback(() => {
    setRefreshing(true);
    loadListeners(true).finally(() => setRefreshing(false));
  }, [filters]);

  const handleLoadMore = () => {
    if (hasNext && !loading) {
      loadListeners(false);
    }
  };

  const renderListener = ({ item }: { item: ListenerFeedItem }) => (
    <TouchableOpacity style={styles.listenerCard}>
      <View style={styles.listenerHeader}>
        {item.profile_image_url ? (
          <Image source={{ uri: item.profile_image_url }} style={styles.avatar} />
        ) : (
          <View style={[styles.avatar, styles.avatarPlaceholder]}>
            <Text style={styles.avatarText}>
              {item.username.charAt(0).toUpperCase()}
            </Text>
          </View>
        )}
        
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
          {item.rating > 0 && (
            <Text style={styles.rating}>⭐ {item.rating}/5</Text>
          )}
        </View>
      </View>
      
      {item.bio && (
        <Text style={styles.bio} numberOfLines={2}>
          {item.bio}
        </Text>
      )}
      
      {item.interests.length > 0 && (
        <View style={styles.interestsContainer}>
          {item.interests.slice(0, 3).map((interest, index) => (
            <View key={index} style={styles.interestTag}>
              <Text style={styles.interestText}>{interest}</Text>
            </View>
          ))}
          {item.interests.length > 3 && (
            <Text style={styles.moreInterests}>+{item.interests.length - 3} more</Text>
          )}
        </View>
      )}
    </TouchableOpacity>
  );

  return (
    <View style={styles.container}>
      <View style={styles.filtersContainer}>
        <View style={styles.filterRow}>
          <TouchableOpacity
            style={[styles.filterButton, filters.online_only && styles.filterButtonActive]}
            onPress={() => setFilters(prev => ({ ...prev, online_only: !prev.online_only }))}
          >
            <Text style={[styles.filterButtonText, filters.online_only && styles.filterButtonTextActive]}>
              Online Only
            </Text>
          </TouchableOpacity>
          
          <TouchableOpacity
            style={[styles.filterButton, filters.available_only && styles.filterButtonActive]}
            onPress={() => setFilters(prev => ({ ...prev, available_only: !prev.available_only }))}
          >
            <Text style={[styles.filterButtonText, filters.available_only && styles.filterButtonTextActive]}>
              Available Only
            </Text>
          </TouchableOpacity>
        </View>
        
        <TextInput
          style={styles.filterInput}
          placeholder="Search by interests..."
          value={filters.interests}
          onChangeText={(text) => setFilters(prev => ({ ...prev, interests: text }))}
        />
      </View>

      <FlatList
        data={listeners}
        renderItem={renderListener}
        keyExtractor={(item) => item.user_id.toString()}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={handleRefresh} />
        }
        onEndReached={handleLoadMore}
        onEndReachedThreshold={0.5}
        ListFooterComponent={() => 
          loading ? <Text style={styles.loadingText}>Loading more...</Text> : null
        }
        ListEmptyComponent={() => 
          !loading ? <Text style={styles.emptyText}>No listeners found</Text> : null
        }
      />
    </View>
  );
};

const styles = {
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  filtersContainer: {
    backgroundColor: 'white',
    padding: 15,
    borderBottomWidth: 1,
    borderBottomColor: '#eee',
  },
  filterRow: {
    flexDirection: 'row',
    marginBottom: 10,
  },
  filterButton: {
    paddingHorizontal: 15,
    paddingVertical: 8,
    borderRadius: 20,
    backgroundColor: '#f0f0f0',
    marginRight: 10,
  },
  filterButtonActive: {
    backgroundColor: '#007AFF',
  },
  filterButtonText: {
    color: '#666',
    fontSize: 12,
  },
  filterButtonTextActive: {
    color: 'white',
  },
  filterInput: {
    borderWidth: 1,
    borderColor: '#ddd',
    borderRadius: 8,
    padding: 10,
    fontSize: 14,
  },
  listenerCard: {
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
  listenerHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 10,
  },
  avatar: {
    width: 50,
    height: 50,
    borderRadius: 25,
    marginRight: 15,
  },
  avatarPlaceholder: {
    backgroundColor: '#ddd',
    justifyContent: 'center',
    alignItems: 'center',
  },
  avatarText: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#666',
  },
  listenerInfo: {
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
    fontSize: 12,
    color: '#666',
  },
  rating: {
    fontSize: 12,
    color: '#FF9800',
  },
  bio: {
    fontSize: 14,
    color: '#666',
    marginBottom: 10,
  },
  interestsContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    alignItems: 'center',
  },
  interestTag: {
    backgroundColor: '#E3F2FD',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 12,
    marginRight: 5,
    marginBottom: 5,
  },
  interestText: {
    fontSize: 10,
    color: '#1976D2',
  },
  moreInterests: {
    fontSize: 10,
    color: '#666',
    fontStyle: 'italic',
  },
  loadingText: {
    textAlign: 'center',
    padding: 20,
    color: '#666',
  },
  emptyText: {
    textAlign: 'center',
    padding: 40,
    color: '#666',
    fontSize: 16,
  },
};

export default ListenersFeedScreen;
```

### 2. Get Feed Statistics

**Business Purpose**: Get statistics about listeners in the feed.

```typescript
// services/feedService.ts
export interface FeedStats {
  total_listeners: number;
  online_listeners: number;
  available_listeners: number;
  busy_listeners: number;
}

export const getFeedStats = async (): Promise<FeedStats> => {
  try {
    const response = await httpClient.get('/feed/stats');
    return response.data;
  } catch (error) {
    throw new Error(`Failed to get feed stats: ${error.response?.data?.detail || error.message}`);
  }
};
```

**React Native Component Example**:

```typescript
// components/FeedStatsCard.tsx
import React, { useState, useEffect } from 'react';
import { View, Text } from 'react-native';
import { getFeedStats } from '../services/feedService';

const FeedStatsCard = () => {
  const [stats, setStats] = useState(null);

  useEffect(() => {
    loadStats();
  }, []);

  const loadStats = async () => {
    try {
      const feedStats = await getFeedStats();
      setStats(feedStats);
    } catch (error) {
      console.error('Failed to load feed stats:', error);
    }
  };

  if (!stats) {
    return <View><Text>Loading stats...</Text></View>;
  }

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Listeners Online</Text>
      
      <View style={styles.statsGrid}>
        <View style={styles.statItem}>
          <Text style={styles.statNumber}>{stats.total_listeners}</Text>
          <Text style={styles.statLabel}>Total</Text>
        </View>
        
        <View style={styles.statItem}>
          <Text style={[styles.statNumber, { color: '#4CAF50' }]}>
            {stats.online_listeners}
          </Text>
          <Text style={styles.statLabel}>Online</Text>
        </View>
        
        <View style={styles.statItem}>
          <Text style={[styles.statNumber, { color: '#2196F3' }]}>
            {stats.available_listeners}
          </Text>
          <Text style={styles.statLabel}>Available</Text>
        </View>
        
        <View style={styles.statItem}>
          <Text style={[styles.statNumber, { color: '#FF9800' }]}>
            {stats.busy_listeners}
          </Text>
          <Text style={styles.statLabel}>Busy</Text>
        </View>
      </View>
    </View>
  );
};

const styles = {
  container: {
    backgroundColor: 'white',
    margin: 10,
    padding: 20,
    borderRadius: 10,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  title: {
    fontSize: 18,
    fontWeight: 'bold',
    marginBottom: 15,
    textAlign: 'center',
  },
  statsGrid: {
    flexDirection: 'row',
    justifyContent: 'space-around',
  },
  statItem: {
    alignItems: 'center',
  },
  statNumber: {
    fontSize: 24,
    fontWeight: 'bold',
    marginBottom: 5,
  },
  statLabel: {
    fontSize: 12,
    color: '#666',
  },
};

export default FeedStatsCard;
```

This documentation covers the presence tracking and feed system functionality. The examples show how to implement real-time status updates, listener discovery, and filtering capabilities in your React Native app.

Would you like me to continue with the Call Management system next?
