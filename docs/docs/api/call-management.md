---
sidebar_position: 5
title: Call Management API
description: Call lifecycle management with coin-based billing system
---

# Call Management API

The Call Management API provides comprehensive call lifecycle management with a coin-based billing system, automatic status updates, and history.

## Overview

- **Call Lifecycle**: Start, manage, and end calls
- **Coin-based Billing**: Real-time billing with coin system
- **Status Management**: Automatic presence status updates
- **Call History**: Complete call history and analytics
- **Wallet Integration**: Coin balance and transaction management

## Call Model

### Call Types

- **Audio Calls**: Voice-only calls
- **Video Calls**: Video and voice calls

### Call Statuses

- **Ongoing**: Call is currently active
- **Completed**: Call ended successfully
- **Dropped**: Call ended due to technical issues
- **Cancelled**: Call was cancelled before starting

### Billing System

- **Coins**: Virtual currency for call payments
- **Per-minute Billing**: Charges applied every minute
- **Minimum Charge**: Initial charge when call starts
- **Earnings**: Listeners earn from calls based on badge

## Endpoints

### Start Call

Start a new call with a listener.

**Endpoint:** `POST /customer/calls/start`

**Headers:**
```
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Request Body:**
```json
{
  "listener_id": 123,
  "call_type": "audio"
}
```

**Fields:**
- `listener_id`: ID of the listener to call
- `call_type`: "audio" or "video"

**Response:**
```json
{
  "call_id": 456,
  "message": "Call started successfully",
  "call_duration": 30,
  "remaining_coins": 700,
  "call_type": "audio",
  "listener_id": 123,
  "status": "ongoing"
}
```

**Behavior:**
- Validates user and listener availability
- Calculates maximum possible duration based on available coins
- Reserves minimum charge (10 coins for audio, 60 for video)
- Updates both users' presence status to busy
- Creates call record in database

### End Call

End an ongoing call.

**Endpoint:** `POST /both/calls/end`

**Headers:**
```
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Request Body:**
```json
{
  "call_id": 456,
  "reason": "completed"
}
```

**Fields:**
- `call_id`: ID of the call to end
- `reason`: "completed", "dropped", "cancelled"

**Response:**
```json
{
  "call_id": 456,
  "message": "Call ended successfully",
  "duration_seconds": 1800,
  "duration_minutes": 30,
  "coins_spent": 300,
  "listener_money_earned": 240,
  "status": "completed"
}
```

**Behavior:**
- Calculates final duration and total cost
- Updates listener earnings based on badge
- Updates both users' presence status to available
- Removes any transient call tracking

### Get Call History

Get paginated call history with filtering options.

**Endpoint:** `GET /both/calls/history`

**Headers:**
```
Authorization: Bearer <access_token>
```

**Query Parameters:**

| Parameter | Type | Description | Default |
|-----------|------|-------------|---------|
| `page` | integer | Page number (1-based) | 1 |
| `per_page` | integer | Items per page (max 100) | 20 |
| `call_type` | string | Filter by call type ("audio", "video") | null |
| `status` | string | Filter by status ("ongoing", "completed", "dropped") | null |

**Example Request:**
```
GET /calls/history?page=1&per_page=10&call_type=audio&status=completed
```

**Response:**
```json
{
  "calls": [
    {
      "call_id": 456,
      "user_id": 123,
      "listener_id": 789,
      "call_type": "audio",
      "start_time": "2024-01-15T10:30:00Z",
      "end_time": "2024-01-15T11:00:00Z",
      "duration_seconds": 1800,
      "duration_minutes": 30,
      "coins_spent": 300,
      "listener_money_earned": 450,
      "status": "completed",
      "caller_username": "john_doe",
      "listener_username": "jane_smith"
    }
  ],
  "total_calls": 25,
  "total_coins_spent": 1500,
  "total_earnings": 2250,
  "page": 1,
  "per_page": 20,
  "has_next": true,
  "has_previous": false
}
```

## Billing System

### Call Rates

**Audio Calls:**
- Rate: 10 coins per minute
- Minimum charge: 10 coins

**Video Calls:**
- Rate: 60 coins per minute  
- Minimum charge: 60 coins

### Billing Process

1. **Call Start**: Reserve minimum charge
2. **Per-minute Billing**: Deduct coins every minute
3. **Call End**: Calculate final cost and update earnings
4. **Automatic Termination**: End call if insufficient coins

### Coin Management

- **Wallet Integration**: Uses existing `user_wallets` table
- **Transaction Tracking**: All movements recorded in `user_transactions`

## Error Handling

### Common Error Responses

**Insufficient Coins (400):**
```json
{
  "detail": "Insufficient coins. Required: 300, Available: 200"
}
```

**User Not Available (400):**
```json
{
  "detail": "User is not available for calls"
}
```

**Call Not Found (404):**
```json
{
  "detail": "Call not found"
}
```

**Invalid Call Type (400):**
```json
{
  "detail": "Invalid call type. Must be 'audio' or 'video'"
}
```

**Call Already Ongoing (400):**
```json
{
  "detail": "User already has an ongoing call"
}
```

## Integration Examples

### React Native Integration

```typescript
// Start call
const startCall = async (token: string, listenerId: number, callType: string) => {
  const response = await fetch('https://saathiiapp.com/calls/start', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      listener_id: listenerId,
      call_type: callType,
      estimated_duration_minutes: 30
    })
  });
  return response.json();
};

// End call
const endCall = async (token: string, callId: number, reason: string) => {
  const response = await fetch('https://saathiiapp.com/calls/end', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      call_id: callId,
      reason: reason
    })
  });
  return response.json();
};

// Get call history
const getCallHistory = async (token: string, filters: any) => {
  const params = new URLSearchParams();
  Object.entries(filters).forEach(([key, value]) => {
    if (value !== null && value !== undefined) {
      params.append(key, value.toString());
    }
  });

  const response = await fetch(`https://saathiiapp.com/calls/history?${params}`, {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });
  return response.json();
};

// Recharge coins
const rechargeCoins = async (token: string, amountRupees: number) => {
  const response = await fetch('https://saathiiapp.com/calls/recharge', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      amount_rupees: amountRupees,
      payment_method: 'upi'
    })
  });
  return response.json();
};
```

### cURL Examples

**Start Call:**
```bash
curl -X POST 'https://saathiiapp.com/calls/start' \
  -H 'Authorization: Bearer <access_token>' \
  -H 'Content-Type: application/json' \
  -d '{
    "listener_id": 123,
    "call_type": "audio",
    "estimated_duration_minutes": 30
  }'
```

**End Call:**
```bash
curl -X POST 'https://saathiiapp.com/calls/end' \
  -H 'Authorization: Bearer <access_token>' \
  -H 'Content-Type: application/json' \
  -d '{
    "call_id": 456,
    "reason": "completed"
  }'
```

**Get Call History:**
```bash
curl -X GET 'https://saathiiapp.com/calls/history?page=1&per_page=10&call_type=audio' \
  -H 'Authorization: Bearer <access_token>'
```

**Recharge Coins:**
```bash
curl -X POST 'https://saathiiapp.com/calls/recharge' \
  -H 'Authorization: Bearer <access_token>' \
  -H 'Content-Type: application/json' \
  -d '{
    "amount_rupees": 150,
    "payment_method": "upi"
  }'
```

## Best Practices

### Call Management

1. **Availability Check**: Always check user availability before starting calls
2. **Coin Validation**: Validate sufficient coins before call start
3. **Status Updates**: Update UI immediately when call status changes
4. **Error Handling**: Handle all possible error scenarios

### Billing

1. **Per-minute Billing**: Implement reliable per-minute billing
2. **Balance Monitoring**: Monitor coin balance during calls
3. **Transaction Logging**: Log all coin transactions
4. **Recharge Options**: Provide multiple recharge options

### Real-time Updates

1. **WebSocket Integration**: Use WebSocket for live updates
2. **Status Broadcasting**: Broadcast status changes to all clients
3. **Connection Management**: Handle WebSocket disconnections
4. **Error Recovery**: Implement retry logic for failed operations

## Per-Minute Coin Deduction

### Background Task: Automatic Coin Deduction

Coins are automatically deducted every minute for all ongoing calls using a background task. This ensures fair billing without requiring external system integration.

**How it works:**
- Background service runs every minute via cron job
- Automatically processes all ongoing calls
- Deducts `rate_per_minute` for each active call
- Ends calls when users have insufficient coins
- Handles listener earnings and call settlement

**Configuration:**
- **Schedule**: Every minute (`* * * * *`)
- **Script**: `background_tasks/scripts/coin_deduction.py`
- **Logs**: `/var/log/saathii/coin_deduction.log`

**Benefits:**
- ✅ **Reliable**: No external dependencies
- ✅ **Scalable**: Handles thousands of calls efficiently
- ✅ **Automatic**: No manual intervention required
- ✅ **Fair Billing**: Precise per-minute charging
- ✅ **Error Handling**: Robust error recovery

**Setup:**
```bash
# Run the setup script to configure cron jobs
./background_tasks/scripts/setup_cron.sh
```

**Monitoring:**
```bash
# View real-time logs
tail -f /var/log/saathii/coin_deduction.log

# Check cron job status
crontab -l | grep coin_deduction
```

**Integration Notes:**
- This endpoint should be called every minute during active calls
- It automatically handles call termination when users run out of coins
- It updates both database and Redis cache
- It broadcasts presence changes via WebSocket
- It calculates fair listener earnings based on actual payment

**Error Handling:**
- Returns detailed error information for each call
- Continues processing other calls even if one fails
- Automatically ends calls when users have insufficient coins
- Maintains data consistency through database transactions

## Next Steps

- Learn about [WebSocket Real-time API](./websocket-realtime) for live updates
- Explore [Listener Verification API](./listener-verification) for verification process
- Check out [S3 File Upload API](./s3-file-upload) for file management
