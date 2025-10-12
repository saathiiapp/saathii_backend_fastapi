# React Native Integration - Favorites, Blocking & Verification

This guide covers the favorites system, user blocking functionality, and listener verification features for your React Native app.

## Favorites System

### 1. Add/Remove Favorites

**Business Purpose**: Allow users to add listeners to their favorites list for quick access.

```typescript
// services/favoritesService.ts
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

export const addFavorite = async (listenerId: number): Promise<FavoriteActionResponse> => {
  try {
    const response = await httpClient.post('/favorites/add', { listener_id: listenerId });
    return response.data;
  } catch (error) {
    throw new Error(`Failed to add favorite: ${error.response?.data?.detail || error.message}`);
  }
};

export const removeFavorite = async (listenerId: number): Promise<FavoriteActionResponse> => {
  try {
    const response = await httpClient.delete('/favorites/remove', { 
      data: { listener_id: listenerId } 
    });
    return response.data;
  } catch (error) {
    throw new Error(`Failed to remove favorite: ${error.response?.data?.detail || error.message}`);
  }
};

export const checkFavoriteStatus = async (listenerId: number): Promise<FavoriteActionResponse> => {
  try {
    const response = await httpClient.get(`/favorites/check/${listenerId}`);
    return response.data;
  } catch (error) {
    throw new Error(`Failed to check favorite status: ${error.response?.data?.detail || error.message}`);
  }
};
```

**React Native Component Example**:

```typescript
// components/FavoriteButton.tsx
import React, { useState, useEffect } from 'react';
import { TouchableOpacity, Text, ActivityIndicator, Alert } from 'react-native';
import { addFavorite, removeFavorite, checkFavoriteStatus } from '../services/favoritesService';

const FavoriteButton = ({ listenerId, listenerName, style }) => {
  const [isFavorited, setIsFavorited] = useState(false);
  const [loading, setLoading] = useState(false);
  const [checking, setChecking] = useState(true);

  useEffect(() => {
    checkStatus();
  }, [listenerId]);

  const checkStatus = async () => {
    try {
      const response = await checkFavoriteStatus(listenerId);
      setIsFavorited(response.is_favorited);
    } catch (error) {
      console.error('Failed to check favorite status:', error);
    } finally {
      setChecking(false);
    }
  };

  const handleToggleFavorite = async () => {
    if (loading) return;

    setLoading(true);
    try {
      if (isFavorited) {
        const response = await removeFavorite(listenerId);
        setIsFavorited(false);
        Alert.alert('Success', `Removed ${listenerName} from favorites`);
      } else {
        const response = await addFavorite(listenerId);
        setIsFavorited(true);
        Alert.alert('Success', `Added ${listenerName} to favorites`);
      }
    } catch (error) {
      Alert.alert('Error', error.message);
    } finally {
      setLoading(false);
    }
  };

  if (checking) {
    return (
      <TouchableOpacity style={[styles.button, styles.buttonDisabled, style]} disabled>
        <ActivityIndicator size="small" color="#666" />
      </TouchableOpacity>
    );
  }

  return (
    <TouchableOpacity
      style={[
        styles.button,
        isFavorited ? styles.buttonFavorited : styles.buttonNotFavorited,
        style
      ]}
      onPress={handleToggleFavorite}
      disabled={loading}
    >
      {loading ? (
        <ActivityIndicator size="small" color="white" />
      ) : (
        <Text style={styles.buttonText}>
          {isFavorited ? '❤️ Favorited' : '🤍 Add to Favorites'}
        </Text>
      )}
    </TouchableOpacity>
  );
};

const styles = {
  button: {
    paddingHorizontal: 15,
    paddingVertical: 8,
    borderRadius: 20,
    alignItems: 'center',
    justifyContent: 'center',
    minWidth: 120,
  },
  buttonFavorited: {
    backgroundColor: '#E91E63',
  },
  buttonNotFavorited: {
    backgroundColor: '#666',
  },
  buttonDisabled: {
    backgroundColor: '#ccc',
  },
  buttonText: {
    color: 'white',
    fontSize: 12,
    fontWeight: '500',
  },
};

export default FavoriteButton;
```

### 2. Get Favorites List

**Business Purpose**: Retrieve user's favorite listeners with filtering options.

```typescript
// services/favoritesService.ts
export interface FavoriteUser {
  user_id: number;
  username: string;
  sex: string;
  bio: string;
  interests: string[];
  profile_image_url: string;
  preferred_language: string;
  rating: number;
  country: string;
  is_online: boolean;
  last_seen: string;
  is_busy: boolean;
  busy_until: string | null;
  is_available: boolean;
  favorited_at: string;
}

export interface FavoritesResponse {
  favorites: FavoriteUser[];
  total_count: number;
  online_count: number;
  available_count: number;
  page: number;
  per_page: number;
  has_next: boolean;
  has_previous: boolean;
}

export interface FavoritesFilters {
  page?: number;
  per_page?: number;
  online_only?: boolean;
  available_only?: boolean;
}

export const getFavorites = async (filters: FavoritesFilters = {}): Promise<FavoritesResponse> => {
  try {
    const response = await httpClient.get('/favorites', { params: filters });
    return response.data;
  } catch (error) {
    throw new Error(`Failed to get favorites: ${error.response?.data?.detail || error.message}`);
  }
};
```

**React Native Component Example**:

```typescript
// components/FavoritesScreen.tsx
import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  FlatList,
  TouchableOpacity,
  Image,
  RefreshControl,
  StyleSheet,
} from 'react-native';
import { getFavorites, FavoriteUser } from '../services/favoritesService';
import FavoriteButton from './FavoriteButton';

const FavoritesScreen = () => {
  const [favorites, setFavorites] = useState<FavoriteUser[]>([]);
  const [loading, setLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [page, setPage] = useState(1);
  const [hasNext, setHasNext] = useState(false);
  const [filters, setFilters] = useState({
    online_only: false,
    available_only: false,
  });

  useEffect(() => {
    loadFavorites(true);
  }, [filters]);

  const loadFavorites = async (reset = false) => {
    if (loading) return;
    
    setLoading(true);
    try {
      const currentPage = reset ? 1 : page;
      const response = await getFavorites({
        ...filters,
        page: currentPage,
        per_page: 20,
      });
      
      if (reset) {
        setFavorites(response.favorites);
        setPage(1);
      } else {
        setFavorites(prev => [...prev, ...response.favorites]);
      }
      
      setHasNext(response.has_next);
      if (!reset) setPage(prev => prev + 1);
    } catch (error) {
      console.error('Failed to load favorites:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleRefresh = () => {
    setRefreshing(true);
    loadFavorites(true).finally(() => setRefreshing(false));
  };

  const handleLoadMore = () => {
    if (hasNext && !loading) {
      loadFavorites(false);
    }
  };

  const renderFavorite = ({ item }: { item: FavoriteUser }) => (
    <View style={styles.favoriteCard}>
      <View style={styles.favoriteHeader}>
        {item.profile_image_url ? (
          <Image source={{ uri: item.profile_image_url }} style={styles.avatar} />
        ) : (
          <View style={[styles.avatar, styles.avatarPlaceholder]}>
            <Text style={styles.avatarText}>
              {item.username.charAt(0).toUpperCase()}
            </Text>
          </View>
        )}
        
        <View style={styles.favoriteInfo}>
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
        
        <FavoriteButton
          listenerId={item.user_id}
          listenerName={item.username}
          style={styles.favoriteButton}
        />
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
      
      <Text style={styles.favoritedAt}>
        Favorited on {new Date(item.favorited_at).toLocaleDateString()}
      </Text>
    </View>
  );

  return (
    <View style={styles.container}>
      <View style={styles.filtersContainer}>
        <TouchableOpacity
          style={[
            styles.filterButton,
            filters.online_only && styles.filterButtonActive
          ]}
          onPress={() => setFilters(prev => ({ ...prev, online_only: !prev.online_only }))}
        >
          <Text style={[
            styles.filterButtonText,
            filters.online_only && styles.filterButtonTextActive
          ]}>
            Online Only
          </Text>
        </TouchableOpacity>
        
        <TouchableOpacity
          style={[
            styles.filterButton,
            filters.available_only && styles.filterButtonActive
          ]}
          onPress={() => setFilters(prev => ({ ...prev, available_only: !prev.available_only }))}
        >
          <Text style={[
            styles.filterButtonText,
            filters.available_only && styles.filterButtonTextActive
          ]}>
            Available Only
          </Text>
        </TouchableOpacity>
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
        ListFooterComponent={() => 
          loading ? <Text style={styles.loadingText}>Loading more...</Text> : null
        }
        ListEmptyComponent={() => 
          !loading ? <Text style={styles.emptyText}>No favorites yet</Text> : null
        }
      />
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  filtersContainer: {
    flexDirection: 'row',
    padding: 15,
    backgroundColor: 'white',
    borderBottomWidth: 1,
    borderBottomColor: '#eee',
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
  favoriteCard: {
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
  favoriteHeader: {
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
  favoriteInfo: {
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
  favoriteButton: {
    marginLeft: 10,
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
    marginBottom: 10,
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
  favoritedAt: {
    fontSize: 12,
    color: '#999',
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
});

export default FavoritesScreen;
```

## Blocking System

### 1. Block/Unblock Users

**Business Purpose**: Allow users to block other users to prevent interactions.

```typescript
// services/blockingService.ts
export interface BlockUserRequest {
  blocked_id: number;
  action_type: 'block' | 'report';
  reason?: string;
}

export interface UnblockUserRequest {
  blocked_id: number;
}

export interface BlockActionResponse {
  success: boolean;
  message: string;
  blocked_id: number;
  action_type: string;
  is_blocked: boolean;
}

export const blockUser = async (blockedId: number, actionType: 'block' | 'report', reason?: string): Promise<BlockActionResponse> => {
  try {
    const response = await httpClient.post('/block', {
      blocked_id: blockedId,
      action_type: actionType,
      reason: reason,
    });
    return response.data;
  } catch (error) {
    throw new Error(`Failed to block user: ${error.response?.data?.detail || error.message}`);
  }
};

export const unblockUser = async (blockedId: number): Promise<BlockActionResponse> => {
  try {
    const response = await httpClient.delete('/block', {
      data: { blocked_id: blockedId }
    });
    return response.data;
  } catch (error) {
    throw new Error(`Failed to unblock user: ${error.response?.data?.detail || error.message}`);
  }
};

export const checkBlockStatus = async (userId: number): Promise<BlockActionResponse> => {
  try {
    const response = await httpClient.get(`/block/check/${userId}`);
    return response.data;
  } catch (error) {
    throw new Error(`Failed to check block status: ${error.response?.data?.detail || error.message}`);
  }
};
```

**React Native Component Example**:

```typescript
// components/BlockButton.tsx
import React, { useState, useEffect } from 'react';
import { TouchableOpacity, Text, Alert, ActivityIndicator } from 'react-native';
import { blockUser, unblockUser, checkBlockStatus } from '../services/blockingService';

const BlockButton = ({ userId, username, style }) => {
  const [isBlocked, setIsBlocked] = useState(false);
  const [loading, setLoading] = useState(false);
  const [checking, setChecking] = useState(true);

  useEffect(() => {
    checkStatus();
  }, [userId]);

  const checkStatus = async () => {
    try {
      const response = await checkBlockStatus(userId);
      setIsBlocked(response.is_blocked);
    } catch (error) {
      console.error('Failed to check block status:', error);
    } finally {
      setChecking(false);
    }
  };

  const handleBlock = () => {
    Alert.alert(
      'Block User',
      `Are you sure you want to block ${username}?`,
      [
        { text: 'Cancel', style: 'cancel' },
        { text: 'Block', style: 'destructive', onPress: performBlock },
      ]
    );
  };

  const handleUnblock = () => {
    Alert.alert(
      'Unblock User',
      `Are you sure you want to unblock ${username}?`,
      [
        { text: 'Cancel', style: 'cancel' },
        { text: 'Unblock', onPress: performUnblock },
      ]
    );
  };

  const performBlock = async () => {
    setLoading(true);
    try {
      const response = await blockUser(userId, 'block', 'User requested block');
      setIsBlocked(true);
      Alert.alert('Success', `Blocked ${username}`);
    } catch (error) {
      Alert.alert('Error', error.message);
    } finally {
      setLoading(false);
    }
  };

  const performUnblock = async () => {
    setLoading(true);
    try {
      const response = await unblockUser(userId);
      setIsBlocked(false);
      Alert.alert('Success', `Unblocked ${username}`);
    } catch (error) {
      Alert.alert('Error', error.message);
    } finally {
      setLoading(false);
    }
  };

  if (checking) {
    return (
      <TouchableOpacity style={[styles.button, styles.buttonDisabled, style]} disabled>
        <ActivityIndicator size="small" color="#666" />
      </TouchableOpacity>
    );
  }

  return (
    <TouchableOpacity
      style={[
        styles.button,
        isBlocked ? styles.buttonUnblock : styles.buttonBlock,
        style
      ]}
      onPress={isBlocked ? handleUnblock : handleBlock}
      disabled={loading}
    >
      {loading ? (
        <ActivityIndicator size="small" color="white" />
      ) : (
        <Text style={styles.buttonText}>
          {isBlocked ? '🚫 Unblock' : '🚫 Block'}
        </Text>
      )}
    </TouchableOpacity>
  );
};

const styles = {
  button: {
    paddingHorizontal: 15,
    paddingVertical: 8,
    borderRadius: 20,
    alignItems: 'center',
    justifyContent: 'center',
    minWidth: 100,
  },
  buttonBlock: {
    backgroundColor: '#F44336',
  },
  buttonUnblock: {
    backgroundColor: '#4CAF50',
  },
  buttonDisabled: {
    backgroundColor: '#ccc',
  },
  buttonText: {
    color: 'white',
    fontSize: 12,
    fontWeight: '500',
  },
};

export default BlockButton;
```

## Listener Verification System

### 1. Upload Verification Audio

**Business Purpose**: Allow listeners to upload audio samples for verification.

```typescript
// services/verificationService.ts
export interface ListenerVerificationResponse {
  sample_id: number;
  listener_id: number;
  audio_file_url: string;
  status: 'pending' | 'approved' | 'rejected';
  remarks: string | null;
  uploaded_at: string;
  reviewed_at: string | null;
}

export const uploadVerificationAudio = async (audioUri: string): Promise<ListenerVerificationResponse> => {
  try {
    const formData = new FormData();
    formData.append('audio_file', {
      uri: audioUri,
      type: 'audio/m4a',
      name: 'verification_audio.m4a',
    } as any);

    const response = await httpClient.post('/verification/upload-audio-file', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  } catch (error) {
    throw new Error(`Failed to upload verification audio: ${error.response?.data?.detail || error.message}`);
  }
};

export const getVerificationStatus = async (): Promise<{
  is_verified: boolean;
  verification_status: string | null;
  last_verification: ListenerVerificationResponse | null;
  message: string;
}> => {
  try {
    const response = await httpClient.get('/verification/status');
    return response.data;
  } catch (error) {
    throw new Error(`Failed to get verification status: ${error.response?.data?.detail || error.message}`);
  }
};
```

**React Native Component Example**:

```typescript
// components/VerificationScreen.tsx
import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  Alert,
  StyleSheet,
  Image,
} from 'react-native';
import { launchImageLibrary } from 'react-native-image-picker';
import { uploadVerificationAudio, getVerificationStatus } from '../services/verificationService';

const VerificationScreen = () => {
  const [verificationStatus, setVerificationStatus] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadVerificationStatus();
  }, []);

  const loadVerificationStatus = async () => {
    try {
      const status = await getVerificationStatus();
      setVerificationStatus(status);
    } catch (error) {
      console.error('Failed to load verification status:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSelectAudio = () => {
    const options = {
      mediaType: 'audio' as const,
      quality: 1,
    };

    launchImageLibrary(options, (response) => {
      if (response.didCancel || response.errorMessage) {
        return;
      }

      if (response.assets && response.assets[0]) {
        uploadAudio(response.assets[0].uri);
      }
    });
  };

  const uploadAudio = async (audioUri: string) => {
    setUploading(true);
    try {
      const result = await uploadVerificationAudio(audioUri);
      Alert.alert('Success', 'Verification audio uploaded successfully!');
      loadVerificationStatus(); // Refresh status
    } catch (error) {
      Alert.alert('Error', error.message);
    } finally {
      setUploading(false);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'approved': return '#4CAF50';
      case 'rejected': return '#F44336';
      case 'pending': return '#FF9800';
      default: return '#666';
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case 'approved': return 'Approved';
      case 'rejected': return 'Rejected';
      case 'pending': return 'Pending Review';
      default: return 'Not Verified';
    }
  };

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <Text>Loading verification status...</Text>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Listener Verification</Text>
      
      <View style={styles.statusCard}>
        <Text style={styles.statusLabel}>Verification Status</Text>
        <View style={styles.statusContainer}>
          <View style={[
            styles.statusDot,
            { backgroundColor: getStatusColor(verificationStatus?.verification_status || 'none') }
          ]} />
          <Text style={styles.statusText}>
            {getStatusText(verificationStatus?.verification_status || 'none')}
          </Text>
        </View>
        
        {verificationStatus?.message && (
          <Text style={styles.statusMessage}>
            {verificationStatus.message}
          </Text>
        )}
      </View>

      {verificationStatus?.last_verification && (
        <View style={styles.verificationCard}>
          <Text style={styles.cardTitle}>Last Verification</Text>
          <Text style={styles.uploadDate}>
            Uploaded: {new Date(verificationStatus.last_verification.uploaded_at).toLocaleString()}
          </Text>
          
          {verificationStatus.last_verification.reviewed_at && (
            <Text style={styles.reviewDate}>
              Reviewed: {new Date(verificationStatus.last_verification.reviewed_at).toLocaleString()}
            </Text>
          )}
          
          {verificationStatus.last_verification.remarks && (
            <Text style={styles.remarks}>
              Remarks: {verificationStatus.last_verification.remarks}
            </Text>
          )}
        </View>
      )}

      {verificationStatus?.verification_status !== 'approved' && (
        <TouchableOpacity
          style={[
            styles.uploadButton,
            uploading && styles.uploadButtonDisabled
          ]}
          onPress={handleSelectAudio}
          disabled={uploading}
        >
          <Text style={styles.uploadButtonText}>
            {uploading ? 'Uploading...' : 'Upload Verification Audio'}
          </Text>
        </TouchableOpacity>
      )}

      <View style={styles.infoCard}>
        <Text style={styles.infoTitle}>Verification Guidelines</Text>
        <Text style={styles.infoText}>
          • Record a clear audio sample of yourself speaking
        </Text>
        <Text style={styles.infoText}>
          • Speak naturally and clearly
        </Text>
        <Text style={styles.infoText}>
          • Keep the recording under 2 minutes
        </Text>
        <Text style={styles.infoText}>
          • Use good quality audio (no background noise)
        </Text>
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    padding: 20,
    backgroundColor: '#f5f5f5',
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    marginBottom: 20,
    textAlign: 'center',
  },
  statusCard: {
    backgroundColor: 'white',
    padding: 20,
    borderRadius: 10,
    marginBottom: 20,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  statusLabel: {
    fontSize: 16,
    fontWeight: '500',
    marginBottom: 10,
  },
  statusContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 10,
  },
  statusDot: {
    width: 12,
    height: 12,
    borderRadius: 6,
    marginRight: 8,
  },
  statusText: {
    fontSize: 18,
    fontWeight: 'bold',
  },
  statusMessage: {
    fontSize: 14,
    color: '#666',
  },
  verificationCard: {
    backgroundColor: 'white',
    padding: 15,
    borderRadius: 10,
    marginBottom: 20,
  },
  cardTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    marginBottom: 10,
  },
  uploadDate: {
    fontSize: 14,
    color: '#666',
    marginBottom: 5,
  },
  reviewDate: {
    fontSize: 14,
    color: '#666',
    marginBottom: 5,
  },
  remarks: {
    fontSize: 14,
    color: '#333',
    fontStyle: 'italic',
  },
  uploadButton: {
    backgroundColor: '#007AFF',
    padding: 15,
    borderRadius: 10,
    alignItems: 'center',
    marginBottom: 20,
  },
  uploadButtonDisabled: {
    backgroundColor: '#ccc',
  },
  uploadButtonText: {
    color: 'white',
    fontSize: 16,
    fontWeight: 'bold',
  },
  infoCard: {
    backgroundColor: 'white',
    padding: 15,
    borderRadius: 10,
  },
  infoTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    marginBottom: 10,
  },
  infoText: {
    fontSize: 14,
    color: '#666',
    marginBottom: 5,
  },
});

export default VerificationScreen;
```

This documentation covers the complete favorites, blocking, and verification systems for your React Native app. The examples show how to implement:

- **Favorites System**: Add/remove favorites, view favorites list with filtering
- **Blocking System**: Block/unblock users with confirmation dialogs
- **Verification System**: Upload audio samples for listener verification

Each feature includes proper error handling, loading states, and user feedback to provide a smooth user experience.

The complete React Native integration now covers all major features of the Saathii Backend API, providing developers with comprehensive examples and implementation patterns for building a full-featured calling and listening app.
