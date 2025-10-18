# React Native Help & Support Integration

This guide shows how to integrate the Help & Support API into your React Native application, including creating support tickets, viewing ticket history, and handling different issue types.

## Table of Contents

- [Setup](#setup)
- [Creating Support Tickets](#creating-support-tickets)
- [Viewing Ticket History](#viewing-ticket-history)
- [Admin Interface](#admin-interface)
- [Error Handling](#error-handling)
- [Complete Examples](#complete-examples)

## Setup

### Install Dependencies

```bash
npm install axios react-native-image-picker
# or
yarn add axios react-native-image-picker
```

### API Service Setup

```javascript
// services/helpSupportAPI.js
import axios from 'axios';

const API_BASE_URL = 'https://your-api-domain.com';

const helpSupportAPI = axios.create({
  baseURL: `${API_BASE_URL}/both/support`,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add auth token interceptor
helpSupportAPI.interceptors.request.use((config) => {
  const token = getAuthToken(); // Your token retrieval function
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export default helpSupportAPI;
```

## Creating Support Tickets

### Support Ticket Service

```javascript
// services/supportTicketService.js
import helpSupportAPI from './helpSupportAPI';

export const createSupportTicket = async (ticketData) => {
  try {
    const response = await helpSupportAPI.post('/tickets', ticketData);
    return response.data;
  } catch (error) {
    throw new Error(error.response?.data?.detail || 'Failed to create support ticket');
  }
};

export const getMyTickets = async (filters = {}) => {
  try {
    const params = new URLSearchParams();
    Object.keys(filters).forEach(key => {
      if (filters[key] !== null && filters[key] !== undefined) {
        params.append(key, filters[key]);
      }
    });
    
    const response = await helpSupportAPI.get(`/tickets?${params.toString()}`);
    return response.data;
  } catch (error) {
    throw new Error(error.response?.data?.detail || 'Failed to fetch tickets');
  }
};

export const getTicketById = async (ticketId) => {
  try {
    const response = await helpSupportAPI.get(`/tickets/${ticketId}`);
    return response.data;
  } catch (error) {
    throw new Error(error.response?.data?.detail || 'Failed to fetch ticket');
  }
};
```

### Support Ticket Form Component

```javascript
// components/SupportTicketForm.js
import React, { useState } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  Alert,
  ScrollView,
  StyleSheet,
} from 'react-native';
import { Picker } from '@react-native-picker/picker';
import { createSupportTicket } from '../services/supportTicketService';

const SupportTicketForm = ({ onTicketCreated }) => {
  const [formData, setFormData] = useState({
    issue_type: 'other',
    issue: '',
    description: '',
    require_call: false,
    call_id: null,
    transaction_id: null,
  });
  const [loading, setLoading] = useState(false);

  const issueTypes = [
    { label: 'Call Session Support', value: 'call_session_support' },
    { label: 'Payment Support', value: 'payment_support' },
    { label: 'Other', value: 'other' },
  ];

  const handleSubmit = async () => {
    if (!formData.issue.trim()) {
      Alert.alert('Error', 'Please enter an issue description');
      return;
    }

    // Validate required fields based on issue type
    if (formData.issue_type === 'call_session_support' && !formData.call_id) {
      Alert.alert('Error', 'Call ID is required for call session support');
      return;
    }

    if (formData.issue_type === 'payment_support' && !formData.transaction_id) {
      Alert.alert('Error', 'Transaction ID is required for payment support');
      return;
    }

    setLoading(true);
    try {
      const ticket = await createSupportTicket(formData);
      Alert.alert('Success', 'Support ticket created successfully');
      onTicketCreated?.(ticket);
      // Reset form
      setFormData({
        issue_type: 'other',
        issue: '',
        description: '',
        require_call: false,
        call_id: null,
        transaction_id: null,
      });
    } catch (error) {
      Alert.alert('Error', error.message);
    } finally {
      setLoading(false);
    }
  };

  const renderAdditionalFields = () => {
    switch (formData.issue_type) {
      case 'call_session_support':
        return (
          <View style={styles.fieldContainer}>
            <Text style={styles.label}>Call ID *</Text>
            <TextInput
              style={styles.input}
              value={formData.call_id?.toString() || ''}
              onChangeText={(text) => setFormData({ ...formData, call_id: parseInt(text) || null })}
              placeholder="Enter call ID"
              keyboardType="numeric"
            />
          </View>
        );
      case 'payment_support':
        return (
          <View style={styles.fieldContainer}>
            <Text style={styles.label}>Transaction ID *</Text>
            <TextInput
              style={styles.input}
              value={formData.transaction_id?.toString() || ''}
              onChangeText={(text) => setFormData({ ...formData, transaction_id: parseInt(text) || null })}
              placeholder="Enter transaction ID"
              keyboardType="numeric"
            />
          </View>
        );
      default:
        return null;
    }
  };

  return (
    <ScrollView style={styles.container}>
      <View style={styles.fieldContainer}>
        <Text style={styles.label}>Issue Type *</Text>
        <View style={styles.pickerContainer}>
          <Picker
            selectedValue={formData.issue_type}
            onValueChange={(value) => setFormData({ ...formData, issue_type: value })}
            style={styles.picker}
          >
            {issueTypes.map((type) => (
              <Picker.Item key={type.value} label={type.label} value={type.value} />
            ))}
          </Picker>
        </View>
      </View>

      {renderAdditionalFields()}

      <View style={styles.fieldContainer}>
        <Text style={styles.label}>Issue Description *</Text>
        <TextInput
          style={[styles.input, styles.textArea]}
          value={formData.issue}
          onChangeText={(text) => setFormData({ ...formData, issue: text })}
          placeholder="Briefly describe your issue"
          multiline
          numberOfLines={3}
        />
      </View>

      <View style={styles.fieldContainer}>
        <Text style={styles.label}>Detailed Description</Text>
        <TextInput
          style={[styles.input, styles.textArea]}
          value={formData.description}
          onChangeText={(text) => setFormData({ ...formData, description: text })}
          placeholder="Provide more details about your issue"
          multiline
          numberOfLines={4}
        />
      </View>

      <View style={styles.fieldContainer}>
        <TouchableOpacity
          style={styles.checkboxContainer}
          onPress={() => setFormData({ ...formData, require_call: !formData.require_call })}
        >
          <View style={[styles.checkbox, formData.require_call && styles.checkboxChecked]}>
            {formData.require_call && <Text style={styles.checkmark}>✓</Text>}
          </View>
          <Text style={styles.checkboxLabel}>Require a call for support</Text>
        </TouchableOpacity>
      </View>

      <TouchableOpacity
        style={[styles.submitButton, loading && styles.submitButtonDisabled]}
        onPress={handleSubmit}
        disabled={loading}
      >
        <Text style={styles.submitButtonText}>
          {loading ? 'Creating...' : 'Create Support Ticket'}
        </Text>
      </TouchableOpacity>
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    padding: 16,
  },
  fieldContainer: {
    marginBottom: 16,
  },
  label: {
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 8,
    color: '#333',
  },
  input: {
    borderWidth: 1,
    borderColor: '#ddd',
    borderRadius: 8,
    padding: 12,
    fontSize: 16,
    backgroundColor: '#fff',
  },
  textArea: {
    height: 80,
    textAlignVertical: 'top',
  },
  pickerContainer: {
    borderWidth: 1,
    borderColor: '#ddd',
    borderRadius: 8,
    backgroundColor: '#fff',
  },
  picker: {
    height: 50,
  },
  checkboxContainer: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  checkbox: {
    width: 20,
    height: 20,
    borderWidth: 2,
    borderColor: '#ddd',
    borderRadius: 4,
    marginRight: 12,
    alignItems: 'center',
    justifyContent: 'center',
  },
  checkboxChecked: {
    backgroundColor: '#007AFF',
    borderColor: '#007AFF',
  },
  checkmark: {
    color: '#fff',
    fontSize: 14,
    fontWeight: 'bold',
  },
  checkboxLabel: {
    fontSize: 16,
    color: '#333',
  },
  submitButton: {
    backgroundColor: '#007AFF',
    padding: 16,
    borderRadius: 8,
    alignItems: 'center',
    marginTop: 16,
  },
  submitButtonDisabled: {
    backgroundColor: '#ccc',
  },
  submitButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
});

export default SupportTicketForm;
```

## Viewing Ticket History

### Ticket List Component

```javascript
// components/SupportTicketList.js
import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  FlatList,
  TouchableOpacity,
  RefreshControl,
  StyleSheet,
} from 'react-native';
import { getMyTickets } from '../services/supportTicketService';

const SupportTicketList = ({ navigation }) => {
  const [tickets, setTickets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [filters, setFilters] = useState({
    status: null,
    issue_type: null,
  });

  useEffect(() => {
    loadTickets();
  }, [filters]);

  const loadTickets = async () => {
    try {
      const data = await getMyTickets(filters);
      setTickets(data.tickets);
    } catch (error) {
      console.error('Failed to load tickets:', error);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  const onRefresh = () => {
    setRefreshing(true);
    loadTickets();
  };

  const getStatusColor = (status) => {
    return status === 'active' ? '#FF9500' : '#34C759';
  };

  const getIssueTypeLabel = (issueType) => {
    const labels = {
      call_session_support: 'Call Session',
      payment_support: 'Payment',
      other: 'Other',
    };
    return labels[issueType] || issueType;
  };

  const renderTicket = ({ item }) => (
    <TouchableOpacity
      style={styles.ticketCard}
      onPress={() => navigation.navigate('TicketDetail', { ticketId: item.support_id })}
    >
      <View style={styles.ticketHeader}>
        <Text style={styles.ticketId}>#{item.support_id}</Text>
        <View style={[styles.statusBadge, { backgroundColor: getStatusColor(item.status) }]}>
          <Text style={styles.statusText}>{item.status.toUpperCase()}</Text>
        </View>
      </View>
      
      <Text style={styles.issueType}>{getIssueTypeLabel(item.issue_type)}</Text>
      <Text style={styles.issueText} numberOfLines={2}>{item.issue}</Text>
      
      <View style={styles.ticketFooter}>
        <Text style={styles.dateText}>
          {new Date(item.created_at).toLocaleDateString()}
        </Text>
        {item.require_call && (
          <Text style={styles.callRequired}>📞 Call Required</Text>
        )}
      </View>
    </TouchableOpacity>
  );

  if (loading) {
    return (
      <View style={styles.centerContainer}>
        <Text>Loading tickets...</Text>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <FlatList
        data={tickets}
        renderItem={renderTicket}
        keyExtractor={(item) => item.support_id.toString()}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
        }
        ListEmptyComponent={
          <View style={styles.emptyContainer}>
            <Text style={styles.emptyText}>No support tickets found</Text>
          </View>
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
  centerContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  ticketCard: {
    backgroundColor: '#fff',
    margin: 8,
    padding: 16,
    borderRadius: 8,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  ticketHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  ticketId: {
    fontSize: 16,
    fontWeight: '600',
    color: '#333',
  },
  statusBadge: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 12,
  },
  statusText: {
    color: '#fff',
    fontSize: 12,
    fontWeight: '600',
  },
  issueType: {
    fontSize: 14,
    color: '#666',
    marginBottom: 4,
  },
  issueText: {
    fontSize: 16,
    color: '#333',
    marginBottom: 8,
  },
  ticketFooter: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  dateText: {
    fontSize: 12,
    color: '#999',
  },
  callRequired: {
    fontSize: 12,
    color: '#007AFF',
    fontWeight: '500',
  },
  emptyContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 32,
  },
  emptyText: {
    fontSize: 16,
    color: '#666',
  },
});

export default SupportTicketList;
```

### Ticket Detail Component

```javascript
// components/SupportTicketDetail.js
import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  ScrollView,
  StyleSheet,
  Alert,
} from 'react-native';
import { getTicketById } from '../services/supportTicketService';

const SupportTicketDetail = ({ route }) => {
  const { ticketId } = route.params;
  const [ticket, setTicket] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadTicket();
  }, [ticketId]);

  const loadTicket = async () => {
    try {
      const data = await getTicketById(ticketId);
      setTicket(data);
    } catch (error) {
      Alert.alert('Error', error.message);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <View style={styles.centerContainer}>
        <Text>Loading ticket details...</Text>
      </View>
    );
  }

  if (!ticket) {
    return (
      <View style={styles.centerContainer}>
        <Text>Ticket not found</Text>
      </View>
    );
  }

  return (
    <ScrollView style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.ticketId}>Ticket #{ticket.support_id}</Text>
        <View style={[styles.statusBadge, { backgroundColor: ticket.status === 'active' ? '#FF9500' : '#34C759' }]}>
          <Text style={styles.statusText}>{ticket.status.toUpperCase()}</Text>
        </View>
      </View>

      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Issue Type</Text>
        <Text style={styles.sectionContent}>{ticket.issue_type.replace('_', ' ').toUpperCase()}</Text>
      </View>

      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Issue</Text>
        <Text style={styles.sectionContent}>{ticket.issue}</Text>
      </View>

      {ticket.description && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Description</Text>
          <Text style={styles.sectionContent}>{ticket.description}</Text>
        </View>
      )}

      {ticket.call_id && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Call ID</Text>
          <Text style={styles.sectionContent}>{ticket.call_id}</Text>
        </View>
      )}

      {ticket.transaction_id && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Transaction ID</Text>
          <Text style={styles.sectionContent}>{ticket.transaction_id}</Text>
        </View>
      )}

      {ticket.require_call && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Call Required</Text>
          <Text style={styles.sectionContent}>Yes - A support call is requested</Text>
        </View>
      )}

      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Created</Text>
        <Text style={styles.sectionContent}>
          {new Date(ticket.created_at).toLocaleString()}
        </Text>
      </View>

      {ticket.resolved_at && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Resolved</Text>
          <Text style={styles.sectionContent}>
            {new Date(ticket.resolved_at).toLocaleString()}
          </Text>
        </View>
      )}

      {ticket.admin_notes && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Admin Notes</Text>
          <Text style={styles.sectionContent}>{ticket.admin_notes}</Text>
        </View>
      )}
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  centerContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 16,
    backgroundColor: '#fff',
    marginBottom: 8,
  },
  ticketId: {
    fontSize: 18,
    fontWeight: '600',
    color: '#333',
  },
  statusBadge: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 16,
  },
  statusText: {
    color: '#fff',
    fontSize: 12,
    fontWeight: '600',
  },
  section: {
    backgroundColor: '#fff',
    padding: 16,
    marginBottom: 8,
  },
  sectionTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: '#666',
    marginBottom: 4,
  },
  sectionContent: {
    fontSize: 16,
    color: '#333',
  },
});

export default SupportTicketDetail;
```

## Admin Interface

### Admin Ticket List (No Auth Required)

```javascript
// services/adminAPI.js
import axios from 'axios';

const adminAPI = axios.create({
  baseURL: 'https://your-api-domain.com/admin/support',
  headers: {
    'Content-Type': 'application/json',
  },
});

export const getAdminTickets = async (filters = {}) => {
  try {
    const params = new URLSearchParams();
    Object.keys(filters).forEach(key => {
      if (filters[key] !== null && filters[key] !== undefined) {
        params.append(key, filters[key]);
      }
    });
    
    const response = await adminAPI.get(`/tickets?${params.toString()}`);
    return response.data;
  } catch (error) {
    throw new Error(error.response?.data?.detail || 'Failed to fetch admin tickets');
  }
};
```

## Error Handling

### Error Handler Hook

```javascript
// hooks/useErrorHandler.js
import { useState, useCallback } from 'react';
import { Alert } from 'react-native';

export const useErrorHandler = () => {
  const [error, setError] = useState(null);

  const handleError = useCallback((error, customMessage) => {
    console.error('Error:', error);
    const message = customMessage || error.message || 'An unexpected error occurred';
    setError(message);
    Alert.alert('Error', message);
  }, []);

  const clearError = useCallback(() => {
    setError(null);
  }, []);

  return { error, handleError, clearError };
};
```

## Complete Examples

### Navigation Setup

```javascript
// App.js
import React from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { createStackNavigator } from '@react-navigation/stack';
import SupportTicketForm from './components/SupportTicketForm';
import SupportTicketList from './components/SupportTicketList';
import SupportTicketDetail from './components/SupportTicketDetail';

const Stack = createStackNavigator();

export default function App() {
  return (
    <NavigationContainer>
      <Stack.Navigator>
        <Stack.Screen 
          name="SupportTickets" 
          component={SupportTicketList} 
          options={{ title: 'Support Tickets' }}
        />
        <Stack.Screen 
          name="CreateTicket" 
          component={SupportTicketForm} 
          options={{ title: 'Create Ticket' }}
        />
        <Stack.Screen 
          name="TicketDetail" 
          component={SupportTicketDetail} 
          options={{ title: 'Ticket Details' }}
        />
      </Stack.Navigator>
    </NavigationContainer>
  );
}
```

### Usage in Your App

```javascript
// screens/SupportScreen.js
import React from 'react';
import { View, TouchableOpacity, Text, StyleSheet } from 'react-native';
import { useNavigation } from '@react-navigation/native';

const SupportScreen = () => {
  const navigation = useNavigation();

  return (
    <View style={styles.container}>
      <TouchableOpacity
        style={styles.button}
        onPress={() => navigation.navigate('CreateTicket')}
      >
        <Text style={styles.buttonText}>Create Support Ticket</Text>
      </TouchableOpacity>
      
      <TouchableOpacity
        style={styles.button}
        onPress={() => navigation.navigate('SupportTickets')}
      >
        <Text style={styles.buttonText}>View My Tickets</Text>
      </TouchableOpacity>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 20,
  },
  button: {
    backgroundColor: '#007AFF',
    padding: 16,
    borderRadius: 8,
    marginVertical: 8,
    minWidth: 200,
    alignItems: 'center',
  },
  buttonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
});

export default SupportScreen;
```

This comprehensive guide provides everything needed to integrate the Help & Support API into your React Native application, including form handling, validation, error management, and a complete user interface.
