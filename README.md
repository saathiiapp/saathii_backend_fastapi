# saathii_backend_fastapi

## React Native (Expo) API Guide

This guide explains how a React Native Expo app should use the authentication APIs (OTP login/registration, access/refresh tokens) and user endpoints.

### Base URL
- Local: `http://localhost:8000`

### Authentication Overview
- OTP-based login with optional registration step
- Token model:
  - Access token: short-lived (default ~30m), used in `Authorization: Bearer <access>`
  - Refresh token: long-lived (default ~30d), rotated on refresh, stored server-side in Redis by `jti`
  - Registration token: short-lived (default ~10m), used only to finalize registration

### Endpoints

1) Request OTP
- `POST /auth/request_otp`
- Body:
```json
{ "phone": "+919876543210" }
```
- Responses:
  - 200 `{ "message": "OTP sent" }`
  - 429 Too many requests (simple rate limit: 5 per 15 minutes)

1a) Resend OTP
- `POST /auth/resend_otp`
- Body:
```json
{ "phone": "+919876543210" }
```
- Behavior:
  - Throttle: 1 resend per 60 seconds per phone
  - If an OTP is active, re-sends the same code without changing its TTL
  - If no OTP is active, generates and sends a new code (5 minute TTL)
- Responses:
  - 200 `{ "message": "OTP re-sent" }` or `{ "message": "OTP sent" }`
  - 429 on throttle

2) Verify OTP
- `POST /auth/verify`
- Body:
```json
{ "phone": "+919876543210", "otp": "123456" }
```
- Responses:
  - 200 Registered user:
```json
{ "status": "registered", "access_token": "...", "refresh_token": "..." }
```
  - 200 Needs registration:
```json
{ "status": "needs_registration", "registration_token": "..." }
```
  - 400 Invalid/expired OTP

3) Register (new users only)
- `POST /auth/register`
- Body:
```json
{
  "registration_token": "...",
  "username": "alice",
  "sex": "female",
  "dob": "2000-01-01",
  "bio": "...",
  "interests": ["music", "tech"],
  "profile_image_url": "https://...",
  "preferred_language": "en",
  "role": "user"
}
```
- Response (200):
```json
{ "access_token": "...", "refresh_token": "..." }
```

4) Refresh tokens (rotation)
- `POST /auth/refresh`
- Body:
```json
{ "refresh_token": "..." }
```
- Response (200):
```json
{ "access_token": "...", "refresh_token": "..." }
```
- Notes:
  - Refresh tokens are single-use. If reused, server returns 401.

5) Logout
- `POST /auth/logout`
- Headers: `Authorization: Bearer <access_token>`
- Behavior: blacklists current access token and revokes all refresh tokens for the user

6) Get current user
- `GET /users/me`
- Headers: `Authorization: Bearer <access_token>`
- Response (200): user profile with active roles

7) Update current user
- `PUT /users/me`
- Headers: `Authorization: Bearer <access_token>`
- Body (any subset):
```json
{
  "username": "newname",
  "bio": "...",
  "rating": 4.8,
  "interests": ["..."],
  "profile_image_url": "https://...",
  "preferred_language": "en"
}
```
- Response (200): updated user

8) Delete current user
- `DELETE /users/me`
- Headers: `Authorization: Bearer <access_token>`
- Response (200): `{ "message": "User deleted" }`

### React Native (Expo) Client Patterns

Storage
- Access token: keep in memory (React state/context)
- Refresh token: secure storage (`expo-secure-store` or `react-native-keychain`)

Axios setup
```ts
import axios from 'axios';
import * as SecureStore from 'expo-secure-store';

export const api = axios.create({ baseURL: 'http://localhost:8000' });

let accessToken: string | null = null;

export function setTokens(access: string, refresh: string) {
  accessToken = access;
  SecureStore.setItemAsync('refresh_token', refresh);
}

api.interceptors.request.use(async (config) => {
  if (accessToken) {
    config.headers = config.headers || {};
    config.headers.Authorization = `Bearer ${accessToken}`;
  }
  return config;
});

let isRefreshing = false;
let pending: Array<(t: string|null) => void> = [];

api.interceptors.response.use(
  (res) => res,
  async (error) => {
    if (error.response?.status === 401) {
      const refresh = await SecureStore.getItemAsync('refresh_token');
      if (!refresh) throw error;

      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          pending.push((t) => {
            if (t) {
              error.config.headers.Authorization = `Bearer ${t}`;
              resolve(api.request(error.config));
            } else {
              reject(error);
            }
          });
        });
      }

      isRefreshing = true;
      try {
        const { data } = await api.post('/auth/refresh', { refresh_token: refresh });
        setTokens(data.access_token, data.refresh_token);
        pending.forEach((cb) => cb(data.access_token));
        pending = [];
        error.config.headers.Authorization = `Bearer ${data.access_token}`;
        return api.request(error.config);
      } catch (e) {
        pending.forEach((cb) => cb(null));
        pending = [];
        accessToken = null;
        await SecureStore.deleteItemAsync('refresh_token');
        // TODO: navigate to login
        throw e;
      } finally {
        isRefreshing = false;
      }
    }
    throw error;
  }
);
```

Auth flow
1. Request OTP → `/auth/request_otp`
2. Verify OTP → `/auth/verify`
   - If `status=needs_registration`, navigate to Registration
   - Else call `setTokens(access_token, refresh_token)` and go to app
3. Registration → `/auth/register` then `setTokens(...)`
4. On app start: if a refresh token exists, call `/auth/refresh` to bootstrap session
5. On 401 at any time, interceptor refreshes and retries; if refresh fails, navigate to login
6. Logout → `/auth/logout`, then clear tokens

Curl examples
```bash
curl -X POST 'http://localhost:8000/auth/request_otp' \
  -H 'Content-Type: application/json' \
  -d '{"phone":"+919876543210"}'

curl -X POST 'http://localhost:8000/auth/resend_otp' \
  -H 'Content-Type: application/json' \
  -d '{"phone":"+919876543210"}'

curl -X POST 'http://localhost:8000/auth/verify' \
  -H 'Content-Type: application/json' \
  -d '{"phone":"+919876543210","otp":"123456"}'

curl -X POST 'http://localhost:8000/auth/register' \
  -H 'Content-Type: application/json' \
  -d '{"registration_token":"...","username":"alice"}'

curl -X POST 'http://localhost:8000/auth/refresh' \
  -H 'Content-Type: application/json' \
  -d '{"refresh_token":"..."}'

curl -X POST 'http://localhost:8000/auth/logout' \
  -H 'Authorization: Bearer <ACCESS>'

curl -X GET 'http://localhost:8000/users/me' \
  -H 'Authorization: Bearer <ACCESS>'
```
