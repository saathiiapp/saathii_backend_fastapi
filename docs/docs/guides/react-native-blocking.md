---
sidebar_position: 7
title: React Native Blocking
description: Complete user blocking and safety features for React Native apps
---

# React Native Blocking

Complete guide for integrating user blocking, safety features, and content moderation into React Native applications.

## Overview

- **User Blocking**: Block and unblock users
- **Blocked Users List**: Manage blocked users
- **Block Status Checking**: Check if a user is blocked
- **Safety Features**: Report and moderation tools

## Blocking Service

### Blocking Service Implementation

```typescript
// services/BlockingService.ts
import ApiService from './ApiService';

export interface BlockedUser {
  user_id: number;
  username: string;
  sex: 'male' | 'female' | 'other';
  bio: string;
  profile_image_url?: string;
  blocked_at: string;
  reason?: string;
}

export interface BlockedUsersResponse {
  blocked_users: BlockedUser[];
  total_count: number;
  page: number;
  per_page: number;
  has_next: boolean;
  has_previous: boolean;
}

export interface BlockUserRequest {
  user_id: number;
  reason?: string;
}

export interface UnblockUserRequest {
  user_id: number;
}

export interface BlockActionResponse {
  success: boolean;
  message: string;
  user_id: number;
  is_blocked: boolean;
}

export interface BlockStatusResponse {
  is_blocked: boolean;
  blocked_at?: string;
  reason?: string;
}

class BlockingService {
  // Block user
  async blockUser(userId: number, reason?: string): Promise<BlockActionResponse> {
    return ApiService.post<BlockActionResponse>('/block', {
      user_id: userId,
      reason,
    });
  }

  // Unblock user
  async unblockUser(userId: number): Promise<BlockActionResponse> {
    return ApiService.delete<BlockActionResponse>('/block', {
      user_id: userId,
    });
  }

  // Get blocked users list
  async getBlockedUsers(page: number = 1, perPage: number = 20): Promise<BlockedUsersResponse> {
    return ApiService.get<BlockedUsersResponse>(`/blocked?page=${page}&per_page=${perPage}`);
  }

  // Check block status
  async checkBlockStatus(userId: number): Promise<BlockStatusResponse> {
    return ApiService.get<BlockStatusResponse>(`/block/check/${userId}`);
  }
}

export default new BlockingService();
```

## Blocking Screens

### Blocked Users Screen

```typescript
// screens/BlockedUsersScreen.tsx
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
import BlockingService, { BlockedUser } from '../services/BlockingService';
import BlockedUserCard from '../components/BlockedUserCard';

const BlockedUsersScreen: React.FC = () => {
  const [blockedUsers, setBlockedUsers] = useState<BlockedUser[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [loadingMore, setLoadingMore] = useState(false);
  const [page, setPage] = useState(1);
  const [hasNext, setHasNext] = useState(true);

  useEffect(() => {
    loadBlockedUsers(true);
  }, []);

  const loadBlockedUsers = async (reset: boolean = false) => {
    if (reset) {
      setPage(1);
      setIsLoading(true);
    } else {
      setLoadingMore(true);
    }

    try {
      const currentPage = reset ? 1 : page;
      const response = await BlockingService.getBlockedUsers(currentPage, 20);
      
      if (reset) {
        setBlockedUsers(response.blocked_users);
      } else {
        setBlockedUsers(prev => [...prev, ...response.blocked_users]);
      }
      
      setHasNext(response.has_next);
      setPage(currentPage + 1);
    } catch (error) {
      console.error('Failed to load blocked users:', error);
      Alert.alert('Error', 'Failed to load blocked users');
    } finally {
      setIsLoading(false);
      setLoadingMore(false);
    }
  };

  const handleRefresh = useCallback(() => {
    setRefreshing(true);
    loadBlockedUsers(true).finally(() => setRefreshing(false));
  }, []);

  const handleLoadMore = () => {
    if (!loadingMore && hasNext) {
      loadBlockedUsers(false);
    }
  };

  const handleUnblockUser = async (userId: number, username: string) => {
    Alert.alert(
      'Unblock User',
      `Are you sure you want to unblock ${username}?`,
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Unblock',
          style: 'default',
          onPress: async () => {
            try {
              await BlockingService.unblockUser(userId);
              setBlockedUsers(prev => prev.filter(user => user.user_id !== userId));
              Alert.alert('Success', 'User unblocked successfully');
            } catch (error) {
              Alert.alert('Error', 'Failed to unblock user');
            }
          },
        },
      ]
    );
  };

  const renderBlockedUser = ({ item }: { item: BlockedUser }) => (
    <BlockedUserCard
      blockedUser={item}
      onUnblock={() => handleUnblockUser(item.user_id, item.username)}
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
      <Text style={styles.emptyTitle}>No Blocked Users</Text>
      <Text style={styles.emptySubtitle}>
        Users you block will appear here
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
        <Text style={styles.title}>Blocked Users</Text>
        <Text style={styles.subtitle}>
          {blockedUsers.length} blocked user{blockedUsers.length !== 1 ? 's' : ''}
        </Text>
      </View>

      <FlatList
        data={blockedUsers}
        renderItem={renderBlockedUser}
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

export default BlockedUsersScreen;
```

### Blocked User Card Component

```typescript
// components/BlockedUserCard.tsx
import React from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  Image,
} from 'react-native';
import { BlockedUser } from '../services/BlockingService';

interface BlockedUserCardProps {
  blockedUser: BlockedUser;
  onUnblock: () => void;
}

const BlockedUserCard: React.FC<BlockedUserCardProps> = ({
  blockedUser,
  onUnblock,
}) => {
  const formatBlockedDate = (dateString: string) => {
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
          {blockedUser.profile_image_url ? (
            <Image
              source={{ uri: blockedUser.profile_image_url }}
              style={styles.profileImage}
            />
          ) : (
            <View style={styles.placeholderImage}>
              <Text style={styles.placeholderText}>
                {blockedUser.username.charAt(0).toUpperCase()}
              </Text>
            </View>
          )}
          
          <View style={styles.profileInfo}>
            <Text style={styles.username}>{blockedUser.username}</Text>
            <Text style={styles.blockedDate}>
              Blocked {formatBlockedDate(blockedUser.blocked_at)}
            </Text>
            {blockedUser.reason && (
              <Text style={styles.reason}>Reason: {blockedUser.reason}</Text>
            )}
          </View>
        </View>
        
        <View style={styles.statusContainer}>
          <Text style={styles.statusText}>🚫 Blocked</Text>
        </View>
      </View>

      <Text style={styles.bio} numberOfLines={2}>
        {blockedUser.bio}
      </Text>

      <View style={styles.actions}>
        <TouchableOpacity
          style={styles.unblockButton}
          onPress={onUnblock}
        >
          <Text style={styles.unblockButtonText}>Unblock User</Text>
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
    backgroundColor: '#FF3B30',
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
  blockedDate: {
    fontSize: 12,
    color: '#666',
    marginBottom: 2,
  },
  reason: {
    fontSize: 12,
    color: '#FF3B30',
    fontStyle: 'italic',
  },
  statusContainer: {
    alignItems: 'flex-end',
  },
  statusText: {
    fontSize: 12,
    color: '#FF3B30',
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
    justifyContent: 'center',
  },
  unblockButton: {
    backgroundColor: '#007AFF',
    paddingVertical: 10,
    paddingHorizontal: 20,
    borderRadius: 6,
  },
  unblockButtonText: {
    color: '#fff',
    fontSize: 14,
    fontWeight: 'bold',
  },
});

export default BlockedUserCard;
```

### Block User Component

```typescript
// components/BlockUserButton.tsx
import React, { useState, useEffect } from 'react';
import {
  TouchableOpacity,
  Text,
  StyleSheet,
  ActivityIndicator,
  Alert,
  Modal,
  View,
  TextInput,
} from 'react-native';
import BlockingService from '../services/BlockingService';

interface BlockUserButtonProps {
  userId: number;
  username: string;
  onBlockChange?: (isBlocked: boolean) => void;
}

const BlockUserButton: React.FC<BlockUserButtonProps> = ({
  userId,
  username,
  onBlockChange,
}) => {
  const [isBlocked, setIsBlocked] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [checkingStatus, setCheckingStatus] = useState(true);
  const [showBlockModal, setShowBlockModal] = useState(false);
  const [blockReason, setBlockReason] = useState('');

  useEffect(() => {
    checkBlockStatus();
  }, [userId]);

  const checkBlockStatus = async () => {
    try {
      const response = await BlockingService.checkBlockStatus(userId);
      setIsBlocked(response.is_blocked);
    } catch (error) {
      console.error('Failed to check block status:', error);
    } finally {
      setCheckingStatus(false);
    }
  };

  const handleBlockUser = () => {
    setShowBlockModal(true);
  };

  const handleUnblockUser = () => {
    Alert.alert(
      'Unblock User',
      `Are you sure you want to unblock ${username}?`,
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Unblock',
          style: 'default',
          onPress: confirmUnblock,
        },
      ]
    );
  };

  const confirmBlock = async () => {
    if (isLoading) return;

    setIsLoading(true);
    try {
      await BlockingService.blockUser(userId, blockReason || undefined);
      setIsBlocked(true);
      setShowBlockModal(false);
      setBlockReason('');
      Alert.alert('Blocked', `${username} has been blocked`);
      onBlockChange?.(true);
    } catch (error) {
      Alert.alert('Error', 'Failed to block user');
    } finally {
      setIsLoading(false);
    }
  };

  const confirmUnblock = async () => {
    if (isLoading) return;

    setIsLoading(true);
    try {
      await BlockingService.unblockUser(userId);
      setIsBlocked(false);
      Alert.alert('Unblocked', `${username} has been unblocked`);
      onBlockChange?.(false);
    } catch (error) {
      Alert.alert('Error', 'Failed to unblock user');
    } finally {
      setIsLoading(false);
    }
  };

  if (checkingStatus) {
    return (
      <TouchableOpacity style={[styles.button, styles.loadingButton]} disabled>
        <ActivityIndicator size="small" color="#FF3B30" />
      </TouchableOpacity>
    );
  }

  return (
    <>
      <TouchableOpacity
        style={[
          styles.button,
          isBlocked ? styles.unblockButton : styles.blockButton,
          isLoading && styles.loadingButton,
        ]}
        onPress={isBlocked ? handleUnblockUser : handleBlockUser}
        disabled={isLoading}
      >
        {isLoading ? (
          <ActivityIndicator size="small" color="#fff" />
        ) : (
          <Text style={styles.buttonText}>
            {isBlocked ? '🚫 Unblock' : '🚫 Block User'}
          </Text>
        )}
      </TouchableOpacity>

      <Modal
        visible={showBlockModal}
        animationType="slide"
        presentationStyle="pageSheet"
      >
        <View style={styles.modalContainer}>
          <View style={styles.modalHeader}>
            <TouchableOpacity onPress={() => setShowBlockModal(false)}>
              <Text style={styles.cancelButton}>Cancel</Text>
            </TouchableOpacity>
            <Text style={styles.modalTitle}>Block User</Text>
            <TouchableOpacity onPress={confirmBlock} disabled={isLoading}>
              <Text style={[styles.confirmButton, isLoading && styles.disabledButton]}>
                Block
              </Text>
            </TouchableOpacity>
          </View>

          <View style={styles.modalContent}>
            <Text style={styles.warningText}>
              Are you sure you want to block {username}?
            </Text>
            <Text style={styles.descriptionText}>
              Blocked users won't be able to see your profile or contact you.
            </Text>

            <Text style={styles.reasonLabel}>Reason (Optional)</Text>
            <TextInput
              style={styles.reasonInput}
              placeholder="Why are you blocking this user?"
              value={blockReason}
              onChangeText={setBlockReason}
              multiline
              numberOfLines={3}
            />
          </View>
        </View>
      </Modal>
    </>
  );
};

const styles = StyleSheet.create({
  button: {
    paddingHorizontal: 20,
    paddingVertical: 10,
    borderRadius: 20,
    alignItems: 'center',
    minWidth: 120,
  },
  blockButton: {
    backgroundColor: '#FF3B30',
  },
  unblockButton: {
    backgroundColor: '#007AFF',
  },
  loadingButton: {
    backgroundColor: '#ccc',
  },
  buttonText: {
    color: '#fff',
    fontSize: 14,
    fontWeight: 'bold',
  },
  modalContainer: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  modalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 15,
    backgroundColor: '#fff',
    borderBottomWidth: 1,
    borderBottomColor: '#eee',
  },
  modalTitle: {
    fontSize: 18,
    fontWeight: 'bold',
  },
  cancelButton: {
    fontSize: 16,
    color: '#007AFF',
  },
  confirmButton: {
    fontSize: 16,
    color: '#FF3B30',
    fontWeight: 'bold',
  },
  disabledButton: {
    color: '#ccc',
  },
  modalContent: {
    flex: 1,
    padding: 20,
  },
  warningText: {
    fontSize: 18,
    fontWeight: 'bold',
    marginBottom: 10,
    color: '#333',
  },
  descriptionText: {
    fontSize: 16,
    color: '#666',
    marginBottom: 20,
    lineHeight: 22,
  },
  reasonLabel: {
    fontSize: 16,
    fontWeight: 'bold',
    marginBottom: 10,
    color: '#333',
  },
  reasonInput: {
    borderWidth: 1,
    borderColor: '#ddd',
    borderRadius: 8,
    padding: 15,
    fontSize: 16,
    backgroundColor: '#fff',
    textAlignVertical: 'top',
  },
});

export default BlockUserButton;
```

### Blocking Context

```typescript
// contexts/BlockingContext.tsx
import React, { createContext, useContext, useState, useEffect } from 'react';
import BlockingService, { BlockedUser } from '../services/BlockingService';

interface BlockingContextType {
  blockedUsers: BlockedUser[];
  isLoading: boolean;
  blockUser: (userId: number, reason?: string) => Promise<void>;
  unblockUser: (userId: number) => Promise<void>;
  isBlocked: (userId: number) => boolean;
  refreshBlockedUsers: () => Promise<void>;
}

const BlockingContext = createContext<BlockingContextType | undefined>(undefined);

export const useBlocking = () => {
  const context = useContext(BlockingContext);
  if (!context) {
    throw new Error('useBlocking must be used within a BlockingProvider');
  }
  return context;
};

interface BlockingProviderProps {
  children: React.ReactNode;
}

export const BlockingProvider: React.FC<BlockingProviderProps> = ({ children }) => {
  const [blockedUsers, setBlockedUsers] = useState<BlockedUser[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  const loadBlockedUsers = async () => {
    setIsLoading(true);
    try {
      const response = await BlockingService.getBlockedUsers(1, 100);
      setBlockedUsers(response.blocked_users);
    } catch (error) {
      console.error('Failed to load blocked users:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const blockUser = async (userId: number, reason?: string) => {
    try {
      await BlockingService.blockUser(userId, reason);
      // Refresh blocked users list
      await loadBlockedUsers();
    } catch (error) {
      throw error;
    }
  };

  const unblockUser = async (userId: number) => {
    try {
      await BlockingService.unblockUser(userId);
      setBlockedUsers(prev => prev.filter(user => user.user_id !== userId));
    } catch (error) {
      throw error;
    }
  };

  const isBlocked = (userId: number): boolean => {
    return blockedUsers.some(user => user.user_id === userId);
  };

  const refreshBlockedUsers = async () => {
    await loadBlockedUsers();
  };

  useEffect(() => {
    loadBlockedUsers();
  }, []);

  const value: BlockingContextType = {
    blockedUsers,
    isLoading,
    blockUser,
    unblockUser,
    isBlocked,
    refreshBlockedUsers,
  };

  return (
    <BlockingContext.Provider value={value}>
      {children}
    </BlockingContext.Provider>
  );
};
```

## Integration Examples

### Using Blocking in User Profiles

```typescript
// components/UserProfileWithBlocking.tsx
import React from 'react';
import { View, StyleSheet } from 'react-native';
import UserProfile from './UserProfile';
import BlockUserButton from './BlockUserButton';
import { useBlocking } from '../contexts/BlockingContext';

interface UserProfileWithBlockingProps {
  user: any; // Your user type
  onBlockChange?: (isBlocked: boolean) => void;
}

const UserProfileWithBlocking: React.FC<UserProfileWithBlockingProps> = ({
  user,
  onBlockChange,
}) => {
  const { isBlocked } = useBlocking();

  const handleBlockChange = (isBlocked: boolean) => {
    onBlockChange?.(isBlocked);
  };

  // Don't show profile if user is blocked
  if (isBlocked(user.user_id)) {
    return (
      <View style={styles.blockedContainer}>
        <Text style={styles.blockedText}>This user is blocked</Text>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <UserProfile user={user} />
      <View style={styles.blockButton}>
        <BlockUserButton
          userId={user.user_id}
          username={user.username}
          onBlockChange={handleBlockChange}
        />
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    marginBottom: 10,
  },
  blockedContainer: {
    padding: 20,
    alignItems: 'center',
    backgroundColor: '#f5f5f5',
    borderRadius: 8,
  },
  blockedText: {
    fontSize: 16,
    color: '#666',
  },
  blockButton: {
    paddingHorizontal: 15,
    paddingBottom: 10,
    backgroundColor: '#fff',
    borderBottomLeftRadius: 8,
    borderBottomRightRadius: 8,
  },
});

export default UserProfileWithBlocking;
```

## Best Practices

### Blocking Management

1. **Check Status**: Always check block status before showing content
2. **Confirmation**: Require confirmation for blocking actions
3. **Reason Tracking**: Allow users to provide reasons for blocking
4. **Privacy**: Respect user privacy when blocking

### User Experience

1. **Clear Indicators**: Show clear visual indicators for blocked users
2. **Graceful Handling**: Handle blocked users gracefully in UI
3. **Easy Unblocking**: Make it easy to unblock users
4. **Safety First**: Prioritize user safety and comfort

### Performance

1. **Caching**: Cache block status for frequently accessed users
2. **Lazy Loading**: Load blocked users list as needed
3. **Efficient Filtering**: Filter out blocked users efficiently
4. **Real-time Updates**: Update UI when blocking status changes

## Next Steps

- Learn about [React Native WebSocket](./react-native-websocket)
- Explore [React Native Feeds](./react-native-feeds)
- Check out [React Native Favorites](./react-native-favorites)
