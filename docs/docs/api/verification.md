---
sidebar_position: 8
title: Listener Verification API
description: Audio verification system for listeners
---

# Listener Verification API

Single endpoint for quick audio verification using an S3 URL.

## Overview

- **Audio Upload**: Upload audio files for verification
- **Status Tracking**: Track verification status and history
- **Admin Review**: Admin endpoints for reviewing submissions
- **S3 Integration**: Secure file storage and management
- **Role-based Access**: Listener-only verification system

## Endpoint

### Verify Audio

Verify that the provided S3 audio URL points to a valid audio file and return a quick verification status.

**Endpoint:** `POST /listener/verification/verify-audio`

**Headers:**
```
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Request Body:**
```json
{
  "audio_file_url": "https://bucket.s3.region.amazonaws.com/path/to/audio.mp3"
}
```

**Response:**
```json
{
  "verified": true,
  "reason": "basic_checks_passed"
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