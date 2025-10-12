# Complete React Native Integration Guide

This is the master guide that ties together all React Native integration components for the Saathii Backend FastAPI. This document provides an overview and links to detailed implementation guides for each feature.

## Overview

The Saathii Backend FastAPI provides a comprehensive platform for building calling and listening applications. This integration guide covers all major features with complete React Native implementations, including:

- **Authentication System** - OTP-based login with JWT tokens
- **User Management** - Profile management and status tracking
- **Presence System** - Real-time online/offline status
- **Feed System** - Discover and browse listeners
- **Call Management** - Start, manage, and track calls with coin billing
- **WebSocket Integration** - Real-time updates and live features
- **Favorites & Blocking** - User interaction management
- **Listener Verification** - Audio verification system
- **Wallet System** - Coin management and transactions

## Quick Start

### 1. Project Setup

```bash
# Create new React Native project
npx react-native init SaathiiApp --template react-native-template-typescript

# Install required dependencies
npm install @react-native-async-storage/async-storage
npm install axios
npm install react-native-image-picker
npm install @react-navigation/native @react-navigation/bottom-tabs
npm install react-native-screens react-native-safe-area-context
```

### 2. Base Configuration

Create the base API configuration as shown in the [Authentication Guide](./react-native-integration.md#getting-started).

### 3. Navigation Setup

```typescript
// App.tsx
import React from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { useWebSocket } from './hooks/useWebSocket';

// Import your screens
import LoginScreen from './screens/LoginScreen';
import MainApp from './screens/MainApp';
import FeedScreen from './screens/FeedScreen';
import FavoritesScreen from './screens/FavoritesScreen';
import ProfileScreen from './screens/ProfileScreen';

const Tab = createBottomTabNavigator();

const App = () => {
  const { isConnected } = useWebSocket();

  return (
    <NavigationContainer>
      <Tab.Navigator>
        <Tab.Screen name="Feed" component={FeedScreen} />
        <Tab.Screen name="Favorites" component={FavoritesScreen} />
        <Tab.Screen name="Profile" component={ProfileScreen} />
      </Tab.Navigator>
    </NavigationContainer>
  );
};

export default App;
```

## Feature Implementation Guides

### 1. Authentication System
**Guide**: [React Native Integration - Authentication](./react-native-integration.md#authentication-system)

**Key Features**:
- OTP-based phone number authentication
- JWT token management with automatic refresh
- User registration with profile setup
- Secure logout with token invalidation

**Implementation Files**:
- `services/authService.ts` - Authentication API calls
- `components/LoginScreen.tsx` - Phone number input and OTP verification
- `components/OTPVerificationScreen.tsx` - OTP input with auto-focus
- `components/RegistrationScreen.tsx` - User profile setup

### 2. User Management
**Guide**: [React Native Integration - User Management](./react-native-integration.md#user-management)

**Key Features**:
- Get and update user profile
- Profile image handling
- User preferences management

**Implementation Files**:
- `services/userService.ts` - User API calls
- `components/ProfileScreen.tsx` - Display user profile
- `components/EditProfileScreen.tsx` - Edit profile form

### 3. Presence & Feed System
**Guide**: [React Native Integration - Presence & Feed](./react-native-presence-feed.md)

**Key Features**:
- Real-time presence tracking (online/offline/busy)
- Heartbeat system to maintain online status
- Feed system with filtering and pagination
- Live status updates

**Implementation Files**:
- `services/presenceService.ts` - Presence API calls
- `services/feedService.ts` - Feed API calls
- `components/StatusToggle.tsx` - Online/busy status controls
- `components/ListenersFeedScreen.tsx` - Browse listeners
- `hooks/useHeartbeat.ts` - Automatic heartbeat management

### 4. Call Management System
**Guide**: [React Native Integration - Call Management](./react-native-call-management.md)

**Key Features**:
- Start and end calls with coin billing
- Call history with filtering
- Coin balance management
- Recharge system with real money

**Implementation Files**:
- `services/callService.ts` - Call API calls
- `services/walletService.ts` - Wallet and coin management
- `components/CallScreen.tsx` - Call interface
- `components/CallHistoryScreen.tsx` - Call history
- `components/RechargeScreen.tsx` - Coin recharge

### 5. WebSocket Real-time Updates
**Guide**: [React Native Integration - WebSocket](./react-native-websocket-realtime.md)

**Key Features**:
- Real-time presence updates
- Live feed updates
- Connection management and reconnection
- App lifecycle handling

**Implementation Files**:
- `services/websocketService.ts` - WebSocket connection manager
- `hooks/usePresenceUpdates.ts` - Presence update handling
- `hooks/useFeedUpdates.ts` - Feed update handling
- `components/ConnectionStatusIndicator.tsx` - Connection status
- `hooks/useWebSocket.ts` - App-wide WebSocket management

### 6. Favorites, Blocking & Verification
**Guide**: [React Native Integration - Favorites, Blocking & Verification](./react-native-favorites-blocking-verification.md)

**Key Features**:
- Add/remove favorites with real-time updates
- Block/unblock users with confirmation
- Audio verification for listeners
- Status tracking and management

**Implementation Files**:
- `services/favoritesService.ts` - Favorites API calls
- `services/blockingService.ts` - Blocking API calls
- `services/verificationService.ts` - Verification API calls
- `components/FavoriteButton.tsx` - Favorite toggle button
- `components/BlockButton.tsx` - Block/unblock button
- `components/VerificationScreen.tsx` - Audio verification

## Complete App Structure

```
src/
├── components/
│   ├── auth/
│   │   ├── LoginScreen.tsx
│   │   ├── OTPVerificationScreen.tsx
│   │   └── RegistrationScreen.tsx
│   ├── user/
│   │   ├── ProfileScreen.tsx
│   │   └── EditProfileScreen.tsx
│   ├── feed/
│   │   ├── ListenersFeedScreen.tsx
│   │   ├── FeedStatsCard.tsx
│   │   └── ListenerCard.tsx
│   ├── calls/
│   │   ├── CallScreen.tsx
│   │   ├── CallHistoryScreen.tsx
│   │   └── RechargeScreen.tsx
│   ├── presence/
│   │   ├── StatusToggle.tsx
│   │   └── RealTimePresenceList.tsx
│   ├── favorites/
│   │   ├── FavoritesScreen.tsx
│   │   └── FavoriteButton.tsx
│   ├── blocking/
│   │   └── BlockButton.tsx
│   ├── verification/
│   │   └── VerificationScreen.tsx
│   └── common/
│       ├── ConnectionStatusIndicator.tsx
│       └── LoadingSpinner.tsx
├── services/
│   ├── httpClient.ts
│   ├── authService.ts
│   ├── userService.ts
│   ├── presenceService.ts
│   ├── feedService.ts
│   ├── callService.ts
│   ├── walletService.ts
│   ├── websocketService.ts
│   ├── favoritesService.ts
│   ├── blockingService.ts
│   └── verificationService.ts
├── hooks/
│   ├── useWebSocket.ts
│   ├── usePresenceUpdates.ts
│   ├── useFeedUpdates.ts
│   └── useHeartbeat.ts
├── config/
│   └── api.ts
├── types/
│   └── index.ts
└── utils/
    └── helpers.ts
```

## Key Implementation Patterns

### 1. Error Handling
All API calls include comprehensive error handling with user-friendly messages:

```typescript
try {
  const response = await apiCall();
  return response.data;
} catch (error) {
  throw new Error(`Operation failed: ${error.response?.data?.detail || error.message}`);
}
```

### 2. Loading States
Components include loading states for better UX:

```typescript
const [loading, setLoading] = useState(false);

const handleAction = async () => {
  setLoading(true);
  try {
    await performAction();
  } finally {
    setLoading(false);
  }
};
```

### 3. Real-time Updates
WebSocket integration provides live updates across the app:

```typescript
useEffect(() => {
  const handleUpdate = (message) => {
    // Update UI based on real-time data
  };
  
  websocketManager.subscribe('feed', handleUpdate);
  return () => websocketManager.unsubscribe('feed', handleUpdate);
}, []);
```

### 4. Token Management
Automatic token refresh and secure storage:

```typescript
// Automatic token refresh in HTTP client
this.client.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      // Attempt token refresh
      const newTokens = await this.refreshTokens();
      // Retry original request
    }
  }
);
```

## Testing Strategy

### 1. Unit Tests
Test individual services and components:

```typescript
// Example test for auth service
describe('AuthService', () => {
  it('should request OTP successfully', async () => {
    const mockResponse = { message: 'OTP sent' };
    jest.spyOn(httpClient, 'post').mockResolvedValue({ data: mockResponse });
    
    const result = await requestOTP('+919876543210');
    expect(result).toEqual(mockResponse);
  });
});
```

### 2. Integration Tests
Test complete user flows:

```typescript
// Example integration test
describe('Authentication Flow', () => {
  it('should complete full login flow', async () => {
    // 1. Request OTP
    // 2. Verify OTP
    // 3. Check token storage
    // 4. Verify API calls include token
  });
});
```

### 3. WebSocket Tests
Test real-time functionality:

```typescript
// Example WebSocket test
describe('WebSocket Integration', () => {
  it('should receive presence updates', (done) => {
    websocketManager.subscribe('presence', (message) => {
      expect(message.type).toBe('presence_update');
      done();
    });
  });
});
```

## Performance Optimization

### 1. Image Optimization
```typescript
// Lazy loading for profile images
<Image
  source={{ uri: user.profile_image_url }}
  style={styles.avatar}
  resizeMode="cover"
  loadingIndicatorSource={require('./placeholder.png')}
/>
```

### 2. List Optimization
```typescript
// FlatList optimization
<FlatList
  data={items}
  renderItem={renderItem}
  keyExtractor={(item) => item.id.toString()}
  getItemLayout={(data, index) => ({
    length: ITEM_HEIGHT,
    offset: ITEM_HEIGHT * index,
    index,
  })}
  removeClippedSubviews={true}
  maxToRenderPerBatch={10}
  windowSize={10}
/>
```

### 3. WebSocket Optimization
```typescript
// Connection management
useEffect(() => {
  const handleAppStateChange = (nextAppState) => {
    if (nextAppState === 'background') {
      websocketManager.disconnect(); // Save battery
    } else if (nextAppState === 'active') {
      websocketManager.connect(); // Reconnect
    }
  };
  
  AppState.addEventListener('change', handleAppStateChange);
}, []);
```

## Security Best Practices

### 1. Token Storage
```typescript
// Secure token storage
await AsyncStorage.setItem('access_token', token);
// Never store sensitive data in plain text
```

### 2. API Security
```typescript
// Always include tokens in API calls
headers: {
  'Authorization': `Bearer ${token}`,
  'Content-Type': 'application/json',
}
```

### 3. Input Validation
```typescript
// Validate user inputs
const validatePhoneNumber = (phone: string) => {
  const phoneRegex = /^\+[1-9]\d{1,14}$/;
  return phoneRegex.test(phone);
};
```

## Deployment Considerations

### 1. Environment Configuration
```typescript
// config/api.ts
const API_BASE_URL = __DEV__ 
  ? 'http://localhost:8000' 
  : 'https://api.saathii.com';
```

### 2. Error Reporting
```typescript
// Integrate with crash reporting
import crashlytics from '@react-native-firebase/crashlytics';

try {
  await apiCall();
} catch (error) {
  crashlytics().recordError(error);
  throw error;
}
```

### 3. Analytics
```typescript
// Track user interactions
import analytics from '@react-native-firebase/analytics';

const trackCallStarted = (callType: string) => {
  analytics().logEvent('call_started', {
    call_type: callType,
  });
};
```

## Conclusion

This complete integration guide provides everything needed to build a full-featured React Native app using the Saathii Backend FastAPI. The modular approach allows you to implement features incrementally, while the comprehensive examples ensure you have working code for every aspect of the system.

Each guide includes:
- **Business context** - Why each feature exists
- **API documentation** - Complete endpoint details
- **React Native examples** - Full component implementations
- **Error handling** - Robust error management
- **Real-time features** - WebSocket integration
- **Best practices** - Security and performance considerations

Start with the authentication system and gradually add features based on your app's requirements. The modular structure makes it easy to customize and extend the functionality as needed.
