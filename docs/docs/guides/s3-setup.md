---
sidebar_position: 2
title: S3 Setup Guide
description: Complete guide for setting up AWS S3 for audio file uploads and listener verification
---

# S3 Setup Guide

This guide explains how to set up AWS S3 for audio file uploads and listener verification in the Saathii Backend API.

## Environment Variables

Add these environment variables to your `.env` file:

```bash
# AWS S3 Configuration for File Uploads
AWS_ACCESS_KEY_ID=your-aws-access-key-id
AWS_SECRET_ACCESS_KEY=your-aws-secret-access-key
AWS_REGION=us-east-1
S3_BUCKET_NAME=your-s3-bucket-name
```

## AWS S3 Setup

### 1. Create S3 Bucket

1. Go to AWS S3 Console
2. Create a new bucket with a unique name
3. Choose a region (e.g., us-east-1)
4. Configure bucket settings:
   - **Block Public Access**: Keep default settings (all blocked)
   - **Bucket Versioning**: Enable if needed
   - **Server-side encryption**: Enable for security

### 2. Configure Bucket Policy

Create a bucket policy to allow your application to upload files:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "AllowAppUploads",
            "Effect": "Allow",
            "Principal": {
                "AWS": "arn:aws:iam::YOUR_ACCOUNT_ID:user/YOUR_IAM_USER"
            },
            "Action": [
                "s3:PutObject",
                "s3:PutObjectAcl",
                "s3:GetObject",
                "s3:DeleteObject"
            ],
            "Resource": "arn:aws:s3:::YOUR_BUCKET_NAME/*"
        }
    ]
}
```

### 3. Create IAM User

1. Go to AWS IAM Console
2. Create a new user (e.g., `saathii-app-user`)
3. Attach a custom policy:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "s3:PutObject",
                "s3:PutObjectAcl",
                "s3:GetObject",
                "s3:DeleteObject"
            ],
            "Resource": "arn:aws:s3:::YOUR_BUCKET_NAME/*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "s3:ListBucket"
            ],
            "Resource": "arn:aws:s3:::YOUR_BUCKET_NAME"
        }
    ]
}
```

4. Generate access keys for this user
5. Use these keys in your environment variables

## API Endpoints

### Upload Audio File (Direct Upload)

**POST** `/verification/upload-audio-file`

Upload an audio file directly to S3.

**Request:**
- Content-Type: `multipart/form-data`
- Body: Audio file (mp3, wav, m4a, etc.)
- Max file size: 10MB

**Response:**
```json
{
    "sample_id": 1,
    "listener_id": 123,
    "audio_file_url": "https://bucket-name.s3.region.amazonaws.com/verification-audio/123/20240115_103000_abc12345.mp3",
    "status": "pending",
    "remarks": null,
    "uploaded_at": "2024-01-15T10:30:00Z",
    "reviewed_at": null
}
```

### Upload Audio URL (External Upload)

**POST** `/verification/upload-audio-url`

Submit an S3 URL for verification (for external uploads).

**Request:**
```json
{
    "audio_file_url": "https://bucket-name.s3.region.amazonaws.com/path/to/audio.mp3"
}
```

## File Organization

Audio files are organized in S3 as:
```
bucket-name/
└── verification-audio/
    └── {user_id}/
        └── {timestamp}_{unique_id}.{extension}
```

Example: `verification-audio/123/20240115_103000_abc12345.mp3`

## Security Features

- **File Type Validation**: Only audio files are accepted
- **File Size Limit**: Maximum 10MB per file
- **User Role Check**: Only users with 'listener' role can upload
- **Pending Check**: Prevents multiple pending verifications
- **S3 Metadata**: Files include user_id and upload metadata

## Error Handling

- **403 Forbidden**: User doesn't have listener role
- **400 Bad Request**: Invalid file type, size, or existing pending verification
- **500 Internal Server Error**: S3 configuration issues or upload failures

## Testing

You can test the upload functionality using curl:

```bash
# Upload audio file
curl -X POST "http://localhost:8000/verification/upload-audio-file" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -F "audio_file=@/path/to/audio.mp3"

# Upload with S3 URL
curl -X POST "http://localhost:8000/verification/upload-audio-url" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"audio_file_url": "https://bucket.s3.region.amazonaws.com/audio.mp3"}'
```
