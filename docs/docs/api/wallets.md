---
sidebar_position: 3
title: Wallets API
description: Wallet management and coin operations
---

# Wallets API

The Wallets API provides comprehensive wallet management, coin operations, and financial tracking for users.

## Overview

- **Coin Management**: Add, track, and manage virtual coins
- **Financial Tracking**: Monitor earnings, withdrawals, and transactions
- **Bank Integration**: Manage bank details for withdrawals
- **Transaction History**: Complete audit trail of all wallet operations

## Endpoints

### Get Wallet Balance

Retrieve the current user's wallet balance and financial summary.

**Endpoint:** `GET /wallet/balance`

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response:**
```json
{
  "user_id": 123,
  "balance_coins": 500,
  "withdrawable_money": 250.50,
  "total_earned": 1000.00,
  "total_withdrawn": 200.00,
  "pending_withdrawals": 50.00
}
```

**Fields:**
- `user_id`: User identifier
- `balance_coins`: Current coin balance
- `withdrawable_money`: Money available for withdrawal
- `total_earned`: Total money earned from calls
- `total_withdrawn`: Total money withdrawn
- `pending_withdrawals`: Pending withdrawal requests

### Add Coins to Wallet

Add coins to the user's wallet with transaction tracking.

**Endpoint:** `POST /wallet/add-coins`

**Headers:**
```
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Request Body:**
```json
{
  "coins": 100,
  "tx_type": "purchase",
  "money_amount": 50.00
}
```

**Fields:**
- `coins`: Number of coins to add (required, must be positive)
- `tx_type`: Transaction type (optional, default: "purchase")
  - `"purchase"` - Coin purchase
  - `"bonus"` - Bonus coins
  - `"referral_bonus"` - Referral bonus
- `money_amount`: Money amount associated with transaction (optional, default: 0.0)

**Response:**
```json
{
  "transaction_id": 123,
  "coins_added": 100,
  "money_amount": 50.00,
  "new_balance": 600,
  "message": "Successfully added 100 coins to wallet (₹50.00)",
  "created_at": "2024-01-15T10:30:00Z"
}
```

**Transaction Types:**
- **purchase**: Regular coin purchase with money
- **bonus**: Free bonus coins (no money involved)
- **referral_bonus**: Referral reward coins

### Get Call Earnings

Get listener's earnings from calls.

**Endpoint:** `GET /wallet/earnings`

**Headers:**
```
Authorization: Bearer <access_token>
```

**Query Parameters:**
- `page`: Page number (default: 1)
- `per_page`: Items per page (default: 20, max: 100)

**Response:**
```json
{
  "earnings": [
    {
      "call_id": 456,
      "user_id": 123,
      "coins_earned": 50,
      "money_earned": 25.00,
      "duration_minutes": 5,
      "created_at": "2024-01-15T10:30:00Z"
    }
  ],
  "total_earnings": 1000.00,
  "total_coins": 2000,
  "page": 1,
  "per_page": 20,
  "has_next": false,
  "has_previous": false
}
```

### Request Withdrawal

Request withdrawal from wallet to bank account.

**Endpoint:** `POST /wallet/withdraw`

**Headers:**
```
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Request Body:**
```json
{
  "amount": 100.00
}
```

**Fields:**
- `amount`: Amount to withdraw (required, must be positive)

**Response:**
```json
{
  "transaction_id": 123,
  "amount": 100.00,
  "message": "Withdrawal request of ₹100.00 submitted successfully",
  "created_at": "2024-01-15T10:30:00Z"
}
```

### Get Withdrawal History

Get user's withdrawal history.

**Endpoint:** `GET /wallet/withdrawals`

**Headers:**
```
Authorization: Bearer <access_token>
```

**Query Parameters:**
- `page`: Page number (default: 1)
- `per_page`: Items per page (default: 20, max: 100)

**Response:**
```json
{
  "withdrawals": [
    {
      "transaction_id": 123,
      "amount": 100.00,
      "created_at": "2024-01-15T10:30:00Z",
      "status": "pending"
    }
  ],
  "total_withdrawn": 500.00,
  "pending_amount": 100.00,
  "page": 1,
  "per_page": 20,
  "has_next": false,
  "has_previous": false
}
```

### Update Bank Details

Update bank account details for withdrawals.

**Endpoint:** `PUT /wallet/bank-details`

**Headers:**
```
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Request Body:**
```json
{
  "payout_account": {
    "account_holder_name": "John Doe",
    "account_number": "1234567890",
    "ifsc_code": "SBIN0001234",
    "bank_name": "State Bank of India"
  }
}
```

**Response:**
```json
{
  "has_bank_details": true,
  "message": "Bank details updated successfully"
}
```

### Get Bank Details Status

Check if user has bank details configured.

**Endpoint:** `GET /wallet/bank-details`

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response:**
```json
{
  "has_bank_details": true,
  "message": "Bank details are configured"
}
```

## Error Handling

### Common Error Responses

**Insufficient Balance (400):**
```json
{
  "detail": "Insufficient balance. Available: ₹250.50, Requested: ₹300.00"
}
```

**Invalid Transaction Type (400):**
```json
{
  "detail": "Invalid transaction type. Must be one of: purchase, bonus, referral_bonus"
}
```

**Bank Details Not Found (400):**
```json
{
  "detail": "Bank details not found. Please add your bank details before requesting withdrawal."
}
```

**Wallet Not Found (404):**
```json
{
  "detail": "Wallet not found"
}
```

## Integration Examples

### React Native Integration

```typescript
// Get wallet balance
const getWalletBalance = async (token: string) => {
  const response = await fetch('https://saathiiapp.com/wallet/balance', {
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    }
  });
  return response.json();
};

// Add coins to wallet
const addCoins = async (token: string, coins: number, txType: string = 'purchase', moneyAmount: number = 0) => {
  const response = await fetch('https://saathiiapp.com/wallet/add-coins', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      coins,
      tx_type: txType,
      money_amount: moneyAmount
    })
  });
  return response.json();
};

// Request withdrawal
const requestWithdrawal = async (token: string, amount: number) => {
  const response = await fetch('https://saathiiapp.com/wallet/withdraw', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ amount })
  });
  return response.json();
};
```

### cURL Examples

**Get Wallet Balance:**
```bash
curl -X GET 'https://saathiiapp.com/wallet/balance' \
  -H 'Authorization: Bearer <access_token>'
```

**Add Coins:**
```bash
curl -X POST 'https://saathiiapp.com/wallet/add-coins' \
  -H 'Authorization: Bearer <access_token>' \
  -H 'Content-Type: application/json' \
  -d '{
    "coins": 100,
    "tx_type": "purchase",
    "money_amount": 50.00
  }'
```

**Request Withdrawal:**
```bash
curl -X POST 'https://saathiiapp.com/wallet/withdraw' \
  -H 'Authorization: Bearer <access_token>' \
  -H 'Content-Type: application/json' \
  -d '{
    "amount": 100.00
  }'
```

## Best Practices

### Wallet Management

1. **Check Balance**: Always check wallet balance before operations
2. **Validate Input**: Validate coin amounts and transaction types
3. **Handle Errors**: Implement proper error handling for all operations
4. **Transaction Tracking**: Keep track of transaction IDs for reference

### Security

1. **Token Management**: Store tokens securely
2. **Input Validation**: Validate all input data
3. **Rate Limiting**: Implement client-side rate limiting
4. **Error Handling**: Don't expose sensitive information in errors

### Performance

1. **Caching**: Cache wallet balance locally
2. **Pagination**: Use pagination for transaction history
3. **Loading States**: Show loading states during operations
4. **Error Recovery**: Implement retry logic for failed requests

## Next Steps

- Learn about [Transactions API](./transactions) for detailed transaction history
- Explore [Call Management API](./call-management) for call operations
- Check out [User Management API](./user-management) for profile management
