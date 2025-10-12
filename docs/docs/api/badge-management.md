---
sidebar_position: 6
title: Badge Management
description: Listener badge system with dynamic earning rates based on daily performance
---

# Badge Management API

The Badge Management system provides dynamic earning rates for listeners based on their daily call performance. Listeners are assigned badges daily at 12:01 AM based on their previous day's call duration.

## 🏆 Badge System Overview

### Badge Tiers

| Badge | Call Duration Required | Audio Rate (INR/min) | Video Rate (INR/min) |
|-------|----------------------|---------------------|---------------------|
| **Basic** | 0+ hours | ₹1.00 | ₹6.00 |
| **Bronze** | 3+ hours | ₹1.25 | ₹7.00 |
| **Silver** | 6+ hours | ₹1.50 | ₹8.50 |
| **Gold** | 9+ hours | ₹1.80 | ₹10.00 |

### How It Works

1. **Daily Assessment**: At 12:01 AM, the system calculates each listener's total call duration from the previous day
2. **Badge Assignment**: Based on duration thresholds, listeners receive their badge for the day
3. **Earning Calculation**: All calls made during the day use the assigned badge's rates
4. **Automatic Updates**: The system runs automatically via scheduled tasks

## 📊 API Endpoints

### Get Current Badge

Get the current badge and performance information for the authenticated listener.

```http
GET /badges/current
```

**Response:**
```json
{
  "current_badge": {
    "listener_id": 123,
    "date": "2024-01-15",
    "badge": "silver",
    "audio_rate_per_minute": 1.5,
    "video_rate_per_minute": 8.5,
    "assigned_at": "2024-01-15T00:01:00Z"
  },
  "yesterday_duration_hours": 6.5,
  "next_badge_threshold": 9.0
}
```

### Get Badge History

Retrieve badge history for a specific date range.

```http
GET /badges/history?start_date=2024-01-01&end_date=2024-01-15
```

**Query Parameters:**
- `start_date` (optional): Start date for history (default: 30 days ago)
- `end_date` (optional): End date for history (default: today)

**Response:**
```json
[
  {
    "listener_id": 123,
    "date": "2024-01-15",
    "badge": "silver",
    "audio_rate_per_minute": 1.5,
    "video_rate_per_minute": 8.5,
    "assigned_at": "2024-01-15T00:01:00Z"
  },
  {
    "listener_id": 123,
    "date": "2024-01-14",
    "badge": "bronze",
    "audio_rate_per_minute": 1.25,
    "video_rate_per_minute": 7.0,
    "assigned_at": "2024-01-14T00:01:00Z"
  }
]
```

### Get Badge Statistics

Get badge distribution statistics across all listeners.

```http
GET /badges/statistics?start_date=2024-01-01&end_date=2024-01-15
```

**Response:**
```json
{
  "statistics": [
    {
      "badge": "basic",
      "count": 45,
      "avg_audio_rate": 1.0,
      "avg_video_rate": 6.0
    },
    {
      "badge": "bronze",
      "count": 23,
      "avg_audio_rate": 1.25,
      "avg_video_rate": 7.0
    },
    {
      "badge": "silver",
      "count": 12,
      "avg_audio_rate": 1.5,
      "avg_video_rate": 8.5
    },
    {
      "badge": "gold",
      "count": 5,
      "avg_audio_rate": 1.8,
      "avg_video_rate": 10.0
    }
  ],
  "total_listeners": 85,
  "date_range": "2024-01-01 to 2024-01-15"
}
```

### Manual Badge Assignment

Manually trigger badge assignment for a specific date (admin only).

```http
POST /badges/assign?target_date=2024-01-15
```

**Response:**
```json
{
  "message": "Badge assignment completed successfully",
  "date": "2024-01-15",
  "total_listeners": 85,
  "basic_assigned": 45,
  "bronze_assigned": 23,
  "silver_assigned": 12,
  "gold_assigned": 5,
  "errors": 0
}
```

### Get Specific Listener Badge

Get badge information for a specific listener (admin only).

```http
GET /badges/123?target_date=2024-01-15
```

**Response:**
```json
{
  "listener_id": 123,
  "date": "2024-01-15",
  "badge": "silver",
  "audio_rate_per_minute": 1.5,
  "video_rate_per_minute": 8.5,
  "assigned_at": "2024-01-15T00:01:00Z"
}
```

## 🔧 Implementation Details

### Database Schema

```sql
CREATE TABLE listener_badges (
  listener_id INT REFERENCES users(user_id) ON DELETE CASCADE,
  date        DATE NOT NULL,
  badge       VARCHAR(20) CHECK (badge IN ('gold','silver','bronze','basic')),
  audio_rate_per_minute NUMERIC(5,2) NOT NULL,
  video_rate_per_minute NUMERIC(5,2) NOT NULL,
  assigned_at TIMESTAMPTZ DEFAULT now(),
  PRIMARY KEY (listener_id, date)
);
```

### Scheduled Tasks

The system includes automatic scheduled tasks:

1. **Badge Assignment**: Runs daily at 12:01 AM
2. **Presence Cleanup**: Runs every 5 minutes

### Integration with Call System

The badge system is automatically integrated with the call management system:

- Call earnings are calculated using the listener's current badge rates
- No manual intervention required
- Real-time rate updates based on daily performance

## 🚀 Getting Started

### 1. Database Migration

Run the migration script to update your database schema:

```bash
psql -d your_database -f migrate_badge_schema.sql
```

### 2. Environment Setup

The badge system works with your existing FastAPI setup. No additional environment variables are required.

### 3. Testing the System

1. **Create a listener account**
2. **Make some calls** to accumulate duration
3. **Check current badge**: `GET /badges/current`
4. **View badge history**: `GET /badges/history`

### 4. Monitoring

- Check application logs for badge assignment status
- Use statistics endpoint to monitor badge distribution
- Monitor call earnings to verify correct rate application

## 📈 Performance Considerations

- Badge assignments are processed in batches for efficiency
- Database indexes are created for optimal query performance
- Scheduled tasks run asynchronously to avoid blocking the main application

## 🔒 Security Notes

- Badge assignment endpoints require authentication
- Admin-only endpoints should implement proper role-based access control
- Badge data is read-only for regular users
- Only system administrators can trigger manual badge assignments

## 🐛 Troubleshooting

### Common Issues

1. **Badge not assigned**: Check if the listener has the 'listener' role
2. **Incorrect rates**: Verify the badge assignment was successful
3. **Missing history**: Ensure calls were completed (not dropped)

### Debug Endpoints

- Use `/badges/statistics` to verify badge distribution
- Check application logs for assignment errors
- Verify call completion status in the database

## 📝 Examples

### React Native Integration

```javascript
// Get current badge
const getCurrentBadge = async () => {
  const response = await fetch('/badges/current', {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });
  return response.json();
};

// Display badge information
const BadgeCard = ({ badge }) => {
  if (!badge) return <Text>No badge assigned</Text>;
  
  return (
    <View>
      <Text>Current Badge: {badge.badge.toUpperCase()}</Text>
      <Text>Audio Rate: ₹{badge.audio_rate_per_minute}/min</Text>
      <Text>Video Rate: ₹{badge.video_rate_per_minute}/min</Text>
    </View>
  );
};
```

### Admin Dashboard

```javascript
// Get badge statistics
const getBadgeStats = async () => {
  const response = await fetch('/badges/statistics');
  return response.json();
};

// Trigger manual assignment
const assignBadges = async (date) => {
  const response = await fetch(`/badges/assign?target_date=${date}`, {
    method: 'POST'
  });
  return response.json();
};
```
