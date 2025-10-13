---
sidebar_position: 2
title: User Management API
description: User profile management and account operations
---

# User Management API

The User Management API provides comprehensive user profile management, account operations, and user data retrieval.

## Overview

- **Profile Management**: Get, update, and delete user profiles
- **Account Operations**: Complete user account lifecycle management
- **Data Validation**: Comprehensive input validation and sanitization
- **Role-based Access**: Support for different user roles (listener, customer)

## Endpoints

### Get Current User

Retrieve the current user's profile information.

**Endpoint:** `GET /both/users/me`

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response:**
```json
{
  "user_id": 123,
  "phone": "+919876543210",
  "username": "alice",
  "sex": "female",
  "dob": "2000-01-01",
  "bio": "Professional listener with 5 years experience...",
  "interests": ["music", "tech", "art"],
  "profile_image_url": "https://example.com/profile.jpg",
  "preferred_language": "en",
  "rating": 4.8,
  "country": "US",
  "roles": ["listener"]
}
```

**Fields:**
- `user_id`: Unique user identifier
- `phone`: User's phone number
- `username`: Unique username
- `sex`: Gender ("male", "female")
- `dob`: Date of birth (YYYY-MM-DD)
- `bio`: User biography/description
- `interests`: Array of interest tags
- `profile_image_url`: Profile image URL
- `preferred_language`: Language preference
- `rating`: User rating (0.0-5.0)
- `country`: Country code
- `roles`: Array of user roles

### Update Current User

Update the current user's profile information.

**Endpoint:** `PUT /both/users/me`

**Headers:**
```
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Request Body (any subset of fields):**
```json
{
  "username": "new_username",
  "bio": "Updated bio...",
  "rating": 4.9,
  "interests": ["music", "tech", "art", "sports"],
  "profile_image_url": "https://example.com/new-profile.jpg",
  "preferred_language": "en",
  "country": "CA"
}
```

**Updatable Fields:**
- `username` - Must be unique
- `bio` - User biography
- `rating` - User rating (0.0-5.0)
- `interests` - Array of interest tags
- `profile_image_url` - Profile image URL
- `preferred_language` - Language preference
- `country` - Country code

**Read-only Fields:**
- `user_id` - Cannot be changed
- `phone` - Cannot be changed
- `sex` - Cannot be changed
- `dob` - Cannot be changed
- `roles` - Managed by admin
- `created_at` - System managed
- `updated_at` - System managed

**Response:**
```json
{
  "user_id": 123,
  "phone": "+919876543210",
  "username": "new_username",
  "sex": "female",
  "dob": "2000-01-01",
  "bio": "Updated bio...",
  "interests": ["music", "tech", "art", "sports"],
  "profile_image_url": "https://example.com/new-profile.jpg",
  "preferred_language": "en",
  "rating": 4.9,
  "country": "CA",
  "roles": ["listener"]
}
```

**Error Responses:**
- `400 Bad Request` - Invalid input data
- `409 Conflict` - Username already exists
- `422 Unprocessable Entity` - Validation errors

### Delete Current User

Permanently delete the current user's account.

**Endpoint:** `DELETE /both/users/me`

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response:**
```json
{
  "message": "User deleted successfully"
}
```

**Behavior:**
- Permanently deletes user account
- Removes all user data from database
- Invalidates all user tokens
- Cannot be undone

**Warning:** This action is irreversible!

## User Roles

### Listener Role

Users with the "listener" role can:
- Provide listening services
- Upload verification audio samples
- Receive calls from other users
- Earn money from calls
- Access listener-specific features

### Customer Role

Users with the "customer" role can:
- Make calls to listeners
- Use the feed system
- Manage their profile
- Access basic features

### Admin Role

Users with the "admin" role can:
- Review listener verifications
- Manage user accounts
- Access admin endpoints
- View system statistics

## Data Validation

### Username Validation

- **Length**: 3-50 characters
- **Characters**: Alphanumeric and underscores only
- **Uniqueness**: Must be unique across all users
- **Case**: Case-insensitive uniqueness check

### Bio Validation

- **Length**: Maximum 500 characters
- **Content**: Plain text only (no HTML)
- **Optional**: Can be empty

### Interests Validation

- **Array**: Must be an array of strings
- **Length**: Maximum 10 interests per user
- **Individual Length**: Each interest max 50 characters
- **Characters**: Alphanumeric, spaces, and hyphens only

### Profile Image URL Validation

- **Format**: Must be a valid URL
- **Protocol**: HTTP or HTTPS only
- **Optional**: Can be null or empty

### Rating Validation

- **Range**: 0.0 to 5.0
- **Precision**: One decimal place
- **Optional**: Can be null

## Error Handling

### Common Error Responses

**Invalid Username (400):**
```json
{
  "detail": "Username must be 3-50 characters and contain only alphanumeric characters and underscores"
}
```

**Username Already Exists (409):**
```json
{
  "detail": "Username already exists"
}
```

**Invalid Bio (400):**
```json
{
  "detail": "Bio must be 500 characters or less"
}
```

**Invalid Interests (400):**
```json
{
  "detail": "Interests must be an array of strings, maximum 10 items"
}
```

**Invalid Rating (400):**
```json
{
  "detail": "Rating must be between 0.0 and 5.0"
}
```

**Unauthorized (401):**
```json
{
  "detail": "Could not validate credentials"
}
```

## Integration Examples

### React Native Integration

```typescript
// Get current user
const getCurrentUser = async (token: string) => {
  const response = await fetch('https://saathiiapp.com/users/me', {
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    }
  });
  return response.json();
};

// Update user profile
const updateProfile = async (token: string, updates: any) => {
  const response = await fetch('https://saathiiapp.com/users/me', {
    method: 'PUT',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(updates)
  });
  return response.json();
};

// Delete user account
const deleteAccount = async (token: string) => {
  const response = await fetch('https://saathiiapp.com/users/me', {
    method: 'DELETE',
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });
  return response.json();
};

```

### cURL Examples

**Get Current User:**
```bash
curl -X GET 'https://saathiiapp.com/users/me' \
  -H 'Authorization: Bearer <access_token>'
```

**Update Profile:**
```bash
curl -X PUT 'https://saathiiapp.com/users/me' \
  -H 'Authorization: Bearer <access_token>' \
  -H 'Content-Type: application/json' \
  -d '{
    "username": "new_username",
    "bio": "Updated bio...",
    "interests": ["music", "tech", "art"]
  }'
```

**Delete Account:**
```bash
curl -X DELETE 'https://saathiiapp.com/users/me' \
  -H 'Authorization: Bearer <access_token>'
```


## Best Practices

### Profile Management

1. **Validate Input**: Always validate user input on the client side
2. **Handle Errors**: Implement proper error handling for all operations
3. **Confirm Deletion**: Always confirm before deleting user accounts
4. **Update UI**: Refresh UI after successful profile updates

### Security

1. **Token Management**: Store tokens securely (use SecureStore in React Native)
2. **Input Sanitization**: Sanitize all user inputs
3. **Rate Limiting**: Implement client-side rate limiting for updates
4. **Validation**: Validate all data before sending to API

### Performance

1. **Caching**: Cache user profile data locally
2. **Optimistic Updates**: Update UI optimistically for better UX
3. **Error Recovery**: Implement retry logic for failed requests
4. **Loading States**: Show loading states during operations

## Next Steps

- Learn about [Presence & Status API](./presence-status) for real-time user status
- Explore [Feed System API](./feed-system) for discovering users
- Check out [Call Management API](./call-management) for call operations
