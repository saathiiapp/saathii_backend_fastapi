---
sidebar_position: 6
title: React Native Favorites
description: Complete favorites management for React Native apps
---

# React Native Favorites

Complete guide for integrating favorites management and user preferences into React Native applications.

## Overview

- **Favorite Management**: Add and remove favorite listeners
- **Favorites List**: Get paginated list of favorite users
- **Status Checking**: Check if a user is favorited
- **User Preferences**: Track user interaction patterns

## Favorites Service

### Favorites Service Implementation

```typescript
// services/FavoritesService.ts
import ApiService from './ApiService';

export interface FavoriteUser {
  user_id: number;
  username: string;
  bio: string;
  interests: string[];
  profile_image_url?: string;
  preferred_language?: string;
  rating: number;
  country: string;
  is_online: boolean;
  is_busy: boolean;
  last_seen: string;
  wait_time?: number;
  is_available: boolean;
  favorited_at: string;
}

export interface FavoritesResponse {
  favorites: FavoriteUser[];
  total_count: number;
  page: number;
  per_page: number;
  has_next: boolean;
  has_previous: boolean;
}

export interface AddFavoriteRequest {
  listener_id: number;
}

export interface RemoveFavoriteRequest {
  listener_id: number;
}

export interface FavoriteActionResponse {
  success: boolean;
  message: string;
  listener_id: number;
  is_favorited: boolean;
}

class FavoritesService {
  // Add favorite
  async addFavorite(listenerId: number): Promise<FavoriteActionResponse> {
    return ApiService.post<FavoriteActionResponse>('/favorites/add', {
      listener_id: listenerId,
    });
  }

  // Remove favorite
  async removeFavorite(listenerId: number): Promise<FavoriteActionResponse> {
    return ApiService.delete<FavoriteActionResponse>('/favorites/remove', {
      listener_id: listenerId,
    });
  }

  // Get favorites list
  async getFavorites(page: number = 1, perPage: number = 20): Promise<FavoritesResponse> {
    return ApiService.get<FavoritesResponse>(`/favorites?page=${page}&per_page=${perPage}`);
  }

  // Check favorite status
  async checkFavoriteStatus(listenerId: number): Promise<FavoriteActionResponse> {
    return ApiService.get<FavoriteActionResponse>(`/favorites/check/${listenerId}`);
  }
}

export default new FavoritesService();
```

## Favorites Screens

### Favorites List Screen

```typescript
// screens/FavoritesListScreen.tsx
import React, { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  FlatList,
  StyleSheet,
  RefreshControl,
  ActivityIndicator,
  TouchableOpacity,
  Alert,
} from 'react-native';
import FavoritesService, { FavoriteUser } from '../services/FavoritesService';
import FavoriteCard from '../components/FavoriteCard';

const FavoritesListScreen: React.FC = () => {
  const [favorites, setFavorites] = useState<FavoriteUser[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [loadingMore, setLoadingMore] = useState(false);
  const [page, setPage] = useState(1);
  const [hasNext, setHasNext] = useState(true);

  useEffect(() => {
    loadFavorites(true);
  }, []);

  const loadFavorites = async (reset: boolean = false) => {
    if (reset) {
      setPage(1);
      setIsLoading(true);
    } else {
      setLoadingMore(true);
    }

    try {
      const currentPage = reset ? 1 : page;
      const response = await FavoritesService.getFavorites(currentPage, 20);
      
      if (reset) {
        setFavorites(response.favorites);
      } else {
        setFavorites(prev => [...prev, ...response.favorites]);
      }
      
      setHasNext(response.has_next);
      setPage(currentPage + 1);
    } catch (error) {
      console.error('Failed to load favorites:', error);
      Alert.alert('Error', 'Failed to load favorites');
    } finally {
      setIsLoading(false);
      setLoadingMore(false);
    }
  };

  const handleRefresh = useCallback(() => {
    setRefreshing(true);
    loadFavorites(true).finally(() => setRefreshing(false));
  }, []);

  const handleLoadMore = () => {
    if (!loadingMore && hasNext) {
      loadFavorites(false);
    }
  };

  const handleRemoveFavorite = async (listenerId: number) => {
    Alert.alert(
      'Remove from Favorites',
      'Are you sure you want to remove this listener from your favorites?',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Remove',
          style: 'destructive',
          onPress: async () => {
            try {
              await FavoritesService.removeFavorite(listenerId);
              setFavorites(prev => prev.filter(fav => fav.user_id !== listenerId));
              Alert.alert('Success', 'Removed from favorites');
            } catch (error) {
              Alert.alert('Error', 'Failed to remove from favorites');
            }
          },
        },
      ]
    );
  };

  const handleStartCall = (listener: FavoriteUser) => {
    // Navigate to start call screen with selected listener
    console.log('Start call with:', listener.username);
  };

  const renderFavorite = ({ item }: { item: FavoriteUser }) => (
    <FavoriteCard
      favorite={item}
      onRemove={() => handleRemoveFavorite(item.user_id)}
      onStartCall={() => handleStartCall(item)}
    />
  );

  const renderFooter = () => {
    if (!loadingMore) return null;
    return (
      <View style={styles.footerLoader}>
        <ActivityIndicator size="small" color="#007AFF" />
      </View>
    );
  };

  const renderEmpty = () => (
    <View style={styles.emptyContainer}>
      <Text style={styles.emptyTitle}>No Favorites Yet</Text>
      <Text style={styles.emptySubtitle}>
        Start adding listeners to your favorites to see them here
      </Text>
    </View>
  );

  if (isLoading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#007AFF" />
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>My Favorites</Text>
        <Text style={styles.subtitle}>
          {favorites.length} favorite{favorites.length !== 1 ? 's' : ''}
        </Text>
      </View>

      <FlatList
        data={favorites}
        renderItem={renderFavorite}
        keyExtractor={(item) => item.user_id.toString()}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={handleRefresh} />
        }
        onEndReached={handleLoadMore}
        onEndReachedThreshold={0.5}
        ListFooterComponent={renderFooter}
        ListEmptyComponent={renderEmpty}
        contentContainerStyle={styles.listContainer}
      />
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  header: {
    backgroundColor: '#fff',
    padding: 20,
    borderBottomWidth: 1,
    borderBottomColor: '#eee',
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    marginBottom: 5,
  },
  subtitle: {
    fontSize: 16,
    color: '#666',
  },
  listContainer: {
    padding: 10,
  },
  footerLoader: {
    padding: 20,
    alignItems: 'center',
  },
  emptyContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 40,
  },
  emptyTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    marginBottom: 10,
    color: '#333',
  },
  emptySubtitle: {
    fontSize: 16,
    color: '#666',
    textAlign: 'center',
    lineHeight: 22,
  },
});

export default FavoritesListScreen;
```

### Favorite Card Component

```typescript
// components/FavoriteCard.tsx
import React from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  Image,
  Alert,
} from 'react-native';
import { FavoriteUser } from '../services/FavoritesService';
import StatusIndicator from './StatusIndicator';

interface FavoriteCardProps {
  favorite: FavoriteUser;
  onRemove: () => void;
  onStartCall: () => void;
}

const FavoriteCard: React.FC<FavoriteCardProps> = ({
  favorite,
  onRemove,
  onStartCall,
}) => {
  const formatFavoritedDate = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
    
    if (diffDays === 0) return 'Today';
    if (diffDays === 1) return 'Yesterday';
    if (diffDays < 7) return `${diffDays} days ago`;
    if (diffDays < 30) return `${Math.floor(diffDays / 7)} weeks ago`;
    return `${Math.floor(diffDays / 30)} months ago`;
  };

  return (
    <View style={styles.card}>
      <View style={styles.header}>
        <View style={styles.profileContainer}>
          {favorite.profile_image_url ? (
            <Image
              source={{ uri: favorite.profile_image_url }}
              style={styles.profileImage}
            />
          ) : (
            <View style={styles.placeholderImage}>
              <Text style={styles.placeholderText}>
                {favorite.username.charAt(0).toUpperCase()}
              </Text>
            </View>
          )}
          
          <View style={styles.profileInfo}>
            <Text style={styles.username}>{favorite.username}</Text>
            <StatusIndicator
              isOnline={favorite.is_online}
              isBusy={favorite.is_busy}
              size="small"
            />
            <Text style={styles.favoritedDate}>
              Added {formatFavoritedDate(favorite.favorited_at)}
            </Text>
          </View>
        </View>
        
        <View style={styles.ratingContainer}>
          <Text style={styles.rating}>⭐ {favorite.rating.toFixed(1)}</Text>
        </View>
      </View>

      <Text style={styles.bio} numberOfLines={2}>
        {favorite.bio}
      </Text>

      <View style={styles.actions}>
        <TouchableOpacity
          style={[
            styles.actionButton,
            styles.callButton,
            favorite.is_busy && styles.disabledButton,
          ]}
          onPress={onStartCall}
          disabled={favorite.is_busy}
        >
          <Text
            style={[
              styles.actionButtonText,
              favorite.is_busy && styles.disabledButtonText,
            ]}
          >
            {favorite.is_busy ? 'Busy' : 'Call'}
          </Text>
        </TouchableOpacity>
        
        <TouchableOpacity
          style={[styles.actionButton, styles.removeButton]}
          onPress={onRemove}
        >
          <Text style={[styles.actionButtonText, styles.removeButtonText]}>
            Remove
          </Text>
        </TouchableOpacity>
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  card: {
    backgroundColor: '#fff',
    marginBottom: 10,
    padding: 15,
    borderRadius: 8,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 2,
    elevation: 2,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 10,
  },
  profileContainer: {
    flexDirection: 'row',
    flex: 1,
  },
  profileImage: {
    width: 50,
    height: 50,
    borderRadius: 25,
    marginRight: 10,
  },
  placeholderImage: {
    width: 50,
    height: 50,
    borderRadius: 25,
    backgroundColor: '#007AFF',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 10,
  },
  placeholderText: {
    color: '#fff',
    fontSize: 20,
    fontWeight: 'bold',
  },
  profileInfo: {
    flex: 1,
  },
  username: {
    fontSize: 16,
    fontWeight: 'bold',
    marginBottom: 5,
  },
  favoritedDate: {
    fontSize: 12,
    color: '#666',
    marginTop: 2,
  },
  ratingContainer: {
    alignItems: 'flex-end',
  },
  rating: {
    fontSize: 14,
    color: '#FFD700',
    fontWeight: 'bold',
  },
  bio: {
    fontSize: 14,
    color: '#666',
    marginBottom: 15,
    lineHeight: 18,
  },
  actions: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  actionButton: {
    flex: 1,
    paddingVertical: 10,
    paddingHorizontal: 15,
    borderRadius: 6,
    alignItems: 'center',
    marginHorizontal: 5,
  },
  callButton: {
    backgroundColor: '#007AFF',
  },
  removeButton: {
    backgroundColor: '#FF3B30',
  },
  disabledButton: {
    backgroundColor: '#ccc',
  },
  actionButtonText: {
    fontSize: 14,
    fontWeight: 'bold',
    color: '#fff',
  },
  removeButtonText: {
    color: '#fff',
  },
  disabledButtonText: {
    color: '#999',
  },
});

export default FavoriteCard;
```

### Add to Favorites Component

```typescript
// components/AddToFavoritesButton.tsx
import React, { useState, useEffect } from 'react';
import {
  TouchableOpacity,
  Text,
  StyleSheet,
  ActivityIndicator,
  Alert,
} from 'react-native';
import FavoritesService from '../services/FavoritesService';

interface AddToFavoritesButtonProps {
  listenerId: number;
  listenerName: string;
  onFavoriteChange?: (isFavorited: boolean) => void;
}

const AddToFavoritesButton: React.FC<AddToFavoritesButtonProps> = ({
  listenerId,
  listenerName,
  onFavoriteChange,
}) => {
  const [isFavorited, setIsFavorited] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [checkingStatus, setCheckingStatus] = useState(true);

  useEffect(() => {
    checkFavoriteStatus();
  }, [listenerId]);

  const checkFavoriteStatus = async () => {
    try {
      const response = await FavoritesService.checkFavoriteStatus(listenerId);
      setIsFavorited(response.is_favorited);
    } catch (error) {
      console.error('Failed to check favorite status:', error);
    } finally {
      setCheckingStatus(false);
    }
  };

  const handleToggleFavorite = async () => {
    if (isLoading) return;

    setIsLoading(true);
    try {
      if (isFavorited) {
        await FavoritesService.removeFavorite(listenerId);
        setIsFavorited(false);
        Alert.alert('Removed', `${listenerName} removed from favorites`);
      } else {
        await FavoritesService.addFavorite(listenerId);
        setIsFavorited(true);
        Alert.alert('Added', `${listenerName} added to favorites`);
      }
      onFavoriteChange?.(!isFavorited);
    } catch (error) {
      Alert.alert(
        'Error',
        `Failed to ${isFavorited ? 'remove from' : 'add to'} favorites`
      );
    } finally {
      setIsLoading(false);
    }
  };

  if (checkingStatus) {
    return (
      <TouchableOpacity style={[styles.button, styles.loadingButton]} disabled>
        <ActivityIndicator size="small" color="#007AFF" />
      </TouchableOpacity>
    );
  }

  return (
    <TouchableOpacity
      style={[
        styles.button,
        isFavorited ? styles.favoritedButton : styles.unfavoritedButton,
        isLoading && styles.loadingButton,
      ]}
      onPress={handleToggleFavorite}
      disabled={isLoading}
    >
      {isLoading ? (
        <ActivityIndicator size="small" color="#fff" />
      ) : (
        <Text style={styles.buttonText}>
          {isFavorited ? '❤️ Favorited' : '🤍 Add to Favorites'}
        </Text>
      )}
    </TouchableOpacity>
  );
};

const styles = StyleSheet.create({
  button: {
    paddingHorizontal: 20,
    paddingVertical: 10,
    borderRadius: 20,
    alignItems: 'center',
    minWidth: 140,
  },
  unfavoritedButton: {
    backgroundColor: '#007AFF',
  },
  favoritedButton: {
    backgroundColor: '#FF3B30',
  },
  loadingButton: {
    backgroundColor: '#ccc',
  },
  buttonText: {
    color: '#fff',
    fontSize: 14,
    fontWeight: 'bold',
  },
});

export default AddToFavoritesButton;
```

### Favorites Context

```typescript
// contexts/FavoritesContext.tsx
import React, { createContext, useContext, useState, useEffect } from 'react';
import FavoritesService, { FavoriteUser } from '../services/FavoritesService';

interface FavoritesContextType {
  favorites: FavoriteUser[];
  isLoading: boolean;
  addFavorite: (listenerId: number) => Promise<void>;
  removeFavorite: (listenerId: number) => Promise<void>;
  isFavorited: (listenerId: number) => boolean;
  refreshFavorites: () => Promise<void>;
}

const FavoritesContext = createContext<FavoritesContextType | undefined>(undefined);

export const useFavorites = () => {
  const context = useContext(FavoritesContext);
  if (!context) {
    throw new Error('useFavorites must be used within a FavoritesProvider');
  }
  return context;
};

interface FavoritesProviderProps {
  children: React.ReactNode;
}

export const FavoritesProvider: React.FC<FavoritesProviderProps> = ({ children }) => {
  const [favorites, setFavorites] = useState<FavoriteUser[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  const loadFavorites = async () => {
    setIsLoading(true);
    try {
      const response = await FavoritesService.getFavorites(1, 100);
      setFavorites(response.favorites);
    } catch (error) {
      console.error('Failed to load favorites:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const addFavorite = async (listenerId: number) => {
    try {
      await FavoritesService.addFavorite(listenerId);
      // Refresh favorites list
      await loadFavorites();
    } catch (error) {
      throw error;
    }
  };

  const removeFavorite = async (listenerId: number) => {
    try {
      await FavoritesService.removeFavorite(listenerId);
      setFavorites(prev => prev.filter(fav => fav.user_id !== listenerId));
    } catch (error) {
      throw error;
    }
  };

  const isFavorited = (listenerId: number): boolean => {
    return favorites.some(fav => fav.user_id === listenerId);
  };

  const refreshFavorites = async () => {
    await loadFavorites();
  };

  useEffect(() => {
    loadFavorites();
  }, []);

  const value: FavoritesContextType = {
    favorites,
    isLoading,
    addFavorite,
    removeFavorite,
    isFavorited,
    refreshFavorites,
  };

  return (
    <FavoritesContext.Provider value={value}>
      {children}
    </FavoritesContext.Provider>
  );
};
```

## Integration Examples

### Using Favorites in Listener Cards

```typescript
// components/ListenerCardWithFavorites.tsx
import React from 'react';
import { View, StyleSheet } from 'react-native';
import ListenerCard from './ListenerCard';
import AddToFavoritesButton from './AddToFavoritesButton';
import { useFavorites } from '../contexts/FavoritesContext';

interface ListenerCardWithFavoritesProps {
  listener: any; // Your listener type
  onPress: () => void;
}

const ListenerCardWithFavorites: React.FC<ListenerCardWithFavoritesProps> = ({
  listener,
  onPress,
}) => {
  const { isFavorited, addFavorite, removeFavorite } = useFavorites();

  const handleFavoriteChange = async (isFavorited: boolean) => {
    try {
      if (isFavorited) {
        await addFavorite(listener.user_id);
      } else {
        await removeFavorite(listener.user_id);
      }
    } catch (error) {
      console.error('Failed to toggle favorite:', error);
    }
  };

  return (
    <View style={styles.container}>
      <ListenerCard listener={listener} onPress={onPress} />
      <View style={styles.favoriteButton}>
        <AddToFavoritesButton
          listenerId={listener.user_id}
          listenerName={listener.username}
          onFavoriteChange={handleFavoriteChange}
        />
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    marginBottom: 10,
  },
  favoriteButton: {
    paddingHorizontal: 15,
    paddingBottom: 10,
    backgroundColor: '#fff',
    borderBottomLeftRadius: 8,
    borderBottomRightRadius: 8,
  },
});

export default ListenerCardWithFavorites;
```

## Best Practices

### Favorites Management

1. **Check Status**: Always check favorite status before showing UI
2. **Optimistic Updates**: Update UI immediately, handle errors gracefully
3. **Pagination**: Use pagination for large favorites lists
4. **Caching**: Cache favorites list locally for better performance

### User Experience

1. **Visual Feedback**: Show clear visual indicators for favorite status
2. **Loading States**: Display loading indicators during operations
3. **Error Handling**: Show user-friendly error messages
4. **Confirmation**: Consider confirmation for remove actions

### Performance

1. **Lazy Loading**: Load favorites as needed
2. **Caching**: Cache favorite status for frequently accessed users
3. **Batch Operations**: Consider batch operations for multiple changes
4. **Real-time Updates**: Update UI when favorites change

## Next Steps

- Learn about [React Native Blocking](./react-native-blocking)
- Explore [React Native WebSocket](./react-native-websocket)
- Check out [React Native Feeds](./react-native-feeds)
