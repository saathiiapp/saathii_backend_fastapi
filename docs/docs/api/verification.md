---
sidebar_position: 8
title: Listener Verification API
description: Audio verification system for listeners
---

# Listener Verification API

The Listener Verification API provides a comprehensive audio verification system for listeners, allowing them to upload audio samples for review and verification.

## Overview

- **Audio Upload**: Upload audio files for verification
- **Status Tracking**: Track verification status and history
- **Admin Review**: Admin endpoints for reviewing submissions
- **S3 Integration**: Secure file storage and management
- **Role-based Access**: Listener-only verification system

## Endpoints

### Upload Audio File

Upload an audio file for listener verification.

**Endpoint:** `POST /verification/upload-audio-file`

**Headers:**
```
Authorization: Bearer <access_token>
Content-Type: multipart/form-data
```

**Request Body:**
- `audio_file`: Audio file (multipart/form-data)

**File Requirements:**
- **Format**: MP3, WAV, M4A, or other audio formats
- **Size**: Maximum 10MB
- **Content-Type**: Must be audio/*

**Response:**
```json
{
  "sample_id": 123,
  "listener_id": 456,
  "audio_file_url": "https://s3.amazonaws.com/bucket/verification-audio/456/20240115_103000_abc123.mp3",
  "status": "pending",
  "remarks": null,
  "uploaded_at": "2024-01-15T10:30:00Z",
  "reviewed_at": null
}
```

**Error Responses:**
- `400 Bad Request` - Invalid file type or size
- `403 Forbidden` - Only listeners can upload verification audio
- `409 Conflict` - Already have a pending verification
- `500 Internal Server Error` - S3 upload failed

### Upload Audio URL

Upload verification audio using an S3 URL (for external uploads).

**Endpoint:** `POST /verification/upload-audio-url`

**Headers:**
```
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Request Body:**
```json
{
  "audio_file_url": "https://s3.amazonaws.com/bucket/verification-audio/456/20240115_103000_abc123.mp3"
}
```

**Fields:**
- `audio_file_url`: S3 URL for the audio file

**Response:**
```json
{
  "sample_id": 123,
  "listener_id": 456,
  "audio_file_url": "https://s3.amazonaws.com/bucket/verification-audio/456/20240115_103000_abc123.mp3",
  "status": "pending",
  "remarks": null,
  "uploaded_at": "2024-01-15T10:30:00Z",
  "reviewed_at": null
}
```

**Error Responses:**
- `400 Bad Request` - Invalid S3 URL format
- `403 Forbidden` - Only listeners can upload verification audio
- `409 Conflict` - Already have a pending verification

### Get Verification Status

Get the current verification status for the listener.

**Endpoint:** `GET /verification/status`

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response:**
```json
{
  "is_verified": false,
  "verification_status": "pending",
  "last_verification": {
    "sample_id": 123,
    "listener_id": 456,
    "audio_file_url": "https://s3.amazonaws.com/bucket/verification-audio/456/20240115_103000_abc123.mp3",
    "status": "pending",
    "remarks": null,
    "uploaded_at": "2024-01-15T10:30:00Z",
    "reviewed_at": null
  },
  "message": "Verification status: pending"
}
```

**Field Descriptions:**
- `is_verified`: Whether the listener is verified
- `verification_status`: Current status ("pending", "approved", "rejected")
- `last_verification`: Details of the latest verification submission
- `message`: Human-readable status message

### Get Verification History

Get the complete verification history for the listener.

**Endpoint:** `GET /verification/history`

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response:**
```json
[
  {
    "sample_id": 123,
    "listener_id": 456,
    "audio_file_url": "https://s3.amazonaws.com/bucket/verification-audio/456/20240115_103000_abc123.mp3",
    "status": "pending",
    "remarks": null,
    "uploaded_at": "2024-01-15T10:30:00Z",
    "reviewed_at": null
  },
  {
    "sample_id": 122,
    "listener_id": 456,
    "audio_file_url": "https://s3.amazonaws.com/bucket/verification-audio/456/20240114_150000_def456.mp3",
    "status": "rejected",
    "remarks": "Audio quality too low",
    "uploaded_at": "2024-01-14T15:00:00Z",
    "reviewed_at": "2024-01-14T16:30:00Z"
  }
]
```

## Admin Endpoints

### Get Pending Verifications

Get all pending verification requests (admin only).

**Endpoint:** `GET /admin/verification/pending`

**Headers:**
```
Authorization: Bearer <access_token>
```

**Query Parameters:**
- `page`: Page number (default: 1)
- `per_page`: Items per page (default: 20, max: 100)

**Response:**
```json
[
  {
    "sample_id": 123,
    "listener_id": 456,
    "audio_file_url": "https://s3.amazonaws.com/bucket/verification-audio/456/20240115_103000_abc123.mp3",
    "status": "pending",
    "remarks": null,
    "uploaded_at": "2024-01-15T10:30:00Z",
    "reviewed_at": null
  }
]
```

### Review Verification

Review and approve/reject verification request (admin only).

**Endpoint:** `POST /admin/verification/review`

**Headers:**
```
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Request Body:**
```json
{
  "sample_id": 123,
  "status": "approved",
  "remarks": "Audio quality is excellent"
}
```

**Fields:**
- `sample_id`: ID of the verification sample
- `status`: Review decision ("approved" or "rejected")
- `remarks`: Optional remarks for the listener

**Response:**
```json
{
  "success": true,
  "message": "Verification approved successfully with remarks: Audio quality is excellent",
  "verification": {
    "sample_id": 123,
    "listener_id": 456,
    "audio_file_url": "https://s3.amazonaws.com/bucket/verification-audio/456/20240115_103000_abc123.mp3",
    "status": "approved",
    "remarks": "Audio quality is excellent",
    "uploaded_at": "2024-01-15T10:30:00Z",
    "reviewed_at": "2024-01-15T11:00:00Z"
  }
}
```

## Verification Statuses

### Pending
- **Description**: Verification is awaiting review
- **Action**: Admin needs to review the audio sample
- **Duration**: Typically reviewed within 24-48 hours

### Approved
- **Description**: Verification has been approved
- **Action**: Listener is now verified
- **Benefits**: Access to verified listener features

### Rejected
- **Description**: Verification has been rejected
- **Action**: Listener can upload a new sample
- **Reason**: Usually includes remarks explaining rejection

## File Management

### S3 Integration

The verification system uses AWS S3 for secure file storage:

- **Bucket**: Configurable S3 bucket
- **Path**: `verification-audio/{user_id}/{timestamp}_{unique_id}.{extension}`
- **Access**: Private files with signed URLs
- **Retention**: Files are retained for audit purposes

### File Validation

**Supported Formats:**
- MP3 (audio/mpeg)
- WAV (audio/wav)
- M4A (audio/mp4)
- OGG (audio/ogg)

**Size Limits:**
- Maximum file size: 10MB
- Minimum file size: 1KB

**Content Validation:**
- Must be valid audio file
- Content-Type must start with "audio/"
- File must be readable and playable

## Error Handling

### Common Error Responses

**Invalid File Type (400):**
```json
{
  "detail": "File must be an audio file (mp3, wav, m4a, etc.)"
}
```

**File Too Large (400):**
```json
{
  "detail": "File size must be less than 10MB"
}
```

**Not a Listener (403):**
```json
{
  "detail": "Only users with listener role can upload verification audio"
}
```

**Pending Verification (409):**
```json
{
  "detail": "You already have a pending verification. Please wait for it to be reviewed."
}
```

**S3 Not Configured (500):**
```json
{
  "detail": "File upload service is not configured. Please contact support."
}
```

**Upload Failed (500):**
```json
{
  "detail": "Failed to upload file. Please try again."
}
```

## Integration Examples

### React Native Integration

```typescript
// services/VerificationService.ts
import ApiService from './ApiService';

export interface ListenerVerificationResponse {
  sample_id: number;
  listener_id: number;
  audio_file_url: string;
  status: 'pending' | 'approved' | 'rejected';
  remarks: string | null;
  uploaded_at: string;
  reviewed_at: string | null;
}

export interface VerificationStatusResponse {
  is_verified: boolean;
  verification_status: 'pending' | 'approved' | 'rejected' | null;
  last_verification: ListenerVerificationResponse | null;
  message: string;
}

export interface AdminReviewRequest {
  sample_id: number;
  status: 'approved' | 'rejected';
  remarks?: string;
}

class VerificationService {
  // Upload audio file
  async uploadAudioFile(audioFile: File): Promise<ListenerVerificationResponse> {
    const formData = new FormData();
    formData.append('audio_file', audioFile);

    return ApiService.post<ListenerVerificationResponse>(
      '/verification/upload-audio-file',
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      }
    );
  }

  // Upload audio URL
  async uploadAudioUrl(audioFileUrl: string): Promise<ListenerVerificationResponse> {
    return ApiService.post<ListenerVerificationResponse>('/verification/upload-audio-url', {
      audio_file_url: audioFileUrl
    });
  }

  // Get verification status
  async getVerificationStatus(): Promise<VerificationStatusResponse> {
    return ApiService.get<VerificationStatusResponse>('/verification/status');
  }

  // Get verification history
  async getVerificationHistory(): Promise<ListenerVerificationResponse[]> {
    return ApiService.get<ListenerVerificationResponse[]>('/verification/history');
  }

  // Admin: Get pending verifications
  async getPendingVerifications(page: number = 1, perPage: number = 20): Promise<ListenerVerificationResponse[]> {
    return ApiService.get<ListenerVerificationResponse[]>(
      `/admin/verification/pending?page=${page}&per_page=${perPage}`
    );
  }

  // Admin: Review verification
  async reviewVerification(request: AdminReviewRequest): Promise<any> {
    return ApiService.post('/admin/verification/review', request);
  }
}

export default new VerificationService();
```

### cURL Examples

**Upload Audio File:**
```bash
curl -X POST 'https://saathiiapp.com/verification/upload-audio-file' \
  -H 'Authorization: Bearer <access_token>' \
  -F 'audio_file=@/path/to/audio.mp3'
```

**Upload Audio URL:**
```bash
curl -X POST 'https://saathiiapp.com/verification/upload-audio-url' \
  -H 'Authorization: Bearer <access_token>' \
  -H 'Content-Type: application/json' \
  -d '{
    "audio_file_url": "https://s3.amazonaws.com/bucket/verification-audio/456/20240115_103000_abc123.mp3"
  }'
```

**Get Verification Status:**
```bash
curl -X GET 'https://saathiiapp.com/verification/status' \
  -H 'Authorization: Bearer <access_token>'
```

**Get Verification History:**
```bash
curl -X GET 'https://saathiiapp.com/verification/history' \
  -H 'Authorization: Bearer <access_token>'
```

**Admin: Review Verification:**
```bash
curl -X POST 'https://saathiiapp.com/admin/verification/review' \
  -H 'Authorization: Bearer <access_token>' \
  -H 'Content-Type: application/json' \
  -d '{
    "sample_id": 123,
    "status": "approved",
    "remarks": "Audio quality is excellent"
  }'
```

## Best Practices

### File Upload

1. **File Validation**: Validate file type and size before upload
2. **Progress Tracking**: Show upload progress to users
3. **Error Handling**: Handle upload errors gracefully
4. **Retry Logic**: Implement retry for failed uploads

### User Experience

1. **Clear Instructions**: Provide clear instructions for audio requirements
2. **Status Updates**: Keep users informed about verification status
3. **Feedback**: Provide helpful feedback for rejected verifications
4. **History**: Show verification history for transparency

### Security

1. **File Validation**: Strictly validate uploaded files
2. **Access Control**: Ensure only listeners can upload
3. **S3 Security**: Use secure S3 configurations
4. **Admin Access**: Protect admin endpoints appropriately

### Performance

1. **File Size Limits**: Enforce reasonable file size limits
2. **Async Processing**: Handle file uploads asynchronously
3. **Caching**: Cache verification status for better performance
4. **Cleanup**: Implement file cleanup for old verifications

## Next Steps

- Learn about [User Management API](./user-management) for profile management
- Explore [Call Management API](./call-management) for making calls
- Check out [S3 Setup Guide](./s3-setup) for file storage configuration
- Access the [WebSocket Integration](./websocket-realtime) for real-time updates