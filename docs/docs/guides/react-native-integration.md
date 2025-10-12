---
sidebar_position: 1
title: React Native Integration
description: Complete guide for integrating the Saathii Backend API with React Native apps
---

# React Native Integration Guide

This guide provides a comprehensive walkthrough for integrating the Saathii Backend API with React Native applications, including authentication, real-time updates, and call management.

## Prerequisites

- React Native development environment set up
- Node.js 16+ installed
- Android Studio / Xcode configured
- Saathii Backend API running locally or deployed

## Dependencies

Install the required dependencies:

```bash
# Core dependencies
npm install axios @react-native-async-storage/async-storage

# For Expo projects
expo install @react-native-async-storage/async-storage

# Optional: for secure storage
npm install expo-secure-store
# or
expo install expo-secure-store
```

## Project Structure

```
src/
├── api/
│   ├── client.ts          # API client configuration
│   ├── auth.ts           # Authentication API calls
│   ├── user.ts           # User management API calls
│   ├── calls.ts          # Call management API calls
│   └── websocket.ts      # WebSocket integration
├── hooks/
│   ├── useAuth.ts        # Authentication hook
│   ├── useWebSocket.ts   # WebSocket hook
│   └── useCalls.ts       # Call management hook
├── screens/
│   ├── LoginScreen.tsx   # Login/OTP screen
│   ├── RegisterScreen.tsx # Registration screen
│   ├── FeedScreen.tsx    # Feed screen
│   └── CallScreen.tsx    # Call screen
├── components/
│   ├── UserCard.tsx      # User card component
│   └── StatusIndicator.tsx # Status indicator
└── utils/
    ├── storage.ts        # Storage utilities
    └── validation.ts     # Input validation
```

## API Client Setup

### 1. Create API Client

```typescript
// src/api/client.ts
import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse } from 'axios';
import AsyncStorage from '@react-native-async-storage/async-storage';

class ApiClient {
  private client: AxiosInstance;
  private baseURL: string;
  private accessToken: string | null = null;
  private refreshToken: string | null = null;
  private isRefreshing = false;
  private failedQueue: Array<{
    resolve: (value: any) => void;
    reject: (error: any) => void;
  }> = [];

  constructor(baseURL: string = 'https://saathiiapp.com') {
    this.baseURL = baseURL;
    this.client = axios.create({
      baseURL,
      timeout: 10000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    this.setupInterceptors();
  }

  private setupInterceptors() {
    // Request interceptor
    this.client.interceptors.request.use(
      async (config) => {
        if (this.accessToken) {
          config.headers.Authorization = `Bearer ${this.accessToken}`;
        }
        return config;
      },
      (error) => Promise.reject(error)
    );

    // Response interceptor
    this.client.interceptors.response.use(
      (response) => response,
      async (error) => {
        const originalRequest = error.config;

        if (error.response?.status === 401 && !originalRequest._retry) {
          if (this.isRefreshing) {
            return new Promise((resolve, reject) => {
              this.failedQueue.push({ resolve, reject });
            }).then((token) => {
              originalRequest.headers.Authorization = `Bearer ${token}`;
              return this.client(originalRequest);
            });
          }

          originalRequest._retry = true;
          this.isRefreshing = true;

          try {
            const newTokens = await this.refreshAccessToken();
            this.processQueue(null, newTokens.access_token);
            originalRequest.headers.Authorization = `Bearer ${newTokens.access_token}`;
            return this.client(originalRequest);
          } catch (refreshError) {
            this.processQueue(refreshError, null);
            await this.logout();
            return Promise.reject(refreshError);
          } finally {
            this.isRefreshing = false;
          }
        }

        return Promise.reject(error);
      }
    );
  }

  private processQueue(error: any, token: string | null) {
    this.failedQueue.forEach(({ resolve, reject }) => {
      if (error) {
        reject(error);
      } else {
        resolve(token);
      }
    });

    this.failedQueue = [];
  }

  private async refreshAccessToken() {
    if (!this.refreshToken) {
      throw new Error('No refresh token available');
    }

    const response = await this.client.post('/auth/refresh', {
      refresh_token: this.refreshToken,
    });

    const { access_token, refresh_token } = response.data;
    await this.setTokens(access_token, refresh_token);
    return { access_token, refresh_token };
  }

  async setTokens(accessToken: string, refreshToken: string) {
    this.accessToken = accessToken;
    this.refreshToken = refreshToken;
    
    await AsyncStorage.setItem('access_token', accessToken);
    await AsyncStorage.setItem('refresh_token', refreshToken);
  }

  async loadTokens() {
    try {
      const accessToken = await AsyncStorage.getItem('access_token');
      const refreshToken = await AsyncStorage.getItem('refresh_token');
      
      if (accessToken && refreshToken) {
        this.accessToken = accessToken;
        this.refreshToken = refreshToken;
        return true;
      }
      return false;
    } catch (error) {
      console.error('Error loading tokens:', error);
      return false;
    }
  }

  async logout() {
    this.accessToken = null;
    this.refreshToken = null;
    
    await AsyncStorage.removeItem('access_token');
    await AsyncStorage.removeItem('refresh_token');
  }

  // Generic request method
  async request<T>(config: AxiosRequestConfig): Promise<T> {
    const response: AxiosResponse<T> = await this.client(config);
    return response.data;
  }

  // HTTP methods
  async get<T>(url: string, config?: AxiosRequestConfig): Promise<T> {
    return this.request<T>({ ...config, method: 'GET', url });
  }

  async post<T>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    return this.request<T>({ ...config, method: 'POST', url, data });
  }

  async put<T>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    return this.request<T>({ ...config, method: 'PUT', url, data });
  }

  async delete<T>(url: string, config?: AxiosRequestConfig): Promise<T> {
    return this.request<T>({ ...config, method: 'DELETE', url });
  }
}

export const apiClient = new ApiClient('https://saathiiapp.com');
export default apiClient;
```

### 2. Authentication API

```typescript
// src/api/auth.ts
import apiClient from './client';

export interface RequestOTPRequest {
  phone: string;
}

export interface VerifyOTPRequest {
  phone: string;
  otp: string;
}

export interface RegisterUserRequest {
  registration_token: string;
  username: string;
  sex: 'male' | 'female' | 'other';
  dob: string;
  bio?: string;
  interests?: string[];
  profile_image_url?: string;
  preferred_language?: string;
  role: 'listener' | 'user';
}

export interface AuthResponse {
  access_token: string;
  refresh_token: string;
}

export interface VerifyOTPResponse {
  status: 'registered' | 'needs_registration';
  access_token?: string;
  refresh_token?: string;
  registration_token?: string;
}

export const authAPI = {
  // Request OTP
  requestOTP: (data: RequestOTPRequest) =>
    apiClient.post<{ message: string }>('/auth/request_otp', data),

  // Resend OTP
  resendOTP: (data: RequestOTPRequest) =>
    apiClient.post<{ message: string }>('/auth/resend_otp', data),

  // Verify OTP
  verifyOTP: (data: VerifyOTPRequest) =>
    apiClient.post<VerifyOTPResponse>('/auth/verify', data),

  // Register user
  registerUser: (data: RegisterUserRequest) =>
    apiClient.post<AuthResponse>('/auth/register', data),

  // Refresh token
  refreshToken: (refreshToken: string) =>
    apiClient.post<AuthResponse>('/auth/refresh', { refresh_token: refreshToken }),

  // Logout
  logout: () =>
    apiClient.post<{ message: string }>('/auth/logout'),
};
```

### 3. User Management API

```typescript
// src/api/user.ts
import apiClient from './client';

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
  roles: string[];
  created_at: string;
  updated_at: string;
}

export interface UserStatus {
  user_id: number;
  is_online: boolean;
  last_seen: string;
  is_busy: boolean;
  busy_until?: string;
  is_available: boolean;
}

export interface UpdateUserRequest {
  username?: string;
  bio?: string;
  rating?: number;
  interests?: string[];
  profile_image_url?: string;
  preferred_language?: string;
  country?: string;
}

export interface UpdateStatusRequest {
  is_online?: boolean;
  is_busy?: boolean;
  busy_until?: string;
}

export const userAPI = {
  // Get current user
  getCurrentUser: () =>
    apiClient.get<User>('/users/me'),

  // Update current user
  updateCurrentUser: (data: UpdateUserRequest) =>
    apiClient.put<User>('/users/me', data),

  // Delete current user
  deleteCurrentUser: () =>
    apiClient.delete<{ message: string }>('/users/me'),

  // Get user status
  getUserStatus: () =>
    apiClient.get<UserStatus>('/users/me/status'),

  // Update user status
  updateUserStatus: (data: UpdateStatusRequest) =>
    apiClient.put<UserStatus>('/users/me/status', data),

  // Send heartbeat
  sendHeartbeat: () =>
    apiClient.post<{ message: string; last_seen: string }>('/users/me/heartbeat'),

  // Get user presence
  getUserPresence: (userId: number) =>
    apiClient.get<UserStatus>(`/users/${userId}/presence`),

  // Get multiple users presence
  getUsersPresence: (userIds: number[]) =>
    apiClient.get<UserStatus[]>('/users/presence', {
      params: { user_ids: userIds.join(',') },
    }),
};
```

## Authentication Hook

```typescript
// src/hooks/useAuth.ts
import { useState, useEffect, useCallback } from 'react';
import { authAPI, AuthResponse, VerifyOTPResponse } from '../api/auth';
import apiClient from '../api/client';

export interface AuthState {
  isAuthenticated: boolean;
  isLoading: boolean;
  user: any | null;
  error: string | null;
}

export const useAuth = () => {
  const [authState, setAuthState] = useState<AuthState>({
    isAuthenticated: false,
    isLoading: true,
    user: null,
    error: null,
  });

  // Check if user is already authenticated
  useEffect(() => {
    const checkAuth = async () => {
      try {
        const hasTokens = await apiClient.loadTokens();
        if (hasTokens) {
          // Try to get current user to validate token
          const user = await userAPI.getCurrentUser();
          setAuthState({
            isAuthenticated: true,
            isLoading: false,
            user,
            error: null,
          });
        } else {
          setAuthState(prev => ({ ...prev, isLoading: false }));
        }
      } catch (error) {
        console.error('Auth check failed:', error);
        setAuthState({
          isAuthenticated: false,
          isLoading: false,
          user: null,
          error: 'Authentication failed',
        });
      }
    };

    checkAuth();
  }, []);

  const requestOTP = useCallback(async (phone: string) => {
    try {
      setAuthState(prev => ({ ...prev, isLoading: true, error: null }));
      const response = await authAPI.requestOTP({ phone });
      return response;
    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || 'Failed to request OTP';
      setAuthState(prev => ({ ...prev, error: errorMessage }));
      throw error;
    } finally {
      setAuthState(prev => ({ ...prev, isLoading: false }));
    }
  }, []);

  const verifyOTP = useCallback(async (phone: string, otp: string) => {
    try {
      setAuthState(prev => ({ ...prev, isLoading: true, error: null }));
      const response = await authAPI.verifyOTP({ phone, otp });
      
      if (response.status === 'registered') {
        // User is already registered
        await apiClient.setTokens(response.access_token!, response.refresh_token!);
        const user = await userAPI.getCurrentUser();
        setAuthState({
          isAuthenticated: true,
          isLoading: false,
          user,
          error: null,
        });
        return { needsRegistration: false };
      } else {
        // User needs to register
        setAuthState(prev => ({ ...prev, isLoading: false }));
        return { needsRegistration: true, registrationToken: response.registration_token };
      }
    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || 'Failed to verify OTP';
      setAuthState(prev => ({ ...prev, error: errorMessage }));
      throw error;
    }
  }, []);

  const registerUser = useCallback(async (registrationData: any) => {
    try {
      setAuthState(prev => ({ ...prev, isLoading: true, error: null }));
      const response = await authAPI.registerUser(registrationData);
      await apiClient.setTokens(response.access_token, response.refresh_token);
      const user = await userAPI.getCurrentUser();
      setAuthState({
        isAuthenticated: true,
        isLoading: false,
        user,
        error: null,
      });
      return response;
    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || 'Failed to register user';
      setAuthState(prev => ({ ...prev, error: errorMessage }));
      throw error;
    }
  }, []);

  const logout = useCallback(async () => {
    try {
      await authAPI.logout();
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      await apiClient.logout();
      setAuthState({
        isAuthenticated: false,
        isLoading: false,
        user: null,
        error: null,
      });
    }
  }, []);

  return {
    ...authState,
    requestOTP,
    verifyOTP,
    registerUser,
    logout,
  };
};
```

## WebSocket Integration

```typescript
// src/hooks/useWebSocket.ts
import { useEffect, useRef, useState, useCallback } from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';

export interface WebSocketMessage {
  type: string;
  user_id?: number;
  status?: any;
  message?: string;
  timestamp?: string;
}

export interface UseWebSocketProps {
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
  reconnectInterval = 5000,
}: UseWebSocketProps) => {
  const [isConnected, setIsConnected] = useState(false);
  const [connectionError, setConnectionError] = useState<string | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const reconnectAttempts = useRef(0);
  const maxReconnectAttempts = 5;

  const connect = useCallback(async () => {
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
        reconnectAttempts.current = 0;
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
        onDisconnect?.(event);
        
        // Attempt to reconnect if not a clean close
        if (event.code !== 1000 && reconnectAttempts.current < maxReconnectAttempts) {
          reconnectAttempts.current++;
          reconnectTimeoutRef.current = setTimeout(() => {
            console.log(`Attempting to reconnect... (${reconnectAttempts.current}/${maxReconnectAttempts})`);
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
  }, [url, onMessage, onConnect, onDisconnect, reconnectInterval]);

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }
    if (wsRef.current) {
      wsRef.current.close(1000, 'User disconnected');
      wsRef.current = null;
    }
    setIsConnected(false);
  }, []);

  const sendMessage = useCallback((message: any) => {
    if (wsRef.current && isConnected) {
      wsRef.current.send(JSON.stringify(message));
    }
  }, [isConnected]);

  const ping = useCallback(() => {
    sendMessage({
      type: 'ping',
      timestamp: new Date().toISOString(),
    });
  }, [sendMessage]);

  useEffect(() => {
    connect();
    
    return () => {
      disconnect();
    };
  }, [connect, disconnect]);

  return {
    isConnected,
    connectionError,
    connect,
    disconnect,
    sendMessage,
    ping,
  };
};
```

## Screen Components

### 1. Login Screen

```typescript
// src/screens/LoginScreen.tsx
import React, { useState } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  StyleSheet,
  Alert,
  ActivityIndicator,
} from 'react-native';
import { useAuth } from '../hooks/useAuth';

export const LoginScreen = ({ navigation }: any) => {
  const [phone, setPhone] = useState('');
  const [otp, setOtp] = useState('');
  const [step, setStep] = useState<'phone' | 'otp'>('phone');
  const { requestOTP, verifyOTP, isLoading, error } = useAuth();

  const handleRequestOTP = async () => {
    if (!phone.trim()) {
      Alert.alert('Error', 'Please enter a phone number');
      return;
    }

    try {
      await requestOTP(phone);
      setStep('otp');
      Alert.alert('Success', 'OTP sent successfully');
    } catch (error: any) {
      Alert.alert('Error', error.message || 'Failed to send OTP');
    }
  };

  const handleVerifyOTP = async () => {
    if (!otp.trim()) {
      Alert.alert('Error', 'Please enter the OTP');
      return;
    }

    try {
      const result = await verifyOTP(phone, otp);
      if (result.needsRegistration) {
        navigation.navigate('Register', { registrationToken: result.registrationToken });
      } else {
        navigation.navigate('Feed');
      }
    } catch (error: any) {
      Alert.alert('Error', error.message || 'Failed to verify OTP');
    }
  };

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Welcome to Saathii</Text>
      
      {step === 'phone' ? (
        <View style={styles.form}>
          <TextInput
            style={styles.input}
            placeholder="Enter phone number"
            value={phone}
            onChangeText={setPhone}
            keyboardType="phone-pad"
            autoFocus
          />
          <TouchableOpacity
            style={styles.button}
            onPress={handleRequestOTP}
            disabled={isLoading}
          >
            {isLoading ? (
              <ActivityIndicator color="white" />
            ) : (
              <Text style={styles.buttonText}>Send OTP</Text>
            )}
          </TouchableOpacity>
        </View>
      ) : (
        <View style={styles.form}>
          <TextInput
            style={styles.input}
            placeholder="Enter OTP"
            value={otp}
            onChangeText={setOtp}
            keyboardType="number-pad"
            autoFocus
          />
          <TouchableOpacity
            style={styles.button}
            onPress={handleVerifyOTP}
            disabled={isLoading}
          >
            {isLoading ? (
              <ActivityIndicator color="white" />
            ) : (
              <Text style={styles.buttonText}>Verify OTP</Text>
            )}
          </TouchableOpacity>
          <TouchableOpacity
            style={styles.linkButton}
            onPress={() => setStep('phone')}
          >
            <Text style={styles.linkText}>Change phone number</Text>
          </TouchableOpacity>
        </View>
      )}

      {error && <Text style={styles.errorText}>{error}</Text>}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    justifyContent: 'center',
    padding: 20,
    backgroundColor: '#f5f5f5',
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    textAlign: 'center',
    marginBottom: 40,
    color: '#333',
  },
  form: {
    width: '100%',
  },
  input: {
    borderWidth: 1,
    borderColor: '#ddd',
    borderRadius: 8,
    padding: 15,
    marginBottom: 20,
    fontSize: 16,
    backgroundColor: 'white',
  },
  button: {
    backgroundColor: '#007AFF',
    padding: 15,
    borderRadius: 8,
    alignItems: 'center',
    marginBottom: 10,
  },
  buttonText: {
    color: 'white',
    fontSize: 16,
    fontWeight: 'bold',
  },
  linkButton: {
    alignItems: 'center',
    padding: 10,
  },
  linkText: {
    color: '#007AFF',
    fontSize: 14,
  },
  errorText: {
    color: 'red',
    textAlign: 'center',
    marginTop: 10,
  },
});
```

### 2. Feed Screen with Real-time Updates

```typescript
// src/screens/FeedScreen.tsx
import React, { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  FlatList,
  RefreshControl,
  StyleSheet,
  TouchableOpacity,
} from 'react-native';
import { useWebSocket } from '../hooks/useWebSocket';
import { userAPI } from '../api/user';

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

export const FeedScreen = ({ navigation }: any) => {
  const [listeners, setListeners] = useState<Listener[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [feedStats, setFeedStats] = useState({
    total_count: 0,
    online_count: 0,
    available_count: 0,
  });

  // WebSocket for real-time updates
  const { isConnected, connectionError, ping } = useWebSocket({
    url: 'wss://saathiiapp.com/ws/feed',
    onMessage: handleWebSocketMessage,
    onConnect: () => {
      console.log('Connected to feed updates');
      ping();
    },
    onDisconnect: () => {
      console.log('Disconnected from feed updates');
    },
  });

  // Handle incoming WebSocket messages
  const handleWebSocketMessage = useCallback((message: any) => {
    console.log('Received WebSocket message:', message);
    
    switch (message.type) {
      case 'user_status_update':
        handleUserStatusUpdate(message);
        break;
      case 'pong':
        // Connection is alive, schedule next ping
        setTimeout(ping, 30000);
        break;
      case 'connection_established':
        console.log('Feed WebSocket connection established');
        break;
      default:
        console.log('Unknown message type:', message.type);
    }
  }, [ping]);

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
          ...status,
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
          interests: [],
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
      const data = await userAPI.getFeedListeners({
        online_only: true,
        available_only: true,
        page: 1,
        per_page: 20,
      });
      
      setListeners(data.listeners);
      setFeedStats({
        total_count: data.total_count,
        online_count: data.online_count,
        available_count: data.available_count,
      });
    } catch (error) {
      console.error('Error loading feed data:', error);
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
    <TouchableOpacity style={styles.listenerItem}>
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
    </TouchableOpacity>
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

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 16,
    backgroundColor: 'white',
    borderBottomWidth: 1,
    borderBottomColor: '#e0e0e0',
  },
  title: {
    fontSize: 20,
    fontWeight: 'bold',
  },
  statsContainer: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  statsText: {
    fontSize: 12,
    color: '#666',
    marginRight: 8,
  },
  connectionStatus: {
    width: 8,
    height: 8,
    borderRadius: 4,
  },
  errorContainer: {
    backgroundColor: '#ffebee',
    padding: 12,
    margin: 16,
  },
  errorText: {
    color: '#c62828',
    fontSize: 14,
  },
  listenerItem: {
    backgroundColor: 'white',
    marginHorizontal: 16,
    marginVertical: 4,
    padding: 16,
    borderRadius: 8,
    elevation: 2,
  },
  listenerInfo: {
    flex: 1,
  },
  username: {
    fontSize: 16,
    fontWeight: 'bold',
    marginBottom: 4,
  },
  statusContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8,
  },
  statusDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    marginRight: 6,
  },
  statusText: {
    fontSize: 12,
    color: '#666',
  },
  bio: {
    fontSize: 14,
    color: '#333',
    marginBottom: 4,
  },
  interests: {
    fontSize: 12,
    color: '#666',
    fontStyle: 'italic',
  },
  emptyText: {
    textAlign: 'center',
    marginTop: 50,
    fontSize: 16,
    color: '#666',
  },
});
```

## Best Practices

### 1. Error Handling

- Always handle network errors gracefully
- Implement retry logic for failed requests
- Show user-friendly error messages
- Log errors for debugging

### 2. Performance

- Use React.memo for expensive components
- Implement proper loading states
- Cache API responses when appropriate
- Optimize WebSocket message handling

### 3. Security

- Store tokens securely using AsyncStorage or SecureStore
- Validate all user inputs
- Implement proper authentication checks
- Use HTTPS in production

### 4. User Experience

- Provide immediate feedback for user actions
- Implement pull-to-refresh functionality
- Show connection status indicators
- Handle offline scenarios gracefully

## Next Steps

- Learn about [WebSocket Integration](./websocket-integration) for real-time features
- Explore [API Examples](./api-examples) for common use cases
- Check out [Error Handling](./error-handling) for robust error management

---

Ready to start building? Check out the [API Documentation](../api/authentication) to learn about all available endpoints!
