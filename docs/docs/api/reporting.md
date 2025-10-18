---
sidebar_position: 8
title: Reporting API
description: User reporting functionality and admin report management
---

# Reporting API

The Reporting API provides user reporting functionality and admin tools for managing reports.

## Overview

- **Report Users**: Report users with optional reasons
- **Reported List**: View paginated list of users you've reported
- **Admin Reports**: Admin endpoint to view all reports with date filters
- **No Unreport**: Reports are permanent (no unreport functionality)
- **Simple Interface**: Clean API without complex enums

## User Endpoints

### Report User

Report a user with optional reason.

**Endpoint:** `POST /both/report`

**Headers:**
```
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Request Body:**
```json
{
  "reported_id": 123,
  "reason": "Inappropriate behavior"
}
```

**Fields:**
- `reported_id`: ID of the user to report (required)
- `reason`: Optional reason for reporting

**Response:**
```json
{
  "success": true,
  "message": "Successfully reported jane_smith",
  "reported_id": 123,
  "is_reported": true
}
```

**Error Responses:**
- `400 Bad Request` - Cannot report yourself
- `404 Not Found` - User not found
- `409 Conflict` - Already reported (returns success with message)

### Get Reported Users

Get a paginated list of users you have reported.

**Endpoint:** `GET /both/reported`

**Headers:**
```
Authorization: Bearer <access_token>
```

**Query Parameters:**

| Parameter | Type | Description | Default |
|-----------|------|-------------|---------|
| `page` | integer | Page number (1-based) | 1 |
| `per_page` | integer | Items per page (max 100) | 20 |

**Example Request:**
```
GET /both/reported?page=1&per_page=10
```

**Response:**
```json
{
  "reported_users": [
    {
      "user_id": 123,
      "username": "jane_smith",
      "sex": "female",
      "bio": "Professional listener...",
      "profile_image_url": "https://example.com/profile.jpg",
      "reason": "Inappropriate behavior",
      "reported_at": "2024-01-15T10:30:00Z"
    }
  ],
  "total_count": 3,
  "page": 1,
  "per_page": 10,
  "has_next": false,
  "has_previous": false
}
```

**Field Descriptions:**
- `user_id`: Unique user identifier
- `username`: User's display name
- `sex`: Gender ("male", "female")
- `bio`: User biography/description
- `profile_image_url`: Profile image URL
- `reason`: Reason for reporting (if provided)
- `reported_at`: When the user was reported

## Admin Endpoints

### Get All Reports (Admin)

Get all reports with date filtering (no authentication required).

**Endpoint:** `GET /admin/reports`

**Headers:**
```
Content-Type: application/json
```

**Query Parameters:**

| Parameter | Type | Description | Default |
|-----------|------|-------------|---------|
| `page` | integer | Page number (1-based) | 1 |
| `per_page` | integer | Items per page (max 100) | 20 |
| `date_from` | string | Filter reports from this date (YYYY-MM-DD) | null |
| `date_to` | string | Filter reports until this date (YYYY-MM-DD) | null |

**Example Requests:**
```
# Get all reports
GET /admin/reports

# Filter by date range
GET /admin/reports?date_from=2024-01-01&date_to=2024-01-31

# Filter from specific date
GET /admin/reports?date_from=2024-01-15

# With pagination
GET /admin/reports?date_from=2024-01-01&date_to=2024-01-31&page=2&per_page=50
```

**Response:**
```json
{
  "reported_users": [
    {
      "report_id": 456,
      "reporter_id": 789,
      "reporter_username": "user_who_reported",
      "reported_id": 123,
      "reported_username": "jane_smith",
      "reported_sex": "female",
      "reported_bio": "Professional listener...",
      "reported_profile_image_url": "https://example.com/profile.jpg",
      "reason": "Inappropriate behavior",
      "reported_at": "2024-01-15T10:30:00Z"
    }
  ],
  "total_count": 150,
  "page": 1,
  "per_page": 20,
  "has_next": true,
  "has_previous": false
}
```

**Admin Response Field Descriptions:**
- `report_id`: Unique report identifier
- `reporter_id`: ID of user who made the report
- `reporter_username`: Username of user who made the report
- `reported_id`: ID of user who was reported
- `reported_username`: Username of user who was reported
- `reported_sex`: Gender of reported user
- `reported_bio`: Bio of reported user
- `reported_profile_image_url`: Profile image of reported user
- `reason`: Reason for reporting (if provided)
- `reported_at`: When the report was made

## Best Practices

### User Experience

1. **Clear Reporting**: Make reporting process clear and simple
2. **Reason Collection**: Encourage users to provide reasons
3. **Confirmation**: Confirm report submission
4. **No Unreport**: Reports are permanent for moderation purposes

### Admin Management

1. **Date Filtering**: Use date filters for time-based analysis
2. **Pagination**: Use pagination for large datasets
3. **Regular Review**: Regularly review reports for patterns
4. **Action Tracking**: Track actions taken on reports

### Privacy and Safety

1. **Immediate Effect**: Reports are recorded immediately
2. **Data Protection**: Protect reporter and reported user data
3. **Moderation**: Use reports for content moderation
4. **Investigation**: Investigate reports thoroughly

### Performance

1. **Pagination**: Use pagination for all report lists
2. **Date Indexing**: Ensure database has proper date indexing
3. **Efficient Queries**: Optimize queries for date filtering
4. **Caching**: Consider caching for frequently accessed data

## Implementation Notes

- All reporting operations use `action_type = 'report'` in the database
- Reports are permanent - no unreport functionality
- Admin endpoint has no authentication requirements
- Date filters use PostgreSQL date comparison
- Separate from blocking functionality for better organization
