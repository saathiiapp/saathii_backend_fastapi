---
sidebar_position: 3
title: React Native Wallets
description: Complete wallet and coin management for React Native apps
---

# React Native Wallets

Complete guide for integrating wallet management, coin operations, and financial tracking into React Native applications.

## Overview

- **Coin Management**: Add, track, and manage virtual coins
- **Financial Tracking**: Monitor earnings, withdrawals, and transactions
- **Bank Integration**: Manage bank details for withdrawals
- **Transaction History**: Complete audit trail of all wallet operations

## Wallet Service

### Wallet Service Implementation

```typescript
// services/WalletService.ts
import ApiService from './ApiService';

export interface UserWalletBalance {
  user_id: number;
  balance_coins: number;
}

export interface ListenerWalletBalance {
  user_id: number;
  withdrawable_money: number;
  total_earned: number;
}

export interface AddCoinsRequest {
  coins: number;
  tx_type: 'purchase' | 'bonus' | 'referral_bonus';
  money_amount?: number;
}

export interface AddCoinsResponse {
  transaction_id: number;
  coins_added: number;
  money_amount: number;
  new_balance: number;
  message: string;
  created_at: string;
}

export interface CallEarning {
  call_id: number;
  user_id: number;
  coins_earned: number;
  money_earned: number;
  duration_minutes: number;
  created_at: string;
}

export interface CallEarningsResponse {
  earnings: CallEarning[];
  total_earnings: number;
  total_coins: number;
  page: number;
  per_page: number;
  has_next: boolean;
  has_previous: boolean;
}

export interface WithdrawalRequest {
  amount: number;
}

export interface WithdrawalResponse {
  transaction_id: number;
  amount: number;
  message: string;
  created_at: string;
}

export interface WithdrawalHistoryItem {
  transaction_id: number;
  amount: number;
  created_at: string;
  status: string;
}

export interface WithdrawalHistoryResponse {
  withdrawals: WithdrawalHistoryItem[];
  total_withdrawn: number;
  pending_amount: number;
  page: number;
  per_page: number;
  has_next: boolean;
  has_previous: boolean;
}

export interface BankDetailsUpdate {
  payout_account: {
    account_holder_name: string;
    account_number: string;
    ifsc_code: string;
    bank_name: string;
  };
}

export interface BankDetailsResponse {
  has_bank_details: boolean;
  message: string;
}

class WalletService {
  // Get user wallet balance
  async getBalance(): Promise<{ user_id: number; balance_coins: number }> {
    return ApiService.get<{ user_id: number; balance_coins: number }>('/balance');
  }

  // Add coins to wallet
  async addCoins(data: AddCoinsRequest): Promise<AddCoinsResponse> {
    return ApiService.post<AddCoinsResponse>('/add_coin', data);
  }

  // Get listener balance (for listeners only)
  async getListenerBalance(): Promise<{ user_id: number; withdrawable_money: number; total_earned: number }> {
    return ApiService.get<{ user_id: number; withdrawable_money: number; total_earned: number }>('/listener/balance');
  }

  // Get listener earnings (for listeners only)
  async getEarnings(page: number = 1, perPage: number = 20): Promise<CallEarningsResponse> {
    return ApiService.get<CallEarningsResponse>(`/listener/earnings?page=${page}&per_page=${perPage}`);
  }

  // Request withdrawal (for listeners only)
  async requestWithdrawal(data: WithdrawalRequest): Promise<WithdrawalResponse> {
    return ApiService.post<WithdrawalResponse>('/listener/withdraw', data);
  }

  // Get withdrawal history (for listeners only)
  async getWithdrawalHistory(page: number = 1, perPage: number = 20): Promise<WithdrawalHistoryResponse> {
    return ApiService.get<WithdrawalHistoryResponse>(`/listener/withdrawals?page=${page}&per_page=${perPage}`);
  }

  // Update bank details (for listeners only)
  async updateBankDetails(data: BankDetailsUpdate): Promise<BankDetailsResponse> {
    return ApiService.put<BankDetailsResponse>('/listener/bank-details', data);
  }

  // Get bank details status (for listeners only)
  async getBankDetailsStatus(): Promise<BankDetailsResponse> {
    return ApiService.get<BankDetailsResponse>('/listener/bank-details');
  }
}

export default new WalletService();
```

## Wallet Screens

### Wallet Dashboard Screen

```typescript
// screens/WalletDashboardScreen.tsx
import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  RefreshControl,
  ActivityIndicator,
} from 'react-native';
import WalletService, { UserWalletBalance, ListenerWalletBalance } from '../services/WalletService';
import WalletCard from '../components/WalletCard';
import TransactionList from '../components/TransactionList';

const WalletDashboardScreen: React.FC = () => {
  const [userBalance, setUserBalance] = useState<UserWalletBalance | null>(null);
  const [listenerBalance, setListenerBalance] = useState<ListenerWalletBalance | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [isListener, setIsListener] = useState(false);

  useEffect(() => {
    loadWalletData();
  }, []);

  const loadWalletData = async () => {
    try {
      const [userWalletBalance, listenerWalletBalance] = await Promise.all([
        WalletService.getBalance(),
        WalletService.getListenerBalance().catch(() => null), // This will fail for non-listeners
      ]);
      setUserBalance(userWalletBalance);
      setListenerBalance(listenerWalletBalance);
      setIsListener(!!listenerWalletBalance);
    } catch (error) {
      console.error('Failed to load wallet data:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleRefresh = async () => {
    setRefreshing(true);
    await loadWalletData();
    setRefreshing(false);
  };

  const handleAddCoins = () => {
    // Navigate to add coins screen
  };

  const handleWithdraw = () => {
    // Navigate to withdrawal screen
  };

  const handleViewEarnings = () => {
    // Navigate to earnings screen
  };

  if (isLoading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#007AFF" />
      </View>
    );
  }

  if (!userBalance) {
    return (
      <View style={styles.errorContainer}>
        <Text style={styles.errorText}>Failed to load wallet data</Text>
        <TouchableOpacity style={styles.retryButton} onPress={loadWalletData}>
          <Text style={styles.retryButtonText}>Retry</Text>
        </TouchableOpacity>
      </View>
    );
  }

  return (
    <ScrollView
      style={styles.container}
      refreshControl={
        <RefreshControl refreshing={refreshing} onRefresh={handleRefresh} />
      }
    >
      <WalletCard 
        userBalance={userBalance} 
        listenerBalance={listenerBalance} 
        isListener={isListener} 
      />
      
      <View style={styles.actionsContainer}>
        <TouchableOpacity style={styles.actionButton} onPress={handleAddCoins}>
          <Text style={styles.actionButtonText}>Add Coins</Text>
        </TouchableOpacity>
        
        {isListener && (
          <TouchableOpacity style={styles.actionButton} onPress={handleWithdraw}>
            <Text style={styles.actionButtonText}>Withdraw</Text>
          </TouchableOpacity>
        )}
      </View>

      {isListener && listenerBalance && (
        <View style={styles.statsContainer}>
          <View style={styles.statItem}>
            <Text style={styles.statLabel}>Total Earned</Text>
            <Text style={styles.statValue}>₹{listenerBalance.total_earned.toFixed(2)}</Text>
          </View>
          
          <View style={styles.statItem}>
            <Text style={styles.statLabel}>Withdrawable</Text>
            <Text style={styles.statValue}>₹{listenerBalance.withdrawable_money.toFixed(2)}</Text>
          </View>
        </View>
      )}

      {isListener && (
        <TouchableOpacity style={styles.earningsButton} onPress={handleViewEarnings}>
          <Text style={styles.earningsButtonText}>View Earnings History</Text>
        </TouchableOpacity>
      )}
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
  errorContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 20,
  },
  errorText: {
    fontSize: 16,
    color: '#FF3B30',
    marginBottom: 20,
  },
  retryButton: {
    backgroundColor: '#007AFF',
    paddingHorizontal: 20,
    paddingVertical: 10,
    borderRadius: 8,
  },
  retryButtonText: {
    color: '#fff',
    fontWeight: 'bold',
  },
  actionsContainer: {
    flexDirection: 'row',
    padding: 20,
    justifyContent: 'space-around',
  },
  actionButton: {
    backgroundColor: '#007AFF',
    paddingHorizontal: 30,
    paddingVertical: 15,
    borderRadius: 8,
    flex: 1,
    marginHorizontal: 10,
    alignItems: 'center',
  },
  actionButtonText: {
    color: '#fff',
    fontWeight: 'bold',
    fontSize: 16,
  },
  statsContainer: {
    flexDirection: 'row',
    padding: 20,
    justifyContent: 'space-around',
  },
  statItem: {
    alignItems: 'center',
  },
  statLabel: {
    fontSize: 12,
    color: '#666',
    marginBottom: 5,
  },
  statValue: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#333',
  },
  earningsButton: {
    backgroundColor: '#fff',
    margin: 20,
    padding: 15,
    borderRadius: 8,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#ddd',
  },
  earningsButtonText: {
    color: '#007AFF',
    fontWeight: 'bold',
  },
});

export default WalletDashboardScreen;
```

### Wallet Card Component

```typescript
// components/WalletCard.tsx
import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { UserWalletBalance, ListenerWalletBalance } from '../services/WalletService';

interface WalletCardProps {
  userBalance: UserWalletBalance;
  listenerBalance?: ListenerWalletBalance | null;
  isListener: boolean;
}

const WalletCard: React.FC<WalletCardProps> = ({ userBalance, listenerBalance, isListener }) => {
  return (
    <View style={styles.card}>
      <View style={styles.header}>
        <Text style={styles.title}>Wallet Balance</Text>
        <Text style={styles.coins}>{userBalance.balance_coins} coins</Text>
      </View>
      
      {isListener && listenerBalance && (
        <View style={styles.balanceContainer}>
          <Text style={styles.balanceLabel}>Withdrawable Amount</Text>
          <Text style={styles.balanceAmount}>₹{listenerBalance.withdrawable_money.toFixed(2)}</Text>
        </View>
      )}
      
      <View style={styles.footer}>
        <Text style={styles.footerText}>
          {isListener 
            ? 'Available for withdrawal to bank account' 
            : 'Coins for making calls and other services'
          }
        </Text>
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  card: {
    backgroundColor: '#007AFF',
    margin: 20,
    padding: 20,
    borderRadius: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 20,
  },
  title: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#fff',
  },
  coins: {
    fontSize: 16,
    color: '#fff',
    backgroundColor: 'rgba(255,255,255,0.2)',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 20,
  },
  balanceContainer: {
    alignItems: 'center',
    marginBottom: 15,
  },
  balanceLabel: {
    fontSize: 14,
    color: 'rgba(255,255,255,0.8)',
    marginBottom: 5,
  },
  balanceAmount: {
    fontSize: 32,
    fontWeight: 'bold',
    color: '#fff',
  },
  footer: {
    alignItems: 'center',
  },
  footerText: {
    fontSize: 12,
    color: 'rgba(255,255,255,0.8)',
    textAlign: 'center',
  },
});

export default WalletCard;
```

### Add Coins Screen

```typescript
// screens/AddCoinsScreen.tsx
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
import WalletService, { AddCoinsRequest } from '../services/WalletService';

const AddCoinsScreen: React.FC = () => {
  const [formData, setFormData] = useState<AddCoinsRequest>({
    coins: 0,
    tx_type: 'purchase',
    money_amount: 0,
  });
  const [isLoading, setIsLoading] = useState(false);

  const coinPackages = [
    { coins: 100, price: 50, label: '100 Coins - ₹50' },
    { coins: 250, price: 125, label: '250 Coins - ₹125' },
    { coins: 500, price: 250, label: '500 Coins - ₹250' },
    { coins: 1000, price: 500, label: '1000 Coins - ₹500' },
  ];

  const handlePackageSelect = (package: typeof coinPackages[0]) => {
    setFormData({
      coins: package.coins,
      tx_type: 'purchase',
      money_amount: package.price,
    });
  };

  const handleCustomAmount = (coins: string) => {
    const coinsNum = parseInt(coins) || 0;
    setFormData({
      ...formData,
      coins: coinsNum,
      money_amount: coinsNum * 0.5, // 2:1 ratio
    });
  };

  const handleSubmit = async () => {
    if (formData.coins <= 0) {
      Alert.alert('Error', 'Please select a valid coin amount');
      return;
    }

    setIsLoading(true);
    try {
      const response = await WalletService.addCoins(formData);
      Alert.alert(
        'Success',
        `Successfully added ${response.coins_added} coins to your wallet!`,
        [{ text: 'OK', onPress: () => navigation.goBack() }]
      );
    } catch (error) {
      Alert.alert('Error', 'Failed to add coins. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <ScrollView style={styles.container}>
      <Text style={styles.title}>Add Coins to Wallet</Text>
      
      <View style={styles.packagesContainer}>
        <Text style={styles.sectionTitle}>Coin Packages</Text>
        {coinPackages.map((pkg, index) => (
          <TouchableOpacity
            key={index}
            style={[
              styles.packageButton,
              formData.coins === pkg.coins && styles.packageButtonSelected,
            ]}
            onPress={() => handlePackageSelect(pkg)}
          >
            <Text
              style={[
                styles.packageButtonText,
                formData.coins === pkg.coins && styles.packageButtonTextSelected,
              ]}
            >
              {pkg.label}
            </Text>
          </TouchableOpacity>
        ))}
      </View>

      <View style={styles.customContainer}>
        <Text style={styles.sectionTitle}>Custom Amount</Text>
        <TextInput
          style={styles.input}
          placeholder="Enter number of coins"
          value={formData.coins > 0 ? formData.coins.toString() : ''}
          onChangeText={handleCustomAmount}
          keyboardType="numeric"
        />
        {formData.money_amount > 0 && (
          <Text style={styles.priceText}>
            Cost: ₹{formData.money_amount.toFixed(2)}
          </Text>
        )}
      </View>

      <View style={styles.transactionTypeContainer}>
        <Text style={styles.sectionTitle}>Transaction Type</Text>
        <Picker
          selectedValue={formData.tx_type}
          onValueChange={(value) => setFormData({ ...formData, tx_type: value })}
          style={styles.picker}
        >
          <Picker.Item label="Purchase" value="purchase" />
          <Picker.Item label="Bonus" value="bonus" />
          <Picker.Item label="Referral Bonus" value="referral_bonus" />
        </Picker>
      </View>

      <TouchableOpacity
        style={[styles.submitButton, isLoading && styles.submitButtonDisabled]}
        onPress={handleSubmit}
        disabled={isLoading}
      >
        {isLoading ? (
          <ActivityIndicator color="#fff" />
        ) : (
          <Text style={styles.submitButtonText}>
            Add {formData.coins} Coins
          </Text>
        )}
      </TouchableOpacity>
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    textAlign: 'center',
    margin: 20,
  },
  packagesContainer: {
    backgroundColor: '#fff',
    margin: 20,
    padding: 15,
    borderRadius: 8,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    marginBottom: 15,
    color: '#333',
  },
  packageButton: {
    borderWidth: 1,
    borderColor: '#ddd',
    borderRadius: 8,
    padding: 15,
    marginBottom: 10,
    alignItems: 'center',
  },
  packageButtonSelected: {
    borderColor: '#007AFF',
    backgroundColor: '#E3F2FD',
  },
  packageButtonText: {
    fontSize: 16,
    color: '#333',
  },
  packageButtonTextSelected: {
    color: '#007AFF',
    fontWeight: 'bold',
  },
  customContainer: {
    backgroundColor: '#fff',
    margin: 20,
    padding: 15,
    borderRadius: 8,
  },
  input: {
    borderWidth: 1,
    borderColor: '#ddd',
    borderRadius: 8,
    padding: 12,
    fontSize: 16,
    marginBottom: 10,
  },
  priceText: {
    fontSize: 14,
    color: '#666',
    textAlign: 'center',
  },
  transactionTypeContainer: {
    backgroundColor: '#fff',
    margin: 20,
    padding: 15,
    borderRadius: 8,
  },
  picker: {
    backgroundColor: '#f9f9f9',
  },
  submitButton: {
    backgroundColor: '#007AFF',
    margin: 20,
    padding: 15,
    borderRadius: 8,
    alignItems: 'center',
  },
  submitButtonDisabled: {
    backgroundColor: '#ccc',
  },
  submitButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: 'bold',
  },
});

export default AddCoinsScreen;
```

### Withdrawal Screen

```typescript
// screens/WithdrawalScreen.tsx
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
} from 'react-native';
import WalletService, { WithdrawalRequest, BankDetailsResponse } from '../services/WalletService';

const WithdrawalScreen: React.FC = () => {
  const [amount, setAmount] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [bankDetails, setBankDetails] = useState<BankDetailsResponse | null>(null);
  const [balance, setBalance] = useState(0);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [listenerBalance, bankStatus] = await Promise.all([
        WalletService.getListenerBalance(),
        WalletService.getBankDetailsStatus(),
      ]);
      setBalance(listenerBalance.withdrawable_money);
      setBankDetails(bankStatus);
    } catch (error) {
      Alert.alert('Error', 'Failed to load wallet data');
    }
  };

  const handleWithdraw = async () => {
    const withdrawAmount = parseFloat(amount);
    
    if (!withdrawAmount || withdrawAmount <= 0) {
      Alert.alert('Error', 'Please enter a valid amount');
      return;
    }

    if (withdrawAmount > balance) {
      Alert.alert('Error', 'Insufficient balance');
      return;
    }

    if (!bankDetails?.has_bank_details) {
      Alert.alert('Error', 'Please add your bank details first');
      return;
    }

    setIsLoading(true);
    try {
      const response = await WalletService.requestWithdrawal({ amount: withdrawAmount });
      Alert.alert(
        'Success',
        `Withdrawal request of ₹${withdrawAmount.toFixed(2)} submitted successfully`,
        [{ text: 'OK', onPress: () => navigation.goBack() }]
      );
    } catch (error) {
      Alert.alert('Error', 'Failed to process withdrawal request');
    } finally {
      setIsLoading(false);
    }
  };

  const handleAddBankDetails = () => {
    // Navigate to bank details screen
  };

  return (
    <ScrollView style={styles.container}>
      <Text style={styles.title}>Request Withdrawal</Text>
      
      <View style={styles.balanceContainer}>
        <Text style={styles.balanceLabel}>Available Balance</Text>
        <Text style={styles.balanceAmount}>₹{balance.toFixed(2)}</Text>
      </View>

      <View style={styles.inputContainer}>
        <Text style={styles.inputLabel}>Withdrawal Amount</Text>
        <TextInput
          style={styles.input}
          placeholder="Enter amount"
          value={amount}
          onChangeText={setAmount}
          keyboardType="numeric"
        />
        <Text style={styles.inputHint}>Minimum withdrawal: ₹100</Text>
      </View>

      <View style={styles.bankDetailsContainer}>
        <Text style={styles.sectionTitle}>Bank Details</Text>
        {bankDetails?.has_bank_details ? (
          <View style={styles.bankDetailsStatus}>
            <Text style={styles.bankDetailsText}>✓ Bank details configured</Text>
          </View>
        ) : (
          <View style={styles.bankDetailsStatus}>
            <Text style={styles.bankDetailsText}>⚠ Bank details not configured</Text>
            <TouchableOpacity style={styles.addBankButton} onPress={handleAddBankDetails}>
              <Text style={styles.addBankButtonText}>Add Bank Details</Text>
            </TouchableOpacity>
          </View>
        )}
      </View>

      <TouchableOpacity
        style={[
          styles.submitButton,
          (isLoading || !bankDetails?.has_bank_details) && styles.submitButtonDisabled,
        ]}
        onPress={handleWithdraw}
        disabled={isLoading || !bankDetails?.has_bank_details}
      >
        {isLoading ? (
          <ActivityIndicator color="#fff" />
        ) : (
          <Text style={styles.submitButtonText}>Request Withdrawal</Text>
        )}
      </TouchableOpacity>

      <View style={styles.infoContainer}>
        <Text style={styles.infoTitle}>Important Information</Text>
        <Text style={styles.infoText}>
          • Withdrawal requests are processed within 24-48 hours
        </Text>
        <Text style={styles.infoText}>
          • Minimum withdrawal amount is ₹100
        </Text>
        <Text style={styles.infoText}>
          • Bank details must be verified before withdrawal
        </Text>
      </View>
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    textAlign: 'center',
    margin: 20,
  },
  balanceContainer: {
    backgroundColor: '#fff',
    margin: 20,
    padding: 20,
    borderRadius: 8,
    alignItems: 'center',
  },
  balanceLabel: {
    fontSize: 16,
    color: '#666',
    marginBottom: 5,
  },
  balanceAmount: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#007AFF',
  },
  inputContainer: {
    backgroundColor: '#fff',
    margin: 20,
    padding: 15,
    borderRadius: 8,
  },
  inputLabel: {
    fontSize: 16,
    fontWeight: 'bold',
    marginBottom: 10,
    color: '#333',
  },
  input: {
    borderWidth: 1,
    borderColor: '#ddd',
    borderRadius: 8,
    padding: 12,
    fontSize: 16,
    marginBottom: 5,
  },
  inputHint: {
    fontSize: 12,
    color: '#666',
  },
  bankDetailsContainer: {
    backgroundColor: '#fff',
    margin: 20,
    padding: 15,
    borderRadius: 8,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    marginBottom: 15,
    color: '#333',
  },
  bankDetailsStatus: {
    alignItems: 'center',
  },
  bankDetailsText: {
    fontSize: 16,
    marginBottom: 10,
  },
  addBankButton: {
    backgroundColor: '#007AFF',
    paddingHorizontal: 20,
    paddingVertical: 10,
    borderRadius: 8,
  },
  addBankButtonText: {
    color: '#fff',
    fontWeight: 'bold',
  },
  submitButton: {
    backgroundColor: '#007AFF',
    margin: 20,
    padding: 15,
    borderRadius: 8,
    alignItems: 'center',
  },
  submitButtonDisabled: {
    backgroundColor: '#ccc',
  },
  submitButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: 'bold',
  },
  infoContainer: {
    backgroundColor: '#fff',
    margin: 20,
    padding: 15,
    borderRadius: 8,
  },
  infoTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    marginBottom: 10,
    color: '#333',
  },
  infoText: {
    fontSize: 14,
    color: '#666',
    marginBottom: 5,
  },
});

export default WithdrawalScreen;
```

## Best Practices

### Wallet Management

1. **Balance Validation**: Always check balance before operations
2. **Input Validation**: Validate amounts and transaction types
3. **Error Handling**: Provide clear error messages for all operations
4. **Transaction Tracking**: Keep track of transaction IDs for reference

### User Experience

1. **Loading States**: Show loading indicators during operations
2. **Confirmation Dialogs**: Confirm important actions like withdrawals
3. **Real-time Updates**: Refresh balance after transactions
4. **Offline Handling**: Handle network connectivity issues gracefully

### Security

1. **Token Management**: Store tokens securely
2. **Input Sanitization**: Sanitize all user inputs
3. **Amount Limits**: Implement reasonable limits for transactions
4. **Audit Trail**: Maintain complete transaction history

## Next Steps

- Learn about [React Native Wallets](./react-native-wallets)
- Explore [React Native Calls](./react-native-calls)
- Check out [React Native Feeds](./react-native-feeds)
