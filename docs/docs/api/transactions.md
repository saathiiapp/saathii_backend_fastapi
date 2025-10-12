---
sidebar_position: 4
title: Transactions API
description: Transaction history and financial tracking
---

# Transactions API

The Transactions API provides comprehensive transaction history and financial tracking for users and listeners.

## Overview

- **Transaction History**: Complete audit trail of all financial operations
- **User Transactions**: Track coins spent and money spent on calls
- **Listener Transactions**: Track earnings from calls and other sources
- **Financial Analytics**: Detailed breakdown of income and expenses

## Endpoints

### Get User Transaction History

Get user's transaction history showing coins spent and money spent on calls.

**Endpoint:** `GET /transactions/user`

**Headers:**
```
Authorization: Bearer <access_token>
```

**Query Parameters:**
- `page`: Page number (default: 1)
- `per_page`: Items per page (default: 20, max: 100)
- `tx_type`: Filter by transaction type (optional)
  - `"purchase"` - Coin purchases
  - `"spend"` - Coins spent on calls
  - `"earn"` - Coins earned
  - `"withdraw"` - Money withdrawals
  - `"bonus"` - Bonus coins
  - `"referral_bonus"` - Referral bonus

**Response:**
```json
{
  "transactions": [
    {
      "transaction_id": 123,
      "tx_type": "spend",
      "coins_change": -50,
      "money_change": -25.00,
      "description": "Call payment - 5 minutes",
      "call_id": 456,
      "created_at": "2024-01-15T10:30:00Z"
    },
    {
      "transaction_id": 124,
      "tx_type": "purchase",
      "coins_change": 100,
      "money_change": 50.00,
      "description": "Coin purchase",
      "call_id": null,
      "created_at": "2024-01-15T09:00:00Z"
    }
  ],
  "summary": {
    "total_coins_spent": 500,
    "total_money_spent": 250.00,
    "total_coins_earned": 100,
    "total_money_earned": 50.00
  },
  "current_balance": 600,
  "page": 1,
  "per_page": 20,
  "total": 25,
  "has_next": true,
  "has_previous": false
}
```

**Fields:**
- `transaction_id`: Unique transaction identifier
- `tx_type`: Transaction type
- `coins_change`: Change in coins (positive = credit, negative = debit)
- `money_change`: Change in money (positive = credit, negative = debit)
- `description`: Human-readable transaction description
- `call_id`: Associated call ID (if applicable)
- `created_at`: Transaction timestamp

### Get Listener Transaction History

Get listener's transaction history showing earnings from calls.

**Endpoint:** `GET /transactions/listener`

**Headers:**
```
Authorization: Bearer <access_token>
```

**Query Parameters:**
- `page`: Page number (default: 1)
- `per_page`: Items per page (default: 20, max: 100)
- `tx_type`: Filter by transaction type (optional)

**Response:**
```json
{
  "transactions": [
    {
      "transaction_id": 125,
      "tx_type": "earn",
      "coins_change": 50,
      "money_change": 25.00,
      "description": "Call earnings - 5 minutes",
      "call_id": 456,
      "created_at": "2024-01-15T10:30:00Z"
    },
    {
      "transaction_id": 126,
      "tx_type": "withdraw",
      "coins_change": 0,
      "money_change": -100.00,
      "description": "Withdrawal to bank account",
      "call_id": null,
      "created_at": "2024-01-15T08:00:00Z"
    }
  ],
  "summary": {
    "total_coins_earned": 2000,
    "total_money_earned": 1000.00,
    "total_withdrawn": 500.00,
    "available_balance": 500.00
  },
  "current_balance": 1500,
  "page": 1,
  "per_page": 20,
  "total": 15,
  "has_next": false,
  "has_previous": false
}
```

## Transaction Types

### Purchase Transactions
- **Type**: `"purchase"`
- **Description**: Coin purchases with real money
- **Coins Change**: Positive (coins added)
- **Money Change**: Positive (money spent)

### Spend Transactions
- **Type**: `"spend"`
- **Description**: Coins spent on calls
- **Coins Change**: Negative (coins deducted)
- **Money Change**: Negative (money spent)

### Earn Transactions
- **Type**: `"earn"`
- **Description**: Coins earned from calls (listeners)
- **Coins Change**: Positive (coins earned)
- **Money Change**: Positive (money earned)

### Withdraw Transactions
- **Type**: `"withdraw"`
- **Description**: Money withdrawn to bank account
- **Coins Change**: Zero (no coin change)
- **Money Change**: Negative (money withdrawn)

### Bonus Transactions
- **Type**: `"bonus"`
- **Description**: Free bonus coins
- **Coins Change**: Positive (coins added)
- **Money Change**: Zero (no money involved)

### Referral Bonus Transactions
- **Type**: `"referral_bonus"`
- **Description**: Referral reward coins
- **Coins Change**: Positive (coins added)
- **Money Change**: Zero (no money involved)

## Error Handling

### Common Error Responses

**Invalid Page (400):**
```json
{
  "detail": "Page must be a positive integer"
}
```

**Invalid Per Page (400):**
```json
{
  "detail": "Per page must be between 1 and 100"
}
```

**Invalid Transaction Type (400):**
```json
{
  "detail": "Invalid transaction type"
}
```

**Wallet Not Found (404):**
```json
{
  "detail": "User wallet not found"
}
```

## Integration Examples

### React Native Integration

```typescript
// Get user transaction history
const getUserTransactions = async (token: string, page: number = 1, txType?: string) => {
  const params = new URLSearchParams({
    page: page.toString(),
    per_page: '20'
  });
  
  if (txType) {
    params.append('tx_type', txType);
  }
  
  const response = await fetch(`http://localhost:8000/transactions/user?${params}`, {
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    }
  });
  return response.json();
};

// Get listener transaction history
const getListenerTransactions = async (token: string, page: number = 1) => {
  const params = new URLSearchParams({
    page: page.toString(),
    per_page: '20'
  });
  
  const response = await fetch(`http://localhost:8000/transactions/listener?${params}`, {
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    }
  });
  return response.json();
};
```

### cURL Examples

**Get User Transactions:**
```bash
curl -X GET 'http://localhost:8000/transactions/user?page=1&per_page=20' \
  -H 'Authorization: Bearer <access_token>'
```

**Get User Transactions (Filtered):**
```bash
curl -X GET 'http://localhost:8000/transactions/user?page=1&per_page=20&tx_type=spend' \
  -H 'Authorization: Bearer <access_token>'
```

**Get Listener Transactions:**
```bash
curl -X GET 'http://localhost:8000/transactions/listener?page=1&per_page=20' \
  -H 'Authorization: Bearer <access_token>'
```

## Best Practices

### Transaction Management

1. **Pagination**: Always use pagination for large transaction lists
2. **Filtering**: Use transaction type filters for specific views
3. **Caching**: Cache recent transactions locally
4. **Real-time Updates**: Refresh transaction lists after operations

### Performance

1. **Page Size**: Use appropriate page sizes (20-50 items)
2. **Lazy Loading**: Load more transactions as needed
3. **Filtering**: Use server-side filtering instead of client-side
4. **Caching**: Cache transaction summaries

### User Experience

1. **Loading States**: Show loading indicators during data fetch
2. **Error Handling**: Display user-friendly error messages
3. **Empty States**: Handle empty transaction lists gracefully
4. **Refresh**: Provide pull-to-refresh functionality

## Next Steps

- Learn about [Wallets API](./wallets) for wallet management
- Explore [Call Management API](./call-management) for call operations
- Check out [User Management API](./user-management) for profile management
