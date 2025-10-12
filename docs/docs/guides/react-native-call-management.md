# React Native Integration - Call Management System

This guide covers the complete call management system including starting calls, billing, coin management, and real-time call tracking.

## Call Management System

### 1. Start a Call

**Business Purpose**: Initiate a call with a listener, reserve coins, and set both users as busy.

```typescript
// services/callService.ts
export interface StartCallRequest {
  listener_id: number;
  call_type: 'audio' | 'video';
  estimated_duration_minutes?: number;
}

export interface StartCallResponse {
  call_id: number;
  message: string;
  estimated_cost: number;
  remaining_coins: number;
  call_type: 'audio' | 'video';
  listener_id: number;
  status: 'ongoing';
}

export const startCall = async (data: StartCallRequest): Promise<StartCallResponse> => {
  try {
    const response = await httpClient.post('/calls/start', data);
    return response.data;
  } catch (error) {
    throw new Error(`Failed to start call: ${error.response?.data?.detail || error.message}`);
  }
};
```

**React Native Component Example**:

```typescript
// components/CallScreen.tsx
import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  Alert,
  ActivityIndicator,
  StyleSheet,
} from 'react-native';
import { startCall, endCall, getOngoingCall } from '../services/callService';
import { getCoinBalance } from '../services/walletService';

const CallScreen = ({ route, navigation }) => {
  const { listener } = route.params;
  const [call, setCall] = useState(null);
  const [balance, setBalance] = useState(0);
  const [loading, setLoading] = useState(false);
  const [callType, setCallType] = useState('audio');

  useEffect(() => {
    loadBalance();
    checkOngoingCall();
  }, []);

  const loadBalance = async () => {
    try {
      const balanceData = await getCoinBalance();
      setBalance(balanceData.current_balance);
    } catch (error) {
      console.error('Failed to load balance:', error);
    }
  };

  const checkOngoingCall = async () => {
    try {
      const ongoingCall = await getOngoingCall();
      if (ongoingCall) {
        setCall(ongoingCall);
      }
    } catch (error) {
      // No ongoing call
    }
  };

  const handleStartCall = async () => {
    if (balance < 10) {
      Alert.alert(
        'Insufficient Coins',
        'You need at least 10 coins to start a call. Please recharge your wallet.',
        [
          { text: 'Cancel', style: 'cancel' },
          { text: 'Recharge', onPress: () => navigation.navigate('Recharge') },
        ]
      );
      return;
    }

    setLoading(true);
    try {
      const callData = await startCall({
        listener_id: listener.user_id,
        call_type: callType,
        estimated_duration_minutes: 30,
      });
      
      setCall(callData);
      Alert.alert('Call Started', `Call started with ${listener.username}`);
    } catch (error) {
      Alert.alert('Error', error.message);
    } finally {
      setLoading(false);
    }
  };

  const handleEndCall = async () => {
    if (!call) return;

    setLoading(true);
    try {
      await endCall({
        call_id: call.call_id,
        reason: 'completed',
      });
      
      setCall(null);
      Alert.alert('Call Ended', 'Call ended successfully');
      navigation.goBack();
    } catch (error) {
      Alert.alert('Error', error.message);
    } finally {
      setLoading(false);
    }
  };

  if (call) {
    return (
      <View style={styles.callActiveContainer}>
        <Text style={styles.callActiveTitle}>Call in Progress</Text>
        <Text style={styles.listenerName}>{listener.username}</Text>
        <Text style={styles.callType}>{call.call_type.toUpperCase()} Call</Text>
        
        <TouchableOpacity
          style={styles.endCallButton}
          onPress={handleEndCall}
          disabled={loading}
        >
          <Text style={styles.endCallButtonText}>
            {loading ? 'Ending...' : 'End Call'}
          </Text>
        </TouchableOpacity>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <View style={styles.listenerInfo}>
        {listener.profile_image_url ? (
          <Image source={{ uri: listener.profile_image_url }} style={styles.avatar} />
        ) : (
          <View style={[styles.avatar, styles.avatarPlaceholder]}>
            <Text style={styles.avatarText}>
              {listener.username.charAt(0).toUpperCase()}
            </Text>
          </View>
        )}
        
        <Text style={styles.listenerName}>{listener.username}</Text>
        <Text style={styles.listenerBio}>{listener.bio}</Text>
        
        <View style={styles.statusContainer}>
          <View style={[
            styles.statusDot,
            { backgroundColor: listener.is_available ? '#4CAF50' : '#FF9800' }
          ]} />
          <Text style={styles.statusText}>
            {listener.is_available ? 'Available' : 'Online'}
          </Text>
        </View>
      </View>

      <View style={styles.balanceContainer}>
        <Text style={styles.balanceLabel}>Your Balance</Text>
        <Text style={styles.balanceAmount}>{balance} coins</Text>
      </View>

      <View style={styles.callTypeContainer}>
        <Text style={styles.callTypeLabel}>Call Type</Text>
        <View style={styles.callTypeButtons}>
          <TouchableOpacity
            style={[
              styles.callTypeButton,
              callType === 'audio' && styles.callTypeButtonActive
            ]}
            onPress={() => setCallType('audio')}
          >
            <Text style={[
              styles.callTypeButtonText,
              callType === 'audio' && styles.callTypeButtonTextActive
            ]}>
              Audio Call
            </Text>
          </TouchableOpacity>
          
          <TouchableOpacity
            style={[
              styles.callTypeButton,
              callType === 'video' && styles.callTypeButtonActive
            ]}
            onPress={() => setCallType('video')}
          >
            <Text style={[
              styles.callTypeButtonText,
              callType === 'video' && styles.callTypeButtonTextActive
            ]}>
              Video Call
            </Text>
          </TouchableOpacity>
        </View>
      </View>

      <TouchableOpacity
        style={[
          styles.startCallButton,
          balance < 10 && styles.startCallButtonDisabled
        ]}
        onPress={handleStartCall}
        disabled={loading || balance < 10}
      >
        {loading ? (
          <ActivityIndicator color="white" />
        ) : (
          <Text style={styles.startCallButtonText}>
            Start {callType.charAt(0).toUpperCase() + callType.slice(1)} Call
          </Text>
        )}
      </TouchableOpacity>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    padding: 20,
    backgroundColor: '#f5f5f5',
  },
  listenerInfo: {
    alignItems: 'center',
    backgroundColor: 'white',
    padding: 20,
    borderRadius: 15,
    marginBottom: 20,
  },
  avatar: {
    width: 80,
    height: 80,
    borderRadius: 40,
    marginBottom: 15,
  },
  avatarPlaceholder: {
    backgroundColor: '#ddd',
    justifyContent: 'center',
    alignItems: 'center',
  },
  avatarText: {
    fontSize: 32,
    fontWeight: 'bold',
    color: '#666',
  },
  listenerName: {
    fontSize: 24,
    fontWeight: 'bold',
    marginBottom: 10,
  },
  listenerBio: {
    fontSize: 14,
    color: '#666',
    textAlign: 'center',
    marginBottom: 15,
  },
  statusContainer: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  statusDot: {
    width: 10,
    height: 10,
    borderRadius: 5,
    marginRight: 5,
  },
  statusText: {
    fontSize: 14,
    color: '#666',
  },
  balanceContainer: {
    backgroundColor: 'white',
    padding: 15,
    borderRadius: 10,
    marginBottom: 20,
    alignItems: 'center',
  },
  balanceLabel: {
    fontSize: 14,
    color: '#666',
    marginBottom: 5,
  },
  balanceAmount: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#007AFF',
  },
  callTypeContainer: {
    backgroundColor: 'white',
    padding: 15,
    borderRadius: 10,
    marginBottom: 20,
  },
  callTypeLabel: {
    fontSize: 16,
    fontWeight: '500',
    marginBottom: 10,
  },
  callTypeButtons: {
    flexDirection: 'row',
  },
  callTypeButton: {
    flex: 1,
    padding: 12,
    borderRadius: 8,
    backgroundColor: '#f0f0f0',
    marginRight: 10,
    alignItems: 'center',
  },
  callTypeButtonActive: {
    backgroundColor: '#007AFF',
  },
  callTypeButtonText: {
    fontSize: 14,
    color: '#666',
  },
  callTypeButtonTextActive: {
    color: 'white',
  },
  startCallButton: {
    backgroundColor: '#007AFF',
    padding: 15,
    borderRadius: 10,
    alignItems: 'center',
  },
  startCallButtonDisabled: {
    backgroundColor: '#ccc',
  },
  startCallButtonText: {
    color: 'white',
    fontSize: 16,
    fontWeight: 'bold',
  },
  callActiveContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#f5f5f5',
    padding: 20,
  },
  callActiveTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    marginBottom: 20,
  },
  callType: {
    fontSize: 16,
    color: '#666',
    marginBottom: 30,
  },
  endCallButton: {
    backgroundColor: '#FF3B30',
    padding: 15,
    borderRadius: 10,
    paddingHorizontal: 30,
  },
  endCallButtonText: {
    color: 'white',
    fontSize: 16,
    fontWeight: 'bold',
  },
});

export default CallScreen;
```

### 2. End a Call

**Business Purpose**: End an ongoing call, calculate final cost, and update both users' status.

```typescript
// services/callService.ts
export interface EndCallRequest {
  call_id: number;
  reason?: 'completed' | 'dropped' | 'technical_issue';
}

export interface EndCallResponse {
  call_id: number;
  message: string;
  duration_seconds: number;
  duration_minutes: number;
  coins_spent: number;
  user_money_spend: number;
  listener_money_earned: number;
  status: 'completed' | 'dropped';
}

export const endCall = async (data: EndCallRequest): Promise<EndCallResponse> => {
  try {
    const response = await httpClient.post('/calls/end', data);
    return response.data;
  } catch (error) {
    throw new Error(`Failed to end call: ${error.response?.data?.detail || error.message}`);
  }
};
```

### 3. Get Ongoing Call

**Business Purpose**: Check if user has an ongoing call and get call details.

```typescript
// services/callService.ts
export interface CallInfo {
  call_id: number;
  user_id: number;
  listener_id: number;
  call_type: 'audio' | 'video';
  status: 'ongoing' | 'completed' | 'dropped';
  start_time: string;
  end_time: string | null;
  duration_seconds: number | null;
  duration_minutes: number | null;
  coins_spent: number;
  user_money_spend: number;
  listener_money_earned: number;
  created_at: string;
  updated_at: string;
}

export const getOngoingCall = async (): Promise<CallInfo> => {
  try {
    const response = await httpClient.get('/calls/ongoing');
    return response.data;
  } catch (error) {
    if (error.response?.status === 404) {
      return null; // No ongoing call
    }
    throw new Error(`Failed to get ongoing call: ${error.response?.data?.detail || error.message}`);
  }
};
```

### 4. Call History

**Business Purpose**: Get user's call history with pagination and filtering.

```typescript
// services/callService.ts
export interface CallHistoryResponse {
  calls: CallInfo[];
  total_calls: number;
  total_coins_spent: number;
  total_money_spent: number;
  total_earnings: number;
  page: number;
  per_page: number;
  has_next: boolean;
  has_previous: boolean;
}

export interface CallHistoryFilters {
  page?: number;
  per_page?: number;
  call_type?: 'audio' | 'video';
  status?: 'ongoing' | 'completed' | 'dropped';
}

export const getCallHistory = async (filters: CallHistoryFilters = {}): Promise<CallHistoryResponse> => {
  try {
    const response = await httpClient.get('/calls/history', { params: filters });
    return response.data;
  } catch (error) {
    throw new Error(`Failed to get call history: ${error.response?.data?.detail || error.message}`);
  }
};
```

**React Native Component Example**:

```typescript
// components/CallHistoryScreen.tsx
import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  FlatList,
  TouchableOpacity,
  RefreshControl,
  StyleSheet,
} from 'react-native';
import { getCallHistory, CallInfo } from '../services/callService';

const CallHistoryScreen = () => {
  const [calls, setCalls] = useState<CallInfo[]>([]);
  const [loading, setLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [page, setPage] = useState(1);
  const [hasNext, setHasNext] = useState(false);
  const [filters, setFilters] = useState({
    call_type: null,
    status: null,
  });

  useEffect(() => {
    loadCallHistory(true);
  }, [filters]);

  const loadCallHistory = async (reset = false) => {
    if (loading) return;
    
    setLoading(true);
    try {
      const currentPage = reset ? 1 : page;
      const response = await getCallHistory({
        ...filters,
        page: currentPage,
        per_page: 20,
      });
      
      if (reset) {
        setCalls(response.calls);
        setPage(1);
      } else {
        setCalls(prev => [...prev, ...response.calls]);
      }
      
      setHasNext(response.has_next);
      if (!reset) setPage(prev => prev + 1);
    } catch (error) {
      console.error('Failed to load call history:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleRefresh = () => {
    setRefreshing(true);
    loadCallHistory(true).finally(() => setRefreshing(false));
  };

  const handleLoadMore = () => {
    if (hasNext && !loading) {
      loadCallHistory(false);
    }
  };

  const formatDuration = (seconds: number) => {
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return '#4CAF50';
      case 'dropped': return '#FF9800';
      case 'ongoing': return '#2196F3';
      default: return '#666';
    }
  };

  const renderCall = ({ item }: { item: CallInfo }) => (
    <View style={styles.callCard}>
      <View style={styles.callHeader}>
        <View style={styles.callTypeContainer}>
          <Text style={styles.callTypeText}>
            {item.call_type.toUpperCase()}
          </Text>
        </View>
        
        <View style={styles.statusContainer}>
          <View style={[
            styles.statusDot,
            { backgroundColor: getStatusColor(item.status) }
          ]} />
          <Text style={styles.statusText}>{item.status}</Text>
        </View>
      </View>
      
      <Text style={styles.callId}>Call #{item.call_id}</Text>
      
      {item.duration_seconds && (
        <Text style={styles.duration}>
          Duration: {formatDuration(item.duration_seconds)}
        </Text>
      )}
      
      <View style={styles.costContainer}>
        <Text style={styles.costText}>
          Cost: {item.coins_spent} coins
        </Text>
        {item.listener_money_earned > 0 && (
          <Text style={styles.earningsText}>
            Earned: ₹{item.listener_money_earned.toFixed(2)}
          </Text>
        )}
      </View>
      
      <Text style={styles.timestamp}>
        {new Date(item.start_time).toLocaleString()}
      </Text>
    </View>
  );

  return (
    <View style={styles.container}>
      <View style={styles.filtersContainer}>
        <TouchableOpacity
          style={[
            styles.filterButton,
            filters.call_type === 'audio' && styles.filterButtonActive
          ]}
          onPress={() => setFilters(prev => ({ 
            ...prev, 
            call_type: prev.call_type === 'audio' ? null : 'audio' 
          }))}
        >
          <Text style={[
            styles.filterButtonText,
            filters.call_type === 'audio' && styles.filterButtonTextActive
          ]}>
            Audio
          </Text>
        </TouchableOpacity>
        
        <TouchableOpacity
          style={[
            styles.filterButton,
            filters.call_type === 'video' && styles.filterButtonActive
          ]}
          onPress={() => setFilters(prev => ({ 
            ...prev, 
            call_type: prev.call_type === 'video' ? null : 'video' 
          }))}
        >
          <Text style={[
            styles.filterButtonText,
            filters.call_type === 'video' && styles.filterButtonTextActive
          ]}>
            Video
          </Text>
        </TouchableOpacity>
      </View>

      <FlatList
        data={calls}
        renderItem={renderCall}
        keyExtractor={(item) => item.call_id.toString()}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={handleRefresh} />
        }
        onEndReached={handleLoadMore}
        onEndReachedThreshold={0.5}
        ListFooterComponent={() => 
          loading ? <Text style={styles.loadingText}>Loading more...</Text> : null
        }
        ListEmptyComponent={() => 
          !loading ? <Text style={styles.emptyText}>No calls found</Text> : null
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
  callCard: {
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
  callHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 10,
  },
  callTypeContainer: {
    backgroundColor: '#E3F2FD',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 12,
  },
  callTypeText: {
    fontSize: 10,
    color: '#1976D2',
    fontWeight: 'bold',
  },
  statusContainer: {
    flexDirection: 'row',
    alignItems: 'center',
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
    textTransform: 'capitalize',
  },
  callId: {
    fontSize: 14,
    color: '#666',
    marginBottom: 5,
  },
  duration: {
    fontSize: 14,
    color: '#333',
    marginBottom: 10,
  },
  costContainer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 10,
  },
  costText: {
    fontSize: 14,
    color: '#FF9800',
    fontWeight: '500',
  },
  earningsText: {
    fontSize: 14,
    color: '#4CAF50',
    fontWeight: '500',
  },
  timestamp: {
    fontSize: 12,
    color: '#999',
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

export default CallHistoryScreen;
```

## Wallet & Coin Management

### 1. Get Coin Balance

**Business Purpose**: Get user's current coin balance and spending history.

```typescript
// services/walletService.ts
export interface CoinBalanceResponse {
  user_id: number;
  current_balance: number;
  total_earned: number;
  total_spent: number;
}

export const getCoinBalance = async (): Promise<CoinBalanceResponse> => {
  try {
    const response = await httpClient.get('/calls/balance');
    return response.data;
  } catch (error) {
    throw new Error(`Failed to get coin balance: ${error.response?.data?.detail || error.message}`);
  }
};
```

### 2. Recharge Coins

**Business Purpose**: Purchase coins with real money.

```typescript
// services/walletService.ts
export interface RechargeRequest {
  amount_rupees: number;
}

export interface RechargeResponse {
  transaction_id: string;
  amount_rupees: number;
  coins_added: number;
  new_balance: number;
  message: string;
}

export const rechargeCoins = async (data: RechargeRequest): Promise<RechargeResponse> => {
  try {
    const response = await httpClient.post('/calls/recharge', data);
    return response.data;
  } catch (error) {
    throw new Error(`Failed to recharge coins: ${error.response?.data?.detail || error.message}`);
  }
};
```

**React Native Component Example**:

```typescript
// components/RechargeScreen.tsx
import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  Alert,
  StyleSheet,
  ScrollView,
} from 'react-native';
import { rechargeCoins, getCoinBalance } from '../services/walletService';

const RECHARGE_OPTIONS = [
  { amount: 50, coins: 100, bonus: 0 },
  { amount: 100, coins: 250, bonus: 50 },
  { amount: 200, coins: 550, bonus: 100 },
  { amount: 500, coins: 1500, bonus: 500 },
  { amount: 1000, coins: 3500, bonus: 1500 },
];

const RechargeScreen = () => {
  const [balance, setBalance] = useState(0);
  const [selectedAmount, setSelectedAmount] = useState(0);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadBalance();
  }, []);

  const loadBalance = async () => {
    try {
      const balanceData = await getCoinBalance();
      setBalance(balanceData.current_balance);
    } catch (error) {
      console.error('Failed to load balance:', error);
    }
  };

  const handleRecharge = async () => {
    if (selectedAmount === 0) {
      Alert.alert('Error', 'Please select a recharge amount');
      return;
    }

    Alert.alert(
      'Confirm Recharge',
      `Are you sure you want to recharge ₹${selectedAmount}?`,
      [
        { text: 'Cancel', style: 'cancel' },
        { text: 'Confirm', onPress: performRecharge },
      ]
    );
  };

  const performRecharge = async () => {
    setLoading(true);
    try {
      const response = await rechargeCoins({ amount_rupees: selectedAmount });
      
      setBalance(response.new_balance);
      Alert.alert(
        'Recharge Successful',
        `Added ${response.coins_added} coins to your wallet!`
      );
      setSelectedAmount(0);
    } catch (error) {
      Alert.alert('Error', error.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <ScrollView style={styles.container}>
      <View style={styles.balanceCard}>
        <Text style={styles.balanceLabel}>Current Balance</Text>
        <Text style={styles.balanceAmount}>{balance} coins</Text>
      </View>

      <Text style={styles.title}>Choose Recharge Amount</Text>
      
      <View style={styles.optionsContainer}>
        {RECHARGE_OPTIONS.map((option) => (
          <TouchableOpacity
            key={option.amount}
            style={[
              styles.optionCard,
              selectedAmount === option.amount && styles.optionCardSelected
            ]}
            onPress={() => setSelectedAmount(option.amount)}
          >
            <Text style={styles.optionAmount}>₹{option.amount}</Text>
            <Text style={styles.optionCoins}>
              {option.coins} coins
              {option.bonus > 0 && (
                <Text style={styles.bonusText}> + {option.bonus} bonus</Text>
              )}
            </Text>
          </TouchableOpacity>
        ))}
      </View>

      <TouchableOpacity
        style={[
          styles.rechargeButton,
          selectedAmount === 0 && styles.rechargeButtonDisabled
        ]}
        onPress={handleRecharge}
        disabled={loading || selectedAmount === 0}
      >
        <Text style={styles.rechargeButtonText}>
          {loading ? 'Processing...' : `Recharge ₹${selectedAmount}`}
        </Text>
      </TouchableOpacity>
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
    padding: 20,
  },
  balanceCard: {
    backgroundColor: 'white',
    padding: 20,
    borderRadius: 15,
    alignItems: 'center',
    marginBottom: 20,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  balanceLabel: {
    fontSize: 16,
    color: '#666',
    marginBottom: 5,
  },
  balanceAmount: {
    fontSize: 32,
    fontWeight: 'bold',
    color: '#007AFF',
  },
  title: {
    fontSize: 20,
    fontWeight: 'bold',
    marginBottom: 20,
  },
  optionsContainer: {
    marginBottom: 30,
  },
  optionCard: {
    backgroundColor: 'white',
    padding: 20,
    borderRadius: 10,
    marginBottom: 10,
    borderWidth: 2,
    borderColor: 'transparent',
  },
  optionCardSelected: {
    borderColor: '#007AFF',
    backgroundColor: '#F0F8FF',
  },
  optionAmount: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 5,
  },
  optionCoins: {
    fontSize: 16,
    color: '#666',
  },
  bonusText: {
    color: '#4CAF50',
    fontWeight: 'bold',
  },
  rechargeButton: {
    backgroundColor: '#007AFF',
    padding: 15,
    borderRadius: 10,
    alignItems: 'center',
  },
  rechargeButtonDisabled: {
    backgroundColor: '#ccc',
  },
  rechargeButtonText: {
    color: 'white',
    fontSize: 16,
    fontWeight: 'bold',
  },
});

export default RechargeScreen;
```

This documentation covers the complete call management system including starting calls, ending calls, call history, and wallet management. The examples show how to implement a full-featured calling system in your React Native app.

Would you like me to continue with the WebSocket real-time updates and other features?
