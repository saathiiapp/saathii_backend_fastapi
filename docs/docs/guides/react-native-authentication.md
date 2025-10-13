---
sidebar_position: 1
title: React Native Authentication
description: Complete authentication integration for React Native apps
---

# React Native Authentication

Complete guide for integrating Saathii Backend authentication into React Native applications.

## Overview

- **OTP Authentication**: Phone number-based OTP verification
- **Token Management**: Secure token storage and refresh
- **User Registration**: Complete user onboarding flow
- **Session Management**: Automatic token refresh and logout

## Installation

### Required Dependencies

```bash
npm install @react-native-async-storage/async-storage
npm install react-native-keychain
npm install react-native-sms-retriever
```

### iOS Setup

Add to `ios/Podfile`:
```ruby
pod 'RNKeychain', :path => '../node_modules/react-native-keychain'
```

### Android Setup

Add to `android/app/src/main/AndroidManifest.xml`:
```xml
<uses-permission android:name="android.permission.RECEIVE_SMS" />
<uses-permission android:name="android.permission.READ_SMS" />
```

## Authentication Service

### Base API Service

```typescript
// services/ApiService.ts
import AsyncStorage from '@react-native-async-storage/async-storage';

const API_BASE_URL = 'https://your-api-domain.com';

class ApiService {
  private baseURL: string;

  constructor() {
    this.baseURL = API_BASE_URL;
  }

  private async getAuthHeaders(): Promise<Record<string, string>> {
    const token = await AsyncStorage.getItem('access_token');
    return {
      'Content-Type': 'application/json',
      ...(token && { Authorization: `Bearer ${token}` }),
    };
  }

  async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseURL}${endpoint}`;
    const headers = await this.getAuthHeaders();

    const response = await fetch(url, {
      ...options,
      headers: {
        ...headers,
        ...options.headers,
      },
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Request failed');
    }

    return response.json();
  }

  // GET request
  async get<T>(endpoint: string): Promise<T> {
    return this.request<T>(endpoint, { method: 'GET' });
  }

  // POST request
  async post<T>(endpoint: string, data?: any): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'POST',
      body: data ? JSON.stringify(data) : undefined,
    });
  }

  // PUT request
  async put<T>(endpoint: string, data?: any): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'PUT',
      body: data ? JSON.stringify(data) : undefined,
    });
  }

  // DELETE request
  async delete<T>(endpoint: string): Promise<T> {
    return this.request<T>(endpoint, { method: 'DELETE' });
  }
}

export default new ApiService();
```

### Authentication Service

```typescript
// services/AuthService.ts
import AsyncStorage from '@react-native-async-storage/async-storage';
import ApiService from './ApiService';

export interface OTPRequest {
  phone: string;
}

export interface VerifyRequest {
  phone: string;
  otp: string;
}

export interface RegisterRequest {
  registration_token: string;
  username: string;
  sex: 'male' | 'female' | 'other';
  dob: string;
  bio?: string;
  interests?: string[];
  profile_image_url?: string;
  preferred_language?: string;
  role?: 'listener' | 'customer';
}

export interface TokenPair {
  access_token: string;
  refresh_token: string;
}

export interface VerifyResponse {
  status: 'registered' | 'needs_registration';
  access_token?: string;
  refresh_token?: string;
  registration_token?: string;
}

class AuthService {
  // Request OTP
  async requestOTP(phone: string): Promise<{ message: string }> {
    return ApiService.post('/auth/request_otp', { phone });
  }

  // Resend OTP
  async resendOTP(phone: string): Promise<{ message: string }> {
    return ApiService.post('/auth/resend_otp', { phone });
  }

  // Verify OTP
  async verifyOTP(phone: string, otp: string): Promise<VerifyResponse> {
    return ApiService.post('/auth/verify', { phone, otp });
  }

  // Register User
  async registerUser(data: RegisterRequest): Promise<TokenPair> {
    return ApiService.post('/auth/register', data);
  }

  // Refresh Tokens
  async refreshTokens(refreshToken: string): Promise<TokenPair> {
    return ApiService.post('/auth/refresh', { refresh_token: refreshToken });
  }

  // Logout
  async logout(): Promise<{ message: string }> {
    return ApiService.post('/auth/logout');
  }

  // Store tokens
  async storeTokens(accessToken: string, refreshToken: string): Promise<void> {
    await AsyncStorage.multiSet([
      ['access_token', accessToken],
      ['refresh_token', refreshToken],
    ]);
  }

  // Get stored tokens
  async getStoredTokens(): Promise<{ accessToken: string | null; refreshToken: string | null }> {
    const [accessToken, refreshToken] = await AsyncStorage.multiGet([
      'access_token',
      'refresh_token',
    ]);
    return {
      accessToken: accessToken[1],
      refreshToken: refreshToken[1],
    };
  }

  // Clear tokens
  async clearTokens(): Promise<void> {
    await AsyncStorage.multiRemove(['access_token', 'refresh_token']);
  }

  // Check if user is authenticated
  async isAuthenticated(): Promise<boolean> {
    const { accessToken } = await this.getStoredTokens();
    return !!accessToken;
  }
}

export default new AuthService();
```

## Authentication Context

```typescript
// contexts/AuthContext.tsx
import React, { createContext, useContext, useEffect, useState } from 'react';
import AuthService, { VerifyResponse, RegisterRequest } from '../services/AuthService';

interface User {
  user_id: number;
  phone: string;
  username: string;
  sex: string;
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

interface AuthContextType {
  user: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (phone: string, otp: string) => Promise<void>;
  register: (data: RegisterRequest) => Promise<void>;
  logout: () => Promise<void>;
  requestOTP: (phone: string) => Promise<void>;
  resendOTP: (phone: string) => Promise<void>;
  verifyOTP: (phone: string, otp: string) => Promise<VerifyResponse>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

interface AuthProviderProps {
  children: React.ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    checkAuthStatus();
  }, []);

  const checkAuthStatus = async () => {
    try {
      const isAuth = await AuthService.isAuthenticated();
      if (isAuth) {
        // Load user profile
        await loadUserProfile();
      }
    } catch (error) {
      console.error('Auth check failed:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const loadUserProfile = async () => {
    try {
      // This would be implemented in UserService
      // const userProfile = await UserService.getCurrentUser();
      // setUser(userProfile);
    } catch (error) {
      console.error('Failed to load user profile:', error);
      await AuthService.clearTokens();
    }
  };

  const requestOTP = async (phone: string) => {
    await AuthService.requestOTP(phone);
  };

  const resendOTP = async (phone: string) => {
    await AuthService.resendOTP(phone);
  };

  const verifyOTP = async (phone: string, otp: string): Promise<VerifyResponse> => {
    return AuthService.verifyOTP(phone, otp);
  };

  const login = async (phone: string, otp: string) => {
    const response = await verifyOTP(phone, otp);
    
    if (response.status === 'registered' && response.access_token && response.refresh_token) {
      await AuthService.storeTokens(response.access_token, response.refresh_token);
      await loadUserProfile();
    } else {
      throw new Error('User needs to complete registration');
    }
  };

  const register = async (data: RegisterRequest) => {
    const response = await AuthService.registerUser(data);
    await AuthService.storeTokens(response.access_token, response.refresh_token);
    await loadUserProfile();
  };

  const logout = async () => {
    try {
      await AuthService.logout();
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      await AuthService.clearTokens();
      setUser(null);
    }
  };

  const value: AuthContextType = {
    user,
    isLoading,
    isAuthenticated: !!user,
    login,
    register,
    logout,
    requestOTP,
    resendOTP,
    verifyOTP,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};
```

## Authentication Screens

### OTP Request Screen

```typescript
// screens/OTPRequestScreen.tsx
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
import { useAuth } from '../contexts/AuthContext';

const OTPRequestScreen: React.FC = () => {
  const [phone, setPhone] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const { requestOTP } = useAuth();

  const handleRequestOTP = async () => {
    if (!phone.trim()) {
      Alert.alert('Error', 'Please enter your phone number');
      return;
    }

    setIsLoading(true);
    try {
      await requestOTP(phone);
      Alert.alert('Success', 'OTP sent to your phone number');
      // Navigate to OTP verification screen
    } catch (error) {
      Alert.alert('Error', error.message || 'Failed to send OTP');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Enter Your Phone Number</Text>
      <Text style={styles.subtitle}>
        We'll send you a verification code
      </Text>
      
      <TextInput
        style={styles.input}
        placeholder="+1234567890"
        value={phone}
        onChangeText={setPhone}
        keyboardType="phone-pad"
        autoFocus
      />
      
      <TouchableOpacity
        style={[styles.button, isLoading && styles.buttonDisabled]}
        onPress={handleRequestOTP}
        disabled={isLoading}
      >
        {isLoading ? (
          <ActivityIndicator color="#fff" />
        ) : (
          <Text style={styles.buttonText}>Send OTP</Text>
        )}
      </TouchableOpacity>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    padding: 20,
    justifyContent: 'center',
    backgroundColor: '#f5f5f5',
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    textAlign: 'center',
    marginBottom: 10,
  },
  subtitle: {
    fontSize: 16,
    textAlign: 'center',
    marginBottom: 30,
    color: '#666',
  },
  input: {
    borderWidth: 1,
    borderColor: '#ddd',
    borderRadius: 8,
    padding: 15,
    fontSize: 16,
    marginBottom: 20,
    backgroundColor: '#fff',
  },
  button: {
    backgroundColor: '#007AFF',
    padding: 15,
    borderRadius: 8,
    alignItems: 'center',
  },
  buttonDisabled: {
    backgroundColor: '#ccc',
  },
  buttonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: 'bold',
  },
});

export default OTPRequestScreen;
```

### OTP Verification Screen

```typescript
// screens/OTPVerificationScreen.tsx
import React, { useState, useRef, useEffect } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  StyleSheet,
  Alert,
  ActivityIndicator,
} from 'react-native';
import { useAuth } from '../contexts/AuthContext';

interface OTPVerificationScreenProps {
  phone: string;
  onSuccess: (response: any) => void;
}

const OTPVerificationScreen: React.FC<OTPVerificationScreenProps> = ({
  phone,
  onSuccess,
}) => {
  const [otp, setOtp] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [resendCooldown, setResendCooldown] = useState(0);
  const { verifyOTP, resendOTP } = useAuth();
  const otpInputRef = useRef<TextInput>(null);

  useEffect(() => {
    // Start resend cooldown
    setResendCooldown(60);
    const timer = setInterval(() => {
      setResendCooldown((prev) => {
        if (prev <= 1) {
          clearInterval(timer);
          return 0;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(timer);
  }, []);

  const handleVerifyOTP = async () => {
    if (otp.length !== 6) {
      Alert.alert('Error', 'Please enter a valid 6-digit OTP');
      return;
    }

    setIsLoading(true);
    try {
      const response = await verifyOTP(phone, otp);
      onSuccess(response);
    } catch (error) {
      Alert.alert('Error', error.message || 'Invalid OTP');
    } finally {
      setIsLoading(false);
    }
  };

  const handleResendOTP = async () => {
    if (resendCooldown > 0) return;

    setIsLoading(true);
    try {
      await resendOTP(phone);
      Alert.alert('Success', 'OTP resent successfully');
      setResendCooldown(60);
    } catch (error) {
      Alert.alert('Error', error.message || 'Failed to resend OTP');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Enter Verification Code</Text>
      <Text style={styles.subtitle}>
        We sent a 6-digit code to {phone}
      </Text>
      
      <TextInput
        ref={otpInputRef}
        style={styles.input}
        placeholder="000000"
        value={otp}
        onChangeText={setOtp}
        keyboardType="number-pad"
        maxLength={6}
        autoFocus
      />
      
      <TouchableOpacity
        style={[styles.button, isLoading && styles.buttonDisabled]}
        onPress={handleVerifyOTP}
        disabled={isLoading}
      >
        {isLoading ? (
          <ActivityIndicator color="#fff" />
        ) : (
          <Text style={styles.buttonText}>Verify OTP</Text>
        )}
      </TouchableOpacity>

      <TouchableOpacity
        style={[
          styles.resendButton,
          resendCooldown > 0 && styles.resendButtonDisabled,
        ]}
        onPress={handleResendOTP}
        disabled={resendCooldown > 0 || isLoading}
      >
        <Text style={styles.resendButtonText}>
          {resendCooldown > 0
            ? `Resend in ${resendCooldown}s`
            : 'Resend OTP'}
        </Text>
      </TouchableOpacity>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    padding: 20,
    justifyContent: 'center',
    backgroundColor: '#f5f5f5',
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    textAlign: 'center',
    marginBottom: 10,
  },
  subtitle: {
    fontSize: 16,
    textAlign: 'center',
    marginBottom: 30,
    color: '#666',
  },
  input: {
    borderWidth: 1,
    borderColor: '#ddd',
    borderRadius: 8,
    padding: 15,
    fontSize: 24,
    textAlign: 'center',
    marginBottom: 20,
    backgroundColor: '#fff',
    letterSpacing: 8,
  },
  button: {
    backgroundColor: '#007AFF',
    padding: 15,
    borderRadius: 8,
    alignItems: 'center',
    marginBottom: 20,
  },
  buttonDisabled: {
    backgroundColor: '#ccc',
  },
  buttonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: 'bold',
  },
  resendButton: {
    alignItems: 'center',
  },
  resendButtonDisabled: {
    opacity: 0.5,
  },
  resendButtonText: {
    color: '#007AFF',
    fontSize: 16,
  },
});

export default OTPVerificationScreen;
```

### Registration Screen

```typescript
// screens/RegistrationScreen.tsx
import React, { useState } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  StyleSheet,
  Alert,
  ActivityIndicator,
  ScrollView,
  Picker,
} from 'react-native';
import { useAuth } from '../contexts/AuthContext';

interface RegistrationScreenProps {
  registrationToken: string;
  onSuccess: () => void;
}

const RegistrationScreen: React.FC<RegistrationScreenProps> = ({
  registrationToken,
  onSuccess,
}) => {
  const [formData, setFormData] = useState({
    username: '',
    sex: 'male' as 'male' | 'female' | 'other',
    dob: '',
    bio: '',
    interests: [] as string[],
    profile_image_url: '',
    preferred_language: 'en',
    role: 'customer' as 'listener' | 'customer',
  });
  const [isLoading, setIsLoading] = useState(false);
  const { register } = useAuth();

  const handleRegister = async () => {
    if (!formData.username.trim()) {
      Alert.alert('Error', 'Please enter a username');
      return;
    }

    if (!formData.dob) {
      Alert.alert('Error', 'Please enter your date of birth');
      return;
    }

    setIsLoading(true);
    try {
      await register({
        registration_token: registrationToken,
        ...formData,
      });
      onSuccess();
    } catch (error) {
      Alert.alert('Error', error.message || 'Registration failed');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <ScrollView style={styles.container}>
      <Text style={styles.title}>Complete Your Profile</Text>
      
      <TextInput
        style={styles.input}
        placeholder="Username"
        value={formData.username}
        onChangeText={(text) => setFormData({ ...formData, username: text })}
      />
      
      <View style={styles.pickerContainer}>
        <Text style={styles.pickerLabel}>Gender</Text>
        <Picker
          selectedValue={formData.sex}
          onValueChange={(value) => setFormData({ ...formData, sex: value })}
          style={styles.picker}
        >
          <Picker.Item label="Male" value="male" />
          <Picker.Item label="Female" value="female" />
          <Picker.Item label="Other" value="other" />
        </Picker>
      </View>
      
      <TextInput
        style={styles.input}
        placeholder="Date of Birth (YYYY-MM-DD)"
        value={formData.dob}
        onChangeText={(text) => setFormData({ ...formData, dob: text })}
      />
      
      <TextInput
        style={[styles.input, styles.textArea]}
        placeholder="Bio (optional)"
        value={formData.bio}
        onChangeText={(text) => setFormData({ ...formData, bio: text })}
        multiline
        numberOfLines={3}
      />
      
      <View style={styles.pickerContainer}>
        <Text style={styles.pickerLabel}>Role</Text>
        <Picker
          selectedValue={formData.role}
          onValueChange={(value) => setFormData({ ...formData, role: value })}
          style={styles.picker}
        >
          <Picker.Item label="Customer" value="customer" />
          <Picker.Item label="Listener" value="listener" />
        </Picker>
      </View>
      
      <TouchableOpacity
        style={[styles.button, isLoading && styles.buttonDisabled]}
        onPress={handleRegister}
        disabled={isLoading}
      >
        {isLoading ? (
          <ActivityIndicator color="#fff" />
        ) : (
          <Text style={styles.buttonText}>Complete Registration</Text>
        )}
      </TouchableOpacity>
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    padding: 20,
    backgroundColor: '#f5f5f5',
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    textAlign: 'center',
    marginBottom: 30,
  },
  input: {
    borderWidth: 1,
    borderColor: '#ddd',
    borderRadius: 8,
    padding: 15,
    fontSize: 16,
    marginBottom: 15,
    backgroundColor: '#fff',
  },
  textArea: {
    height: 80,
    textAlignVertical: 'top',
  },
  pickerContainer: {
    marginBottom: 15,
  },
  pickerLabel: {
    fontSize: 16,
    marginBottom: 5,
    color: '#333',
  },
  picker: {
    backgroundColor: '#fff',
    borderWidth: 1,
    borderColor: '#ddd',
    borderRadius: 8,
  },
  button: {
    backgroundColor: '#007AFF',
    padding: 15,
    borderRadius: 8,
    alignItems: 'center',
    marginTop: 20,
  },
  buttonDisabled: {
    backgroundColor: '#ccc',
  },
  buttonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: 'bold',
  },
});

export default RegistrationScreen;
```

## App Integration

### App.tsx

```typescript
// App.tsx
import React from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { createStackNavigator } from '@react-navigation/stack';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import OTPRequestScreen from './screens/OTPRequestScreen';
import OTPVerificationScreen from './screens/OTPVerificationScreen';
import RegistrationScreen from './screens/RegistrationScreen';
import MainApp from './screens/MainApp';

const Stack = createStackNavigator();

const AuthNavigator = () => {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return <LoadingScreen />;
  }

  return (
    <Stack.Navigator screenOptions={{ headerShown: false }}>
      {isAuthenticated ? (
        <Stack.Screen name="MainApp" component={MainApp} />
      ) : (
        <>
          <Stack.Screen name="OTPRequest" component={OTPRequestScreen} />
          <Stack.Screen name="OTPVerification" component={OTPVerificationScreen} />
          <Stack.Screen name="Registration" component={RegistrationScreen} />
        </>
      )}
    </Stack.Navigator>
  );
};

const App = () => {
  return (
    <AuthProvider>
      <NavigationContainer>
        <AuthNavigator />
      </NavigationContainer>
    </AuthProvider>
  );
};

export default App;
```

## Best Practices

### Security

1. **Token Storage**: Use secure storage for tokens
2. **Token Refresh**: Implement automatic token refresh
3. **Input Validation**: Validate all user inputs
4. **Error Handling**: Don't expose sensitive information in errors

### User Experience

1. **Loading States**: Show loading indicators during operations
2. **Error Messages**: Provide clear, user-friendly error messages
3. **Form Validation**: Validate forms before submission
4. **Auto-focus**: Focus appropriate inputs automatically

### Performance

1. **Token Caching**: Cache tokens locally
2. **Request Debouncing**: Debounce rapid requests
3. **Error Recovery**: Implement retry logic for failed requests
4. **Memory Management**: Clean up resources properly

## Next Steps

- Learn about [React Native User Management](./react-native-user-management)
- Explore [React Native Wallets](./react-native-wallets)
- Check out [React Native Calls](./react-native-calls)
