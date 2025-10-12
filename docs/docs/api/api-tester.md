---
sidebar_position: 8
title: API Tester
description: Interactive Postman-like API testing interface for the Saathii Backend API
---

# API Tester

Test the Saathii Backend API endpoints directly from your browser with our interactive API testing interface. This tool provides a Postman-like experience with a clean, intuitive interface.

import APITester from '@site/src/components/APITester';

<APITester baseUrl="https://saathiiapp.com" height="700px" />

## How to Use

### 1. Select HTTP Method
Choose from GET, POST, PUT, DELETE, or PATCH methods using the dropdown.

### 2. Enter Endpoint URL
Type the API endpoint path (e.g., `/auth/request_otp`, `/users/me`, `/calls/start`).

### 3. Add Query Parameters
For GET requests or any endpoint that accepts query parameters:
- Click "Add" to add new parameters
- Enter key-value pairs for each parameter
- Remove parameters by clicking the "×" button

### 4. Set Headers
Configure request headers:
- Default headers include `Content-Type: application/json`
- Add `Authorization: Bearer <your_token>` for protected endpoints
- Add custom headers as needed

### 5. Request Body
For POST, PUT, and PATCH requests:
- Enter JSON data in the body textarea
- Use proper JSON formatting
- Example: `{"phone": "+919876543210"}`

### 6. Send Request
Click the "Send" button to execute the request and view the response.

## Example Requests

### Authentication Flow

**1. Request OTP:**
- Method: `POST`
- URL: `/auth/request_otp`
- Body: `{"phone": "+919876543210"}`

**2. Verify OTP:**
- Method: `POST`
- URL: `/auth/verify`
- Body: `{"phone": "+919876543210", "otp": "123456"}`

**3. Get User Profile:**
- Method: `GET`
- URL: `/users/me`
- Headers: `Authorization: Bearer <access_token>`

### Call Management

**1. Start a Call:**
- Method: `POST`
- URL: `/calls/start`
- Headers: `Authorization: Bearer <access_token>`
- Body: `{"listener_id": 123, "call_type": "audio"}`

**2. Get Call History:**
- Method: `GET`
- URL: `/calls/history`
- Headers: `Authorization: Bearer <access_token>`
- Query Parameters: `page=1`, `per_page=10`

### Feed System

**1. Get Listeners Feed:**
- Method: `GET`
- URL: `/feed/listeners`
- Headers: `Authorization: Bearer <access_token>`
- Query Parameters: `page=1`, `per_page=20`, `online_only=true`

## Features

### ✅ **Real-time Testing**
- Test API endpoints instantly without leaving the documentation
- See response times and status codes
- View formatted JSON responses

### ✅ **Authentication Support**
- Easy token management
- Pre-configured authorization headers
- Support for Bearer tokens

### ✅ **Request Configuration**
- All HTTP methods supported
- Query parameters management
- Custom headers
- JSON request body support

### ✅ **Response Analysis**
- Status code with color coding
- Response time measurement
- Formatted JSON output
- Error handling and display

### ✅ **User-friendly Interface**
- Clean, intuitive design
- Dark/light theme support
- Responsive layout
- Keyboard shortcuts

## Tips for Testing

### 1. **Start with Authentication**
Always begin by getting an access token:
1. Request OTP with your phone number
2. Verify OTP to get access and refresh tokens
3. Use the access token in the Authorization header

### 2. **Use Proper Headers**
- Set `Content-Type: application/json` for JSON requests
- Include `Authorization: Bearer <token>` for protected endpoints
- Add custom headers as needed for specific endpoints

### 3. **Test Different Scenarios**
- Test with valid data
- Test with invalid data to see error responses
- Test edge cases and boundary conditions

### 4. **Check Response Codes**
- 200-299: Success responses
- 400-499: Client errors (bad request, unauthorized, etc.)
- 500-599: Server errors

## Troubleshooting

### Common Issues

**CORS Errors:**
- The API tester handles CORS automatically
- If you encounter CORS issues, check that the API server is running

**Authentication Errors:**
- Ensure you're using a valid access token
- Check that the token hasn't expired
- Verify the Authorization header format: `Bearer <token>`

**Request Timeout:**
- Check your internet connection
- Verify the API server is accessible
- Try reducing the request body size

**Invalid JSON:**
- Ensure request body is valid JSON
- Check for missing quotes or commas
- Use a JSON validator if needed

## Need Help?

- **API Documentation**: Check the detailed [API Reference](./authentication)
- **Examples**: See [API Examples](../guides/api-examples)
- **GitHub Issues**: [Report issues](https://github.com/saathiiapp/saathii_backend_fastapi/issues)
