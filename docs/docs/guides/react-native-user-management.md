---
sidebar_position: 2
title: React Native User Management
description: Complete user profile and presence management for React Native apps
---

# React Native User Management

Complete guide for integrating user profile management and presence features into React Native applications.

## Overview

- **Profile Management**: Get, update, and delete user profiles
- **Presence System**: Real-time online/offline status tracking
- **Heartbeat System**: Keep users online with periodic heartbeats
- **Admin Functions**: Cleanup and management utilities

## User Service

### User Service Implementation

```typescript
// services/UserService.ts
import ApiService from './ApiService';

export interface User {
  user_id: number;
  phone: string;
  username: string;
  sex: 'male' | 'female' | 'other';
  dob: string;
  bio?: string;
  interests?: string[];
  profile_image_url?: string;
  preferred_language?: string;
  rating?: number;
  country?: string;
  roles?: string[];
  created_at: string;
  updated_at: string;
}

export interface EditUserRequest {
  username?: string;
  bio?: string;
  rating?: number;
  interests?: string[];
  profile_image_url?: string;
  preferred_language?: string;
}

export interface UserStatus {
  user_id: number;
  is_online: boolean;
  is_busy: boolean;
  last_seen: string;
  updated_at: string;
}

export interface UpdateStatusRequest {
  is_online?: boolean;
  is_busy?: boolean;
}

export interface UserPresence {
  user_id: number;
  username: string;
  is_online: boolean;
  is_busy: boolean;
  last_seen: string;
  profile_image_url?: string;
}

class UserService {
  // Get current user profile
  async getCurrentUser(): Promise<User> {
    return ApiService.get<User>('/users/me');
  }

  // Update current user profile
  async updateProfile(data: EditUserRequest): Promise<User> {
    return ApiService.put<User>('/users/me', data);
  }

  // Delete current user account
  async deleteAccount(): Promise<{ message: string }> {
    return ApiService.delete<{ message: string }>('/users/me');
  }

  // Get user status
  async getUserStatus(): Promise<UserStatus> {
    return ApiService.get<UserStatus>('/users/me/status');
  }

  // Update user status
  async updateStatus(data: UpdateStatusRequest): Promise<UserStatus> {
    return ApiService.put<UserStatus>('/users/me/status', data);
  }

  // Send heartbeat
  async sendHeartbeat(): Promise<{ message: string }> {
    return ApiService.post<{ message: string }>('/users/me/heartbeat');
  }


  // Admin: Cleanup presence
  async cleanupPresence(): Promise<{ message: string }> {
    return ApiService.post<{ message: string }>('/admin/cleanup-presence');
  }
}

export default new UserService();
```

## Profile Management Screens

### Profile Screen

```typescript
// screens/ProfileScreen.tsx
import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  StyleSheet,
  Alert,
  ActivityIndicator,
  ScrollView,
  Image,
} from 'react-native';
import { useAuth } from '../contexts/AuthContext';
import UserService, { User, EditUserRequest } from '../services/UserService';

const ProfileScreen: React.FC = () => {
  const { user, logout } = useAuth();
  const [profile, setProfile] = useState<User | null>(null);
  const [isEditing, setIsEditing] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [formData, setFormData] = useState<EditUserRequest>({});

  useEffect(() => {
    loadProfile();
  }, []);

  const loadProfile = async () => {
    try {
      const userProfile = await UserService.getCurrentUser();
      setProfile(userProfile);
    } catch (error) {
      Alert.alert('Error', 'Failed to load profile');
    }
  };

  const handleEdit = () => {
    if (profile) {
      setFormData({
        username: profile.username,
        bio: profile.bio || '',
        interests: profile.interests || [],
        profile_image_url: profile.profile_image_url || '',
        preferred_language: profile.preferred_language || 'en',
        country: profile.country || '',
      });
      setIsEditing(true);
    }
  };

  const handleSave = async () => {
    setIsLoading(true);
    try {
      const updatedProfile = await UserService.updateProfile(formData);
      setProfile(updatedProfile);
      setIsEditing(false);
      Alert.alert('Success', 'Profile updated successfully');
    } catch (error) {
      Alert.alert('Error', 'Failed to update profile');
    } finally {
      setIsLoading(false);
    }
  };

  const handleCancel = () => {
    setIsEditing(false);
    setFormData({});
  };

  const handleDeleteAccount = () => {
    Alert.alert(
      'Delete Account',
      'Are you sure you want to delete your account? This action cannot be undone.',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Delete',
          style: 'destructive',
          onPress: confirmDeleteAccount,
        },
      ]
    );
  };

  const confirmDeleteAccount = async () => {
    setIsLoading(true);
    try {
      await UserService.deleteAccount();
      await logout();
    } catch (error) {
      Alert.alert('Error', 'Failed to delete account');
    } finally {
      setIsLoading(false);
    }
  };

  if (!profile) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#007AFF" />
      </View>
    );
  }

  return (
    <ScrollView style={styles.container}>
      <View style={styles.header}>
        {profile.profile_image_url ? (
          <Image
            source={{ uri: profile.profile_image_url }}
            style={styles.profileImage}
          />
        ) : (
          <View style={styles.placeholderImage}>
            <Text style={styles.placeholderText}>
              {profile.username.charAt(0).toUpperCase()}
            </Text>
          </View>
        )}
        
        <Text style={styles.username}>{profile.username}</Text>
        <Text style={styles.phone}>{profile.phone}</Text>
        
        {profile.rating && (
          <View style={styles.ratingContainer}>
            <Text style={styles.rating}>⭐ {profile.rating.toFixed(1)}</Text>
          </View>
        )}
      </View>

      <View style={styles.content}>
        {isEditing ? (
          <View style={styles.editForm}>
            <Text style={styles.sectionTitle}>Edit Profile</Text>
            
            <TextInput
              style={styles.input}
              placeholder="Username"
              value={formData.username || ''}
              onChangeText={(text) => setFormData({ ...formData, username: text })}
            />
            
            <TextInput
              style={[styles.input, styles.textArea]}
              placeholder="Bio"
              value={formData.bio || ''}
              onChangeText={(text) => setFormData({ ...formData, bio: text })}
              multiline
              numberOfLines={3}
            />
            
            <TextInput
              style={styles.input}
              placeholder="Profile Image URL"
              value={formData.profile_image_url || ''}
              onChangeText={(text) => setFormData({ ...formData, profile_image_url: text })}
            />
            
            <TextInput
              style={styles.input}
              placeholder="Country"
              value={formData.country || ''}
              onChangeText={(text) => setFormData({ ...formData, country: text })}
            />
            
            <View style={styles.buttonRow}>
              <TouchableOpacity
                style={[styles.button, styles.cancelButton]}
                onPress={handleCancel}
              >
                <Text style={styles.cancelButtonText}>Cancel</Text>
              </TouchableOpacity>
              
              <TouchableOpacity
                style={[styles.button, styles.saveButton]}
                onPress={handleSave}
                disabled={isLoading}
              >
                {isLoading ? (
                  <ActivityIndicator color="#fff" />
                ) : (
                  <Text style={styles.saveButtonText}>Save</Text>
                )}
              </TouchableOpacity>
            </View>
          </View>
        ) : (
          <View style={styles.profileInfo}>
            <View style={styles.infoRow}>
              <Text style={styles.label}>Bio:</Text>
              <Text style={styles.value}>{profile.bio || 'No bio provided'}</Text>
            </View>
            
            <View style={styles.infoRow}>
              <Text style={styles.label}>Interests:</Text>
              <Text style={styles.value}>
                {profile.interests?.join(', ') || 'No interests listed'}
              </Text>
            </View>
            
            <View style={styles.infoRow}>
              <Text style={styles.label}>Language:</Text>
              <Text style={styles.value}>{profile.preferred_language || 'English'}</Text>
            </View>
            
            <View style={styles.infoRow}>
              <Text style={styles.label}>Country:</Text>
              <Text style={styles.value}>{profile.country || 'Not specified'}</Text>
            </View>
            
            <View style={styles.infoRow}>
              <Text style={styles.label}>Member since:</Text>
              <Text style={styles.value}>
                {new Date(profile.created_at).toLocaleDateString()}
              </Text>
            </View>
            
            <TouchableOpacity
              style={styles.editButton}
              onPress={handleEdit}
            >
              <Text style={styles.editButtonText}>Edit Profile</Text>
            </TouchableOpacity>
          </View>
        )}
      </View>

      <TouchableOpacity
        style={styles.deleteButton}
        onPress={handleDeleteAccount}
        disabled={isLoading}
      >
        <Text style={styles.deleteButtonText}>Delete Account</Text>
      </TouchableOpacity>
    </ScrollView>
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
    alignItems: 'center',
    borderBottomWidth: 1,
    borderBottomColor: '#eee',
  },
  profileImage: {
    width: 100,
    height: 100,
    borderRadius: 50,
    marginBottom: 10,
  },
  placeholderImage: {
    width: 100,
    height: 100,
    borderRadius: 50,
    backgroundColor: '#007AFF',
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 10,
  },
  placeholderText: {
    color: '#fff',
    fontSize: 36,
    fontWeight: 'bold',
  },
  username: {
    fontSize: 24,
    fontWeight: 'bold',
    marginBottom: 5,
  },
  phone: {
    fontSize: 16,
    color: '#666',
    marginBottom: 10,
  },
  ratingContainer: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  rating: {
    fontSize: 16,
    color: '#FFD700',
  },
  content: {
    padding: 20,
  },
  sectionTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    marginBottom: 15,
  },
  editForm: {
    backgroundColor: '#fff',
    padding: 15,
    borderRadius: 8,
    marginBottom: 20,
  },
  input: {
    borderWidth: 1,
    borderColor: '#ddd',
    borderRadius: 8,
    padding: 12,
    fontSize: 16,
    marginBottom: 15,
    backgroundColor: '#f9f9f9',
  },
  textArea: {
    height: 80,
    textAlignVertical: 'top',
  },
  buttonRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  button: {
    padding: 12,
    borderRadius: 8,
    flex: 1,
    marginHorizontal: 5,
    alignItems: 'center',
  },
  cancelButton: {
    backgroundColor: '#f0f0f0',
  },
  saveButton: {
    backgroundColor: '#007AFF',
  },
  cancelButtonText: {
    color: '#333',
    fontWeight: 'bold',
  },
  saveButtonText: {
    color: '#fff',
    fontWeight: 'bold',
  },
  profileInfo: {
    backgroundColor: '#fff',
    padding: 15,
    borderRadius: 8,
    marginBottom: 20,
  },
  infoRow: {
    flexDirection: 'row',
    marginBottom: 10,
  },
  label: {
    fontWeight: 'bold',
    width: 100,
    color: '#333',
  },
  value: {
    flex: 1,
    color: '#666',
  },
  editButton: {
    backgroundColor: '#007AFF',
    padding: 12,
    borderRadius: 8,
    alignItems: 'center',
    marginTop: 10,
  },
  editButtonText: {
    color: '#fff',
    fontWeight: 'bold',
  },
  deleteButton: {
    backgroundColor: '#FF3B30',
    padding: 15,
    margin: 20,
    borderRadius: 8,
    alignItems: 'center',
  },
  deleteButtonText: {
    color: '#fff',
    fontWeight: 'bold',
  },
});

export default ProfileScreen;
```

## Presence Management

### Presence Service

```typescript
// services/PresenceService.ts
import UserService from './UserService';

export interface PresenceStatus {
  is_online: boolean;
  is_busy: boolean;
  last_seen: string;
}

class PresenceService {
  private heartbeatInterval: NodeJS.Timeout | null = null;
  private isHeartbeatActive = false;

  // Start heartbeat to keep user online
  startHeartbeat(intervalMs: number = 30000) {
    if (this.isHeartbeatActive) return;

    this.isHeartbeatActive = true;
    this.heartbeatInterval = setInterval(async () => {
      try {
        await UserService.sendHeartbeat();
      } catch (error) {
        console.error('Heartbeat failed:', error);
      }
    }, intervalMs);
  }

  // Stop heartbeat
  stopHeartbeat() {
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval);
      this.heartbeatInterval = null;
    }
    this.isHeartbeatActive = false;
  }

  // Update user status
  async updateStatus(isOnline: boolean, isBusy: boolean = false) {
    return UserService.updateStatus({
      is_online: isOnline,
      is_busy: isBusy,
    });
  }

  // Get user status
  async getStatus() {
    return UserService.getUserStatus();
  }

  // Get presence for specific user
  async getUserPresence(userId: number) {
    return UserService.getUserPresence(userId);
  }

  // Get presence for multiple users
  async getMultipleUsersPresence(userIds: number[]) {
    return UserService.getMultipleUsersPresence(userIds);
  }
}

export default new PresenceService();
```

### Presence Hook

```typescript
// hooks/usePresence.ts
import { useState, useEffect, useCallback } from 'react';
import { AppState, AppStateStatus } from 'react-native';
import PresenceService, { PresenceStatus } from '../services/PresenceService';

export const usePresence = () => {
  const [status, setStatus] = useState<PresenceStatus | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const loadStatus = useCallback(async () => {
    setIsLoading(true);
    try {
      const userStatus = await PresenceService.getStatus();
      setStatus(userStatus);
    } catch (error) {
      console.error('Failed to load status:', error);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const updateStatus = useCallback(async (isOnline: boolean, isBusy: boolean = false) => {
    try {
      const newStatus = await PresenceService.updateStatus(isOnline, isBusy);
      setStatus(newStatus);
    } catch (error) {
      console.error('Failed to update status:', error);
    }
  }, []);

  const goOnline = useCallback(() => {
    updateStatus(true, false);
    PresenceService.startHeartbeat();
  }, [updateStatus]);

  const goOffline = useCallback(() => {
    updateStatus(false, false);
    PresenceService.stopHeartbeat();
  }, [updateStatus]);

  const setBusy = useCallback((isBusy: boolean) => {
    if (status) {
      updateStatus(status.is_online, isBusy);
    }
  }, [status, updateStatus]);

  useEffect(() => {
    loadStatus();
  }, [loadStatus]);

  useEffect(() => {
    const handleAppStateChange = (nextAppState: AppStateStatus) => {
      if (nextAppState === 'active') {
        goOnline();
      } else if (nextAppState === 'background') {
        goOffline();
      }
    };

    const subscription = AppState.addEventListener('change', handleAppStateChange);

    return () => {
      subscription?.remove();
      PresenceService.stopHeartbeat();
    };
  }, [goOnline, goOffline]);

  return {
    status,
    isLoading,
    goOnline,
    goOffline,
    setBusy,
    updateStatus,
    refreshStatus: loadStatus,
  };
};
```

### Status Indicator Component

```typescript
// components/StatusIndicator.tsx
import React from 'react';
import { View, Text, StyleSheet } from 'react-native';

interface StatusIndicatorProps {
  isOnline: boolean;
  isBusy: boolean;
  size?: 'small' | 'medium' | 'large';
}

const StatusIndicator: React.FC<StatusIndicatorProps> = ({
  isOnline,
  isBusy,
  size = 'medium',
}) => {
  const getStatusColor = () => {
    if (!isOnline) return '#999';
    if (isBusy) return '#FF9500';
    return '#34C759';
  };

  const getStatusText = () => {
    if (!isOnline) return 'Offline';
    if (isBusy) return 'Busy';
    return 'Online';
  };

  const getSizeStyles = () => {
    switch (size) {
      case 'small':
        return { width: 8, height: 8, fontSize: 10 };
      case 'large':
        return { width: 16, height: 16, fontSize: 14 };
      default:
        return { width: 12, height: 12, fontSize: 12 };
    }
  };

  const sizeStyles = getSizeStyles();

  return (
    <View style={styles.container}>
      <View
        style={[
          styles.indicator,
          {
            backgroundColor: getStatusColor(),
            width: sizeStyles.width,
            height: sizeStyles.height,
          },
        ]}
      />
      <Text style={[styles.text, { fontSize: sizeStyles.fontSize }]}>
        {getStatusText()}
      </Text>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  indicator: {
    borderRadius: 50,
    marginRight: 6,
  },
  text: {
    color: '#666',
    fontWeight: '500',
  },
});

export default StatusIndicator;
```

## Best Practices

### Profile Management

1. **Form Validation**: Validate all form inputs before submission
2. **Image Handling**: Implement proper image upload and caching
3. **Error Handling**: Provide clear error messages for validation failures
4. **Loading States**: Show loading indicators during operations

### Presence Management

1. **Heartbeat Timing**: Use appropriate heartbeat intervals (30-60 seconds)
2. **App State Handling**: Handle app background/foreground transitions
3. **Network Awareness**: Handle network connectivity changes
4. **Battery Optimization**: Consider battery impact of frequent heartbeats

### Performance

1. **Caching**: Cache user profiles and status locally
2. **Optimistic Updates**: Update UI immediately, handle errors gracefully
3. **Debouncing**: Debounce rapid status changes
4. **Memory Management**: Clean up intervals and listeners properly

## Next Steps

- Learn about [React Native Wallets](./react-native-wallets)
- Explore [React Native Feeds](./react-native-feeds)
- Check out [React Native Calls](./react-native-calls)
