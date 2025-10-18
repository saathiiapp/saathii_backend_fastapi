# Help & Support API

The Help & Support API provides a comprehensive ticket system for customer service, issue tracking, and technical support requests. This system allows users to create support tickets with different issue types and provides administrators with powerful filtering and management capabilities.

## Table of Contents

- [Overview](#overview)
- [Authentication](#authentication)
- [User Endpoints](#user-endpoints)
- [Admin Endpoints](#admin-endpoints)
- [Data Models](#data-models)
- [Validation Rules](#validation-rules)
- [Error Handling](#error-handling)
- [Examples](#examples)

## Overview

The Help & Support system includes:

- **User Support Tickets**: Create and manage support tickets for active customers and verified listeners
- **Admin Management**: Comprehensive admin interface for viewing and managing all tickets
- **Issue Type Validation**: Different validation rules based on support type
- **Rich Filtering**: Multiple filter options for efficient ticket management
- **Status Tracking**: Simple two-status system (active, resolved)

## Authentication

### User Endpoints
- **Required**: JWT Bearer token
- **Access**: Active customers and verified listeners only
- **Validation**: Users can only access their own tickets

### Admin Endpoints
- **Required**: None (as requested)
- **Access**: Public access for administrative purposes
- **Security**: SQL injection protection and input validation

## User Endpoints

### Create Support Ticket

**`POST /both/support/tickets`**

Creates a new support ticket with validation based on issue type.

#### Request Body

```json
{
  "issue_type": "call_session_support",
  "issue": "Call dropped unexpectedly",
  "description": "The call ended after 2 minutes of conversation",
  "image_s3_urls": ["https://example.com/screenshot.jpg"],
  "require_call": true,
  "call_id": 123,
  "transaction_id": null
}
```

#### Validation Rules

| Issue Type | Required Fields | Optional Fields |
|------------|----------------|-----------------|
| `call_session_support` | `call_id` | `description`, `image_s3_urls`, `require_call` |
| `payment_support` | `transaction_id` | `description`, `image_s3_urls`, `require_call` |
| `other` | None | `description`, `image_s3_urls`, `require_call` |

#### Response

```json
{
  "support_id": 1,
  "user_id": 123,
  "issue_type": "call_session_support",
  "issue": "Call dropped unexpectedly",
  "description": "The call ended after 2 minutes of conversation",
  "image_s3_urls": ["https://example.com/screenshot.jpg"],
  "require_call": true,
  "call_id": 123,
  "transaction_id": null,
  "status": "active",
  "admin_notes": null,
  "resolved_at": null,
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z"
}
```

### Get My Support Tickets

**`GET /both/support/tickets`**

Retrieves paginated list of support tickets for the current user.

#### Query Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `page` | integer | No | Page number (default: 1) |
| `page_size` | integer | No | Items per page (default: 10, max: 50) |
| `status` | string | No | Filter by status (`active`, `resolved`) |
| `issue_type` | string | No | Filter by issue type |

#### Example Request

```bash
GET /both/support/tickets?page=1&page_size=20&status=active&issue_type=call_session_support
```

#### Response

```json
{
  "tickets": [
    {
      "support_id": 1,
      "user_id": 123,
      "issue_type": "call_session_support",
      "issue": "Call dropped unexpectedly",
      "description": "The call ended after 2 minutes",
      "image_s3_urls": ["https://example.com/screenshot.jpg"],
      "require_call": true,
      "call_id": 123,
      "transaction_id": null,
      "status": "active",
      "admin_notes": null,
      "resolved_at": null,
      "created_at": "2024-01-15T10:30:00Z",
      "updated_at": "2024-01-15T10:30:00Z"
    }
  ],
  "total_count": 25,
  "page": 1,
  "page_size": 20
}
```

### Get Support Ticket by ID

**`GET /both/support/tickets/{support_id}`**

Retrieves a specific support ticket by ID.

#### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `support_id` | integer | Yes | Support ticket ID |

#### Response

Returns the same format as individual ticket in the list response.

## Admin Endpoints

### Get All Support Tickets (Admin)

**`GET /admin/support/tickets`**

Retrieves all support tickets with comprehensive filtering options. No authentication required.

#### Query Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `page` | integer | No | Page number (default: 1) |
| `page_size` | integer | No | Items per page (default: 10, max: 100) |
| `status` | string | No | Filter by status (`active`, `resolved`) |
| `issue_type` | string | No | Filter by issue type |
| `user_id` | integer | No | Filter by specific user ID |
| `username` | string | No | Filter by username (partial match) |
| `phone` | string | No | Filter by phone number (partial match) |
| `created_from` | string | No | Filter tickets created from date (YYYY-MM-DD) |
| `created_to` | string | No | Filter tickets created to date (YYYY-MM-DD) |
| `require_call` | boolean | No | Filter by require_call flag |
| `sort_by` | string | No | Sort field (`created_at`, `updated_at`, `support_id`) |
| `sort_order` | string | No | Sort order (`asc`, `desc`) |

#### Example Requests

```bash
# Get all active tickets
GET /admin/support/tickets?status=active

# Filter by user
GET /admin/support/tickets?user_id=123
GET /admin/support/tickets?username=john

# Date range filter
GET /admin/support/tickets?created_from=2024-01-01&created_to=2024-01-31

# Complex filtering with sorting
GET /admin/support/tickets?status=active&issue_type=payment_support&sort_by=created_at&sort_order=desc
```

#### Response

```json
{
  "tickets": [
    {
      "support_id": 1,
      "user_id": 123,
      "username": "john_doe",
      "phone": "+1234567890",
      "issue_type": "call_session_support",
      "issue": "Call dropped unexpectedly",
      "description": "The call ended after 2 minutes",
      "image_s3_urls": ["https://example.com/screenshot.jpg"],
      "require_call": true,
      "call_id": 123,
      "transaction_id": null,
      "status": "active",
      "admin_notes": null,
      "resolved_at": null,
      "created_at": "2024-01-15T10:30:00Z",
      "updated_at": "2024-01-15T10:30:00Z"
    }
  ],
  "total_count": 150,
  "page": 1,
  "page_size": 10
}
```

## Data Models

### Issue Types

| Value | Description | Required Fields |
|-------|-------------|----------------|
| `call_session_support` | Issues related to call sessions | `call_id` |
| `payment_support` | Issues related to payments/transactions | `transaction_id` |
| `other` | General support issues | None |

### Status Types

| Value | Description |
|-------|-------------|
| `active` | Ticket is open and being processed |
| `resolved` | Ticket has been resolved |

### CreateSupportTicketRequest

```json
{
  "issue_type": "call_session_support",
  "issue": "Brief description of the issue",
  "description": "Detailed description (optional)",
  "image_s3_urls": ["https://example.com/image1.jpg"],
  "require_call": false,
  "call_id": 123,
  "transaction_id": null
}
```

### SupportTicketResponse

```json
{
  "support_id": 1,
  "user_id": 123,
  "issue_type": "call_session_support",
  "issue": "Call dropped unexpectedly",
  "description": "The call ended after 2 minutes",
  "image_s3_urls": ["https://example.com/screenshot.jpg"],
  "require_call": true,
  "call_id": 123,
  "transaction_id": null,
  "status": "active",
  "admin_notes": null,
  "resolved_at": null,
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z"
}
```

### AdminSupportTicketResponse

Extends `SupportTicketResponse` with additional user information:

```json
{
  "support_id": 1,
  "user_id": 123,
  "username": "john_doe",
  "phone": "+1234567890",
  "issue_type": "call_session_support",
  "issue": "Call dropped unexpectedly",
  "description": "The call ended after 2 minutes",
  "image_s3_urls": ["https://example.com/screenshot.jpg"],
  "require_call": true,
  "call_id": 123,
  "transaction_id": null,
  "status": "active",
  "admin_notes": null,
  "resolved_at": null,
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z"
}
```

## Validation Rules

### Field Requirements by Issue Type

#### Call Session Support
- **Required**: `call_id` must be provided and belong to the user
- **Optional**: `description`, `image_s3_urls`, `require_call`

#### Payment Support
- **Required**: `transaction_id` must be provided and belong to the user's wallet
- **Optional**: `description`, `image_s3_urls`, `require_call`

#### Other Support
- **Required**: None
- **Optional**: `description`, `image_s3_urls`, `require_call`

### Field Validation

| Field | Type | Constraints |
|-------|------|-------------|
| `issue` | string | 1-500 characters |
| `description` | string | Max 2000 characters |
| `image_s3_urls` | array | Array of valid S3 URLs |
| `call_id` | integer | Must exist and belong to user |
| `transaction_id` | integer | Must exist and belong to user's wallet |

## Error Handling

### Common Error Responses

#### 400 Bad Request
```json
{
  "detail": "call_id is required for call_session_support issues"
}
```

#### 401 Unauthorized
```json
{
  "detail": "Invalid or expired token"
}
```

#### 403 Forbidden
```json
{
  "detail": "User account is inactive"
}
```

#### 404 Not Found
```json
{
  "detail": "Support ticket not found"
}
```

#### 500 Internal Server Error
```json
{
  "detail": "Failed to create support ticket"
}
```

## Examples

### Creating Different Types of Support Tickets

#### Call Session Support
```bash
curl -X POST "/both/support/tickets" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "issue_type": "call_session_support",
    "issue": "Call quality was poor",
    "description": "Audio was choppy throughout the call",
    "call_id": 123,
    "require_call": true
  }'
```

#### Payment Support
```bash
curl -X POST "/both/support/tickets" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "issue_type": "payment_support",
    "issue": "Payment not processed",
    "description": "Money deducted but coins not added to wallet",
    "transaction_id": 456,
    "image_s3_urls": ["https://example.com/payment-screenshot.jpg"]
  }'
```

#### General Support
```bash
curl -X POST "/both/support/tickets" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "issue_type": "other",
    "issue": "How to change profile picture?",
    "description": "I cannot find the option to update my profile picture"
  }'
```

### Admin Filtering Examples

#### Get Active Call Session Issues
```bash
curl "/admin/support/tickets?status=active&issue_type=call_session_support"
```

#### Get Tickets from Specific User
```bash
curl "/admin/support/tickets?username=john&phone=+1234567890"
```

#### Get Recent Tickets with Sorting
```bash
curl "/admin/support/tickets?created_from=2024-01-01&sort_by=created_at&sort_order=desc"
```

## Database Schema

The help support system uses the following database table:

```sql
CREATE TABLE help_support (
  support_id      SERIAL PRIMARY KEY,
  user_id         INT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
  issue_type      VARCHAR(30) NOT NULL CHECK (issue_type IN ('call_session_support', 'payment_support', 'other')),
  issue           TEXT NOT NULL,
  description     TEXT,
  image_s3_urls   TEXT[],
  require_call    BOOLEAN DEFAULT FALSE,
  call_id         INT REFERENCES user_calls(call_id) ON DELETE SET NULL,
  transaction_id  INT REFERENCES user_transactions(transaction_id) ON DELETE SET NULL,
  status          VARCHAR(20) CHECK (status IN ('active', 'resolved')) DEFAULT 'active',
  admin_notes     TEXT,
  resolved_at     TIMESTAMPTZ,
  created_at      TIMESTAMPTZ DEFAULT now(),
  updated_at      TIMESTAMPTZ DEFAULT now()
);
```

## Security Considerations

- **SQL Injection Protection**: All queries use parameterized statements
- **Input Validation**: Comprehensive validation for all input fields
- **User Isolation**: Users can only access their own tickets
- **Admin Access**: Admin endpoint has no authentication (as requested)
- **Sort Field Validation**: Only predefined sort fields are allowed
- **Referential Integrity**: Foreign key constraints ensure data consistency
