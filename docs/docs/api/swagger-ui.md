---
sidebar_position: 7
title: Interactive API Explorer
description: Interactive Swagger UI for testing API endpoints
---

# Interactive API Explorer

Use the interactive Swagger UI below to explore and test the Saathii Backend API endpoints directly from your browser.

import SwaggerUI from '@site/src/components/SwaggerUI';

<SwaggerUI url="https://saathiiapp.com/docs" height="800px" />

## How to Use

1. **Authentication**: Click on the "Authorize" button to add your access token
2. **Explore Endpoints**: Browse through different API categories
3. **Test Requests**: Click "Try it out" on any endpoint to test it
4. **View Responses**: See real-time responses and error messages

## Authentication

To use the interactive API explorer:

1. **Get an Access Token**:
   - Use the `/auth/request_otp` endpoint to request an OTP
   - Use the `/auth/verify` endpoint to verify the OTP and get tokens
   - Or use the `/auth/register` endpoint if you need to register

2. **Authorize**:
   - Click the "Authorize" button at the top of the page
   - Enter your access token in the format: `Bearer <your_access_token>`
   - Click "Authorize" to authenticate

3. **Test Endpoints**:
   - All protected endpoints will now use your token automatically
   - You can test any endpoint by clicking "Try it out"

## Available Endpoints

### Authentication
- `POST /auth/request_otp` - Request OTP for phone number
- `POST /auth/resend_otp` - Resend OTP
- `POST /auth/verify` - Verify OTP and get tokens
- `POST /auth/register` - Complete user registration
- `POST /auth/refresh` - Refresh access token
- `POST /auth/logout` - Logout and invalidate tokens

### User Management
- `GET /users/me` - Get current user profile
- `PUT /users/me` - Update user profile
- `DELETE /users/me` - Delete user account
- `GET /users/me/status` - Get user presence status
- `PUT /users/me/status` - Update user presence status
- `POST /users/me/heartbeat` - Send heartbeat

### Feed System
- `GET /feed/listeners` - Get listeners feed
- `GET /feed/stats` - Get feed statistics

### Call Management
- `POST /calls/start` - Start a new call
- `POST /calls/end` - End an ongoing call
- `GET /calls/ongoing` - Get ongoing call details
- `GET /calls/history` - Get call history
- `GET /calls/balance` - Get coin balance
- `POST /calls/recharge` - Recharge coins

### Listener Verification
- `POST /verification/upload-audio-file` - Upload audio file
- `POST /verification/upload-audio-url` - Upload audio URL
- `GET /verification/status` - Check verification status
- `GET /verification/history` - Get verification history

## Tips for Testing

### 1. Start with Authentication
Always begin by authenticating using the OTP flow:
1. Request OTP with your phone number
2. Verify OTP to get access and refresh tokens
3. Use the access token to authorize requests

### 2. Test User Management
After authentication, test user profile operations:
1. Get your current user profile
2. Update your profile information
3. Check your presence status

### 3. Explore Feed System
Test the feed functionality:
1. Get listeners feed with different filters
2. Check feed statistics
3. Test pagination parameters

### 4. Test Call Management
If you have coins, test call operations:
1. Check your coin balance
2. Start a call with a listener
3. End the call and see the billing

### 5. WebSocket Testing
For real-time features, use a WebSocket client:
- Connect to `wss://saathiiapp.com/ws/feed?token=<your_token>`
- Connect to `wss://saathiiapp.com/ws/presence?token=<your_token>`

## Error Handling

The API returns detailed error messages for different scenarios:

- **400 Bad Request**: Invalid input data
- **401 Unauthorized**: Invalid or expired token
- **403 Forbidden**: Insufficient permissions
- **404 Not Found**: Resource not found
- **429 Too Many Requests**: Rate limit exceeded
- **500 Internal Server Error**: Server error

## Rate Limits

Be aware of the following rate limits:

- **OTP Requests**: 5 requests per 15 minutes per phone number
- **OTP Resend**: 1 resend per 60 seconds per phone number
- **Feed Requests**: 100 requests per minute per user
- **WebSocket Connections**: 5 concurrent connections per user

## Production vs Development

- **Development**: Uses `http://localhost:8000`
- **Production**: Uses `https://saathiiapp.com`
- **HTTPS**: Always use HTTPS in production
- **CORS**: Configured for production domain

## Need Help?

- **API Documentation**: Check the detailed [API Reference](./authentication)
- **Integration Guides**: Follow the [React Native Integration Guide](../guides/react-native-integration)
- **Examples**: See [API Examples](../guides/api-examples)
- **GitHub Issues**: [Report issues](https://github.com/saathii/saathii-backend-api/issues)
