---
sidebar_position: 9
title: Listener Verification API
description: Complete listener verification and preferences management system
---

# Listener Verification API

The listener verification system ensures quality control and authenticity of listeners on the platform. Listeners must be verified before they can access any listener-specific APIs or appear in customer feeds.

## Overview

- **Live Audio Capture**: Listeners provide audio samples during registration
- **Boolean Verification Status**: Simple true/false verification system
- **Manual Admin Review**: Admins manually verify listeners by updating database
- **API Protection**: All listener APIs require verification
- **Feed Filtering**: Only verified listeners appear in customer feeds

## Registration with Audio

When registering as a listener, include the live audio sample:

### Register Listener

**Endpoint:** `POST /auth/both/register`

**Headers:**
```
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Request Body:**
```json
{
  "registration_token": "eyJ...",
  "username": "listener123",
  "role": "listener",
  "live_audio_url": "https://bucket.s3.region.amazonaws.com/audio/sample.mp3",
  "sex": "female",
  "dob": "1990-01-01",
  "bio": "Professional listener with 5 years experience...",
  "interests": ["music", "counseling", "relationships"],
  "preferred_language": "en"
}
```

**Response:**
```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ..."
}
```

## Verification Status

### Get Verification Status

**Endpoint:** `GET /listener/verification/status`

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response:**
```json
{
  "verification_status": false,
  "verification_message": "Verification pending admin review",
  "verified_on": null,
  "latest_verification": null
}
```

**Status Values:**
- `false`: Not verified (default) - cannot access listener APIs
- `true`: Verified - can access all listener features

## Listener Preferences

### Get Call Preferences

**Endpoint:** `GET /listener/preferences`

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response:**
```json
{
  "listener_id": 123,
  "listener_allowed_call_type": ["audio", "video"],
  "listener_audio_call_enable": true,
  "listener_video_call_enable": false
}
```

### Update Call Preferences

**Endpoint:** `PUT /listener/preferences`

**Headers:**
```
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Request Body:**
```json
{
  "listener_audio_call_enable": false,
  "listener_video_call_enable": true
}
```

**Response:**
```json
{
  "listener_id": 123,
  "listener_allowed_call_type": ["video"],
  "listener_audio_call_enable": false,
  "listener_video_call_enable": true
}
```

## Admin Verification

To verify a listener, admins update the database directly:

```sql
UPDATE listener_profile 
SET verification_status = true, verified_on = now() 
WHERE listener_id = <listener_id>;
```

## Error Responses

### 403 Forbidden - Not Verified
```json
{
  "detail": "Access denied. Listener verification is pending. Please wait for admin approval."
}
```

### 403 Forbidden - Not a Listener
```json
{
  "detail": "Only users with listener role can access this endpoint"
}
```

### 404 Not Found - Profile Not Found
```json
{
  "detail": "Listener preferences not found. Please complete registration."
}
```

## Security Features

- ✅ **Role-based access**: Only listeners can access verification endpoints
- ✅ **Verification required**: All listener APIs check verification status
- ✅ **Feed filtering**: Only verified listeners appear in customer feeds
- ✅ **Audio validation**: Live audio samples stored for admin review

## Integration Notes

1. **Registration Flow**: Include `live_audio_url` when registering as a listener
2. **Verification Check**: Always check verification status before showing listener features
3. **Preferences Management**: Use dedicated preferences API for call type settings
4. **Admin Workflow**: Update database directly to verify listeners
5. **Feed Integration**: Feed automatically filters to show only verified listeners
