# React Native Integration Guide

This comprehensive guide shows how to integrate your React Native app with the Saathii Backend FastAPI. The guide includes detailed examples for each API endpoint, business logic explanations, and complete React Native code implementations.

## Table of Contents

1. [Getting Started](#getting-started)
2. [Authentication System](#authentication-system)
3. [User Management](#user-management)
4. [Presence & Status System](#presence--status-system)
5. [Feed System](#feed-system)
6. [Call Management](#call-management)
7. [WebSocket Real-time Updates](#websocket-real-time-updates)
8. [Wallet & Earnings](#wallet--earnings)
9. [Favorites & Blocking](#favorites--blocking)
10. [Listener Verification](#listener-verification)
11. [Complete App Example](#complete-app-example)

## Getting Started

### Base Configuration

First, set up your base API configuration:

```typescript
// config/api.ts
const API_BASE_URL = 'http://localhost:8000'; // Change to your production URL
const WS_BASE_URL = 'ws://localhost:8000'; // Change to your production WebSocket URL

export const API_ENDPOINTS = {
  AUTH: {
    REQUEST_OTP: `${API_BASE_URL}/auth/request_otp`,
    VERIFY_OTP: `${API_BASE_URL}/auth/verify`,
    REGISTER: `${API_BASE_URL}/auth/register`,
    REFRESH: `${API_BASE_URL}/auth/refresh`,
    LOGOUT: `${API_BASE_URL}/auth/logout`,
  },
  USER: {
    ME: `${API_BASE_URL}/users/me`,
    STATUS: `${API_BASE_URL}/users/me/status`,
    HEARTBEAT: `${API_BASE_URL}/users/me/heartbeat`,
    PRESENCE: `${API_BASE_URL}/users/presence`,
  },
  FEED: {
    LISTENERS: `${API_BASE_URL}/feed/listeners`,
    STATS: `${API_BASE_URL}/feed/stats`,
  },
  CALLS: {
    START: `${API_BASE_URL}/calls/start`,
    END: `${API_BASE_URL}/calls/end`,
    ONGOING: `${API_BASE_URL}/calls/ongoing`,
    HISTORY: `${API_BASE_URL}/calls/history`,
    BALANCE: `${API_BASE_URL}/calls/balance`,
    RECHARGE: `${API_BASE_URL}/calls/recharge`,
  },
  WEBSOCKET: {
    FEED: `${WS_BASE_URL}/ws/feed`,
    PRESENCE: `${WS_BASE_URL}/ws/presence`,
  },
};

export const API_BASE_URL;
export const WS_BASE_URL;
```

### HTTP Client Setup

```typescript
// services/httpClient.ts
import axios, { AxiosInstance, AxiosRequestConfig } from 'axios';
import AsyncStorage from '@react-native-async-storage/async-storage';

class HttpClient {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      timeout: 10000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Add request interceptor to include auth token
    this.client.interceptors.request.use(
      async (config) => {
        const token = await AsyncStorage.getItem('access_token');
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => Promise.reject(error)
    );

    // Add response interceptor to handle token refresh
    this.client.interceptors.response.use(
      (response) => response,
      async (error) => {
        if (error.response?.status === 401) {
          const refreshToken = await AsyncStorage.getItem('refresh_token');
          if (refreshToken) {
            try {
              const newTokens = await this.refreshTokens(refreshToken);
              await AsyncStorage.setItem('access_token', newTokens.access_token);
              await AsyncStorage.setItem('refresh_token', newTokens.refresh_token);
              
              // Retry the original request
              const originalRequest = error.config;
              originalRequest.headers.Authorization = `Bearer ${newTokens.access_token}`;
              return this.client(originalRequest);
            } catch (refreshError) {
              // Refresh failed, redirect to login
              await this.logout();
              throw refreshError;
            }
          }
        }
        return Promise.reject(error);
      }
    );
  }

  private async refreshTokens(refreshToken: string) {
    const response = await this.client.post('/auth/refresh', {
      refresh_token: refreshToken,
    });
    return response.data;
  }

  private async logout() {
    await AsyncStorage.multiRemove(['access_token', 'refresh_token', 'user_data']);
    // Navigate to login screen
  }

  async get(url: string, config?: AxiosRequestConfig) {
    return this.client.get(url, config);
  }

  async post(url: string, data?: any, config?: AxiosRequestConfig) {
    return this.client.post(url, data, config);
  }

  async put(url: string, data?: any, config?: AxiosRequestConfig) {
    return this.client.put(url, data, config);
  }

  async delete(url: string, config?: AxiosRequestConfig) {
    return this.client.delete(url, config);
  }
}

export const httpClient = new HttpClient();
```

## Authentication System

The authentication system uses OTP-based login with JWT tokens. Here's how to implement it:

### 1. Request OTP

**Business Purpose**: Send OTP to user's phone number for authentication.

```typescript
// services/authService.ts
import { httpClient } from './httpClient';

export interface OTPRequest {
  phone: string;
}

export interface OTPResponse {
  message: string;
}

export const requestOTP = async (phone: string): Promise<OTPResponse> => {
  try {
    const response = await httpClient.post('/auth/request_otp', { phone });
    return response.data;
  } catch (error) {
    throw new Error(`Failed to request OTP: ${error.response?.data?.detail || error.message}`);
  }
};
```

**React Native Component Example**:

```typescript
// components/LoginScreen.tsx
import React, { useState } from 'react';
import { View, Text, TextInput, TouchableOpacity, Alert } from 'react-native';
import { requestOTP } from '../services/authService';

const LoginScreen = () => {
  const [phone, setPhone] = useState('');
  const [loading, setLoading] = useState(false);

  const handleRequestOTP = async () => {
    if (!phone.trim()) {
      Alert.alert('Error', 'Please enter your phone number');
      return;
    }

    setLoading(true);
    try {
      await requestOTP(phone);
      Alert.alert('Success', 'OTP sent to your phone number');
      // Navigate to OTP verification screen
    } catch (error) {
      Alert.alert('Error', error.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <View style={{ flex: 1, padding: 20, justifyContent: 'center' }}>
      <Text style={{ fontSize: 24, marginBottom: 20, textAlign: 'center' }}>
        Welcome to Saathii
      </Text>
      
      <TextInput
        style={{
          borderWidth: 1,
          borderColor: '#ccc',
          padding: 15,
          borderRadius: 8,
          marginBottom: 20,
        }}
        placeholder="Enter phone number (e.g., +919876543210)"
        value={phone}
        onChangeText={setPhone}
        keyboardType="phone-pad"
      />
      
      <TouchableOpacity
        style={{
          backgroundColor: '#007AFF',
          padding: 15,
          borderRadius: 8,
          alignItems: 'center',
        }}
        onPress={handleRequestOTP}
        disabled={loading}
      >
        <Text style={{ color: 'white', fontSize: 16 }}>
          {loading ? 'Sending...' : 'Send OTP'}
        </Text>
      </TouchableOpacity>
    </View>
  );
};

export default LoginScreen;
```

### 2. Verify OTP

**Business Purpose**: Verify the OTP and get authentication tokens or registration token.

```typescript
// services/authService.ts
export interface VerifyRequest {
  phone: string;
  otp: string;
}

export interface VerifyResponse {
  status: 'registered' | 'needs_registration';
  access_token?: string;
  refresh_token?: string;
  registration_token?: string;
}

export const verifyOTP = async (phone: string, otp: string): Promise<VerifyResponse> => {
  try {
    const response = await httpClient.post('/auth/verify', { phone, otp });
    return response.data;
  } catch (error) {
    throw new Error(`Failed to verify OTP: ${error.response?.data?.detail || error.message}`);
  }
};
```

**React Native Component Example**:

```typescript
// components/OTPVerificationScreen.tsx
import React, { useState, useRef } from 'react';
import { View, Text, TextInput, TouchableOpacity, Alert } from 'react-native';
import { verifyOTP } from '../services/authService';
import AsyncStorage from '@react-native-async-storage/async-storage';

const OTPVerificationScreen = ({ route, navigation }) => {
  const { phone } = route.params;
  const [otp, setOtp] = useState(['', '', '', '', '', '']);
  const [loading, setLoading] = useState(false);
  const inputRefs = useRef([]);

  const handleOTPChange = (value: string, index: number) => {
    const newOtp = [...otp];
    newOtp[index] = value;
    setOtp(newOtp);

    // Auto-focus next input
    if (value && index < 5) {
      inputRefs.current[index + 1]?.focus();
    }
  };

  const handleVerifyOTP = async () => {
    const otpString = otp.join('');
    if (otpString.length !== 6) {
      Alert.alert('Error', 'Please enter complete OTP');
      return;
    }

    setLoading(true);
    try {
      const response = await verifyOTP(phone, otpString);
      
      if (response.status === 'registered') {
        // User is registered, save tokens and navigate to main app
        await AsyncStorage.setItem('access_token', response.access_token!);
        await AsyncStorage.setItem('refresh_token', response.refresh_token!);
        navigation.replace('MainApp');
      } else {
        // User needs registration, navigate to registration screen
        navigation.navigate('Registration', {
          phone,
          registration_token: response.registration_token,
        });
      }
    } catch (error) {
      Alert.alert('Error', error.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <View style={{ flex: 1, padding: 20, justifyContent: 'center' }}>
      <Text style={{ fontSize: 24, marginBottom: 20, textAlign: 'center' }}>
        Verify OTP
      </Text>
      
      <Text style={{ textAlign: 'center', marginBottom: 30, color: '#666' }}>
        Enter the 6-digit code sent to {phone}
      </Text>
      
      <View style={{ flexDirection: 'row', justifyContent: 'space-between', marginBottom: 30 }}>
        {otp.map((digit, index) => (
          <TextInput
            key={index}
            ref={(ref) => (inputRefs.current[index] = ref)}
            style={{
              width: 45,
              height: 45,
              borderWidth: 1,
              borderColor: '#ccc',
              borderRadius: 8,
              textAlign: 'center',
              fontSize: 18,
            }}
            value={digit}
            onChangeText={(value) => handleOTPChange(value, index)}
            keyboardType="numeric"
            maxLength={1}
          />
        ))}
      </View>
      
      <TouchableOpacity
        style={{
          backgroundColor: '#007AFF',
          padding: 15,
          borderRadius: 8,
          alignItems: 'center',
        }}
        onPress={handleVerifyOTP}
        disabled={loading}
      >
        <Text style={{ color: 'white', fontSize: 16 }}>
          {loading ? 'Verifying...' : 'Verify OTP'}
        </Text>
      </TouchableOpacity>
    </View>
  );
};

export default OTPVerificationScreen;
```

### 3. User Registration

**Business Purpose**: Complete user registration with profile information.

```typescript
// services/authService.ts
export interface RegisterRequest {
  registration_token: string;
  username: string;
  sex: 'male' | 'female' | 'other';
  dob: string; // YYYY-MM-DD format
  bio?: string;
  interests?: string[];
  profile_image_url?: string;
  preferred_language?: string;
  role?: 'listener' | 'user';
}

export interface TokenPairResponse {
  access_token: string;
  refresh_token: string;
}

export const registerUser = async (data: RegisterRequest): Promise<TokenPairResponse> => {
  try {
    const response = await httpClient.post('/auth/register', data);
    return response.data;
  } catch (error) {
    throw new Error(`Failed to register: ${error.response?.data?.detail || error.message}`);
  }
};
```

**React Native Component Example**:

```typescript
// components/RegistrationScreen.tsx
import React, { useState } from 'react';
import { View, Text, TextInput, TouchableOpacity, Alert, ScrollView, Picker } from 'react-native';
import { registerUser } from '../services/authService';
import AsyncStorage from '@react-native-async-storage/async-storage';

const RegistrationScreen = ({ route, navigation }) => {
  const { phone, registration_token } = route.params;
  const [formData, setFormData] = useState({
    username: '',
    sex: 'male',
    dob: '',
    bio: '',
    interests: [],
    preferred_language: 'en',
    role: 'listener',
  });
  const [loading, setLoading] = useState(false);

  const handleRegister = async () => {
    if (!formData.username || !formData.dob) {
      Alert.alert('Error', 'Please fill in all required fields');
      return;
    }

    setLoading(true);
    try {
      const response = await registerUser({
        registration_token,
        ...formData,
      });
      
      await AsyncStorage.setItem('access_token', response.access_token);
      await AsyncStorage.setItem('refresh_token', response.refresh_token);
      
      Alert.alert('Success', 'Registration completed successfully!');
      navigation.replace('MainApp');
    } catch (error) {
      Alert.alert('Error', error.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <ScrollView style={{ flex: 1, padding: 20 }}>
      <Text style={{ fontSize: 24, marginBottom: 20, textAlign: 'center' }}>
        Complete Registration
      </Text>
      
      <TextInput
        style={styles.input}
        placeholder="Username *"
        value={formData.username}
        onChangeText={(text) => setFormData({ ...formData, username: text })}
      />
      
      <View style={styles.pickerContainer}>
        <Text style={styles.label}>Gender *</Text>
        <Picker
          selectedValue={formData.sex}
          onValueChange={(value) => setFormData({ ...formData, sex: value })}
        >
          <Picker.Item label="Male" value="male" />
          <Picker.Item label="Female" value="female" />
          <Picker.Item label="Other" value="other" />
        </Picker>
      </View>
      
      <TextInput
        style={styles.input}
        placeholder="Date of Birth (YYYY-MM-DD) *"
        value={formData.dob}
        onChangeText={(text) => setFormData({ ...formData, dob: text })}
      />
      
      <TextInput
        style={[styles.input, { height: 80 }]}
        placeholder="Bio (optional)"
        value={formData.bio}
        onChangeText={(text) => setFormData({ ...formData, bio: text })}
        multiline
      />
      
      <TextInput
        style={styles.input}
        placeholder="Interests (comma-separated)"
        value={formData.interests.join(', ')}
        onChangeText={(text) => setFormData({ 
          ...formData, 
          interests: text.split(',').map(i => i.trim()).filter(i => i) 
        })}
      />
      
      <TouchableOpacity
        style={styles.button}
        onPress={handleRegister}
        disabled={loading}
      >
        <Text style={styles.buttonText}>
          {loading ? 'Registering...' : 'Complete Registration'}
        </Text>
      </TouchableOpacity>
    </ScrollView>
  );
};

const styles = {
  input: {
    borderWidth: 1,
    borderColor: '#ccc',
    padding: 15,
    borderRadius: 8,
    marginBottom: 15,
  },
  pickerContainer: {
    borderWidth: 1,
    borderColor: '#ccc',
    borderRadius: 8,
    marginBottom: 15,
  },
  label: {
    padding: 15,
    paddingBottom: 5,
    color: '#666',
  },
  button: {
    backgroundColor: '#007AFF',
    padding: 15,
    borderRadius: 8,
    alignItems: 'center',
    marginTop: 20,
  },
  buttonText: {
    color: 'white',
    fontSize: 16,
  },
};

export default RegistrationScreen;
```

### 4. Logout

**Business Purpose**: Logout user and invalidate all tokens.

```typescript
// services/authService.ts
export const logout = async (): Promise<void> => {
  try {
    await httpClient.post('/auth/logout');
    await AsyncStorage.multiRemove(['access_token', 'refresh_token', 'user_data']);
  } catch (error) {
    // Even if logout fails, clear local storage
    await AsyncStorage.multiRemove(['access_token', 'refresh_token', 'user_data']);
    throw new Error(`Logout failed: ${error.response?.data?.detail || error.message}`);
  }
};
```

## User Management

### 1. Get Current User Profile

**Business Purpose**: Retrieve current user's profile information.

```typescript
// services/userService.ts
export interface UserResponse {
  user_id: number;
  username: string;
  phone: string;
  sex: string;
  dob: string;
  bio: string;
  interests: string[];
  profile_image_url: string;
  preferred_language: string;
  rating: number;
  country: string;
  roles: string[];
  created_at: string;
  updated_at: string;
}

export const getCurrentUser = async (): Promise<UserResponse> => {
  try {
    const response = await httpClient.get('/users/me');
    return response.data;
  } catch (error) {
    throw new Error(`Failed to get user profile: ${error.response?.data?.detail || error.message}`);
  }
};
```

**React Native Component Example**:

```typescript
// components/ProfileScreen.tsx
import React, { useState, useEffect } from 'react';
import { View, Text, Image, TouchableOpacity, ActivityIndicator } from 'react-native';
import { getCurrentUser } from '../services/userService';

const ProfileScreen = () => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadUserProfile();
  }, []);

  const loadUserProfile = async () => {
    try {
      const userData = await getCurrentUser();
      setUser(userData);
    } catch (error) {
      console.error('Failed to load profile:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <View style={{ flex: 1, justifyContent: 'center', alignItems: 'center' }}>
        <ActivityIndicator size="large" />
      </View>
    );
  }

  return (
    <View style={{ flex: 1, padding: 20 }}>
      <View style={{ alignItems: 'center', marginBottom: 30 }}>
        {user?.profile_image_url ? (
          <Image
            source={{ uri: user.profile_image_url }}
            style={{ width: 100, height: 100, borderRadius: 50 }}
          />
        ) : (
          <View style={{
            width: 100,
            height: 100,
            borderRadius: 50,
            backgroundColor: '#ccc',
            justifyContent: 'center',
            alignItems: 'center',
          }}>
            <Text style={{ fontSize: 24, color: '#666' }}>
              {user?.username?.charAt(0)?.toUpperCase()}
            </Text>
          </View>
        )}
        
        <Text style={{ fontSize: 24, marginTop: 10, fontWeight: 'bold' }}>
          {user?.username}
        </Text>
        
        <Text style={{ color: '#666', marginTop: 5 }}>
          {user?.phone}
        </Text>
      </View>

      <View style={{ marginBottom: 20 }}>
        <Text style={{ fontSize: 18, fontWeight: 'bold', marginBottom: 10 }}>
          About
        </Text>
        <Text style={{ color: '#666' }}>
          {user?.bio || 'No bio available'}
        </Text>
      </View>

      <View style={{ marginBottom: 20 }}>
        <Text style={{ fontSize: 18, fontWeight: 'bold', marginBottom: 10 }}>
          Interests
        </Text>
        <View style={{ flexDirection: 'row', flexWrap: 'wrap' }}>
          {user?.interests?.map((interest, index) => (
            <View
              key={index}
              style={{
                backgroundColor: '#007AFF',
                paddingHorizontal: 12,
                paddingVertical: 6,
                borderRadius: 15,
                marginRight: 8,
                marginBottom: 8,
              }}
            >
              <Text style={{ color: 'white', fontSize: 12 }}>
                {interest}
              </Text>
            </View>
          ))}
        </View>
      </View>

      <View style={{ marginBottom: 20 }}>
        <Text style={{ fontSize: 18, fontWeight: 'bold', marginBottom: 10 }}>
          Rating
        </Text>
        <Text style={{ fontSize: 16, color: '#666' }}>
          {user?.rating ? `${user.rating}/5` : 'No rating yet'}
        </Text>
      </View>
    </View>
  );
};

export default ProfileScreen;
```

### 2. Update User Profile

**Business Purpose**: Update user's profile information.

```typescript
// services/userService.ts
export interface EditUserRequest {
  username?: string;
  bio?: string;
  rating?: number;
  interests?: string[];
  profile_image_url?: string;
  preferred_language?: string;
}

export const updateUserProfile = async (data: EditUserRequest): Promise<UserResponse> => {
  try {
    const response = await httpClient.put('/users/me', data);
    return response.data;
  } catch (error) {
    throw new Error(`Failed to update profile: ${error.response?.data?.detail || error.message}`);
  }
};
```

**React Native Component Example**:

```typescript
// components/EditProfileScreen.tsx
import React, { useState, useEffect } from 'react';
import { View, Text, TextInput, TouchableOpacity, Alert, ScrollView } from 'react-native';
import { getCurrentUser, updateUserProfile } from '../services/userService';

const EditProfileScreen = ({ navigation }) => {
  const [formData, setFormData] = useState({
    username: '',
    bio: '',
    interests: [],
    preferred_language: 'en',
  });
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadCurrentProfile();
  }, []);

  const loadCurrentProfile = async () => {
    try {
      const user = await getCurrentUser();
      setFormData({
        username: user.username,
        bio: user.bio || '',
        interests: user.interests || [],
        preferred_language: user.preferred_language || 'en',
      });
    } catch (error) {
      Alert.alert('Error', 'Failed to load profile');
    }
  };

  const handleSave = async () => {
    if (!formData.username.trim()) {
      Alert.alert('Error', 'Username is required');
      return;
    }

    setLoading(true);
    try {
      await updateUserProfile(formData);
      Alert.alert('Success', 'Profile updated successfully');
      navigation.goBack();
    } catch (error) {
      Alert.alert('Error', error.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <ScrollView style={{ flex: 1, padding: 20 }}>
      <Text style={{ fontSize: 24, marginBottom: 20 }}>Edit Profile</Text>
      
      <TextInput
        style={styles.input}
        placeholder="Username"
        value={formData.username}
        onChangeText={(text) => setFormData({ ...formData, username: text })}
      />
      
      <TextInput
        style={[styles.input, { height: 80 }]}
        placeholder="Bio"
        value={formData.bio}
        onChangeText={(text) => setFormData({ ...formData, bio: text })}
        multiline
      />
      
      <TextInput
        style={styles.input}
        placeholder="Interests (comma-separated)"
        value={formData.interests.join(', ')}
        onChangeText={(text) => setFormData({ 
          ...formData, 
          interests: text.split(',').map(i => i.trim()).filter(i => i) 
        })}
      />
      
      <TouchableOpacity
        style={styles.button}
        onPress={handleSave}
        disabled={loading}
      >
        <Text style={styles.buttonText}>
          {loading ? 'Saving...' : 'Save Changes'}
        </Text>
      </TouchableOpacity>
    </ScrollView>
  );
};

const styles = {
  input: {
    borderWidth: 1,
    borderColor: '#ccc',
    padding: 15,
    borderRadius: 8,
    marginBottom: 15,
  },
  button: {
    backgroundColor: '#007AFF',
    padding: 15,
    borderRadius: 8,
    alignItems: 'center',
    marginTop: 20,
  },
  buttonText: {
    color: 'white',
    fontSize: 16,
  },
};

export default EditProfileScreen;
```

This documentation provides a comprehensive foundation for React Native integration. The examples show real-world usage patterns and include proper error handling, loading states, and user feedback. Each API endpoint is explained with its business purpose and includes complete React Native implementation examples.

Would you like me to continue with the remaining sections (Presence & Status, Feed System, Call Management, WebSocket, etc.)?
