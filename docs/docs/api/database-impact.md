---
sidebar_position: 12
title: Database Impact Analysis
description: Complete database operations and table impacts for each API endpoint
---

# Database Impact Analysis

This document explains what happens in the database for each API endpoint, which tables are impacted, and how.

## Database Tables Overview

- **`users`** - User profiles and basic information
- **`user_roles`** - User role assignments (listener, admin, etc.)
- **`user_status`** - User presence and online status
- **`user_wallets`** - User coin balances and wallet information
- **`user_transactions`** - All coin transactions (spend, earn, purchase, etc.)
- **`user_calls`** - Call records and history
- **`user_favorites`** - User favorite relationships
- **`user_blocks`** - User blocking relationships
- **`listener_verifications`** - Audio verification submissions
- **`user_withdrawals`** - Withdrawal requests and history

---

## 🔐 Authentication APIs

### `POST /auth/request_otp`
**Database Impact:** None
- **Redis Only:** Stores OTP temporarily (`otp:{phone}`)
- **Rate Limiting:** Redis counter (`otp_rl:{phone}`)

### `POST /auth/resend_otp`
**Database Impact:** None
- **Redis Only:** Reuses existing OTP or generates new one
- **Throttling:** Redis key (`otp_resend:{phone}`)

### `POST /auth/verify`
**Database Impact:** READ + UPDATE
- **Tables:** `users`, `user_status`
- **Operations:**
  - `SELECT * FROM users WHERE phone = $1` - Check if user exists
  - `UPDATE user_status SET is_online = TRUE, last_seen = now() WHERE user_id = $1` - Set user online
- **Redis:** Deletes OTP, stores refresh token

### `POST /auth/register`
**Database Impact:** INSERT + INSERT
- **Tables:** `users`, `user_roles`, `user_status`
- **Operations:**
  - `INSERT INTO users (username, phone, sex, dob, bio, interests, preferred_language, created_at) VALUES (...)`
  - `INSERT INTO user_roles (user_id, role) VALUES ($1, $2)` - If role provided
  - `INSERT INTO user_status (user_id, is_online, last_seen, is_busy, updated_at, created_at) VALUES ($1, TRUE, now(), FALSE, now(), now())`
- **Redis:** Stores refresh token

### `POST /auth/refresh`
**Database Impact:** None
- **Redis Only:** 
  - Deletes old refresh token (`refresh:{user_id}:{jti}`)
  - Stores new refresh token

### `POST /auth/logout`
**Database Impact:** UPDATE
- **Tables:** `user_status`
- **Operations:**
  - `UPDATE user_status SET is_online = FALSE, last_seen = now() WHERE user_id = $1`
- **Redis:** Blacklists access token, deletes all refresh tokens

---

## 👤 User Management APIs

### `GET /users/me`
**Database Impact:** READ
- **Tables:** `users`, `user_roles`
- **Operations:**
  - `SELECT u.*, array_agg(ur.role) FILTER (WHERE ur.active = TRUE) AS roles FROM users u LEFT JOIN user_roles ur ON u.user_id = ur.user_id WHERE u.user_id = $1 GROUP BY u.user_id`

### `PUT /users/me`
**Database Impact:** UPDATE
- **Tables:** `users`
- **Operations:**
  - `UPDATE users SET username=COALESCE($2, username), bio=COALESCE($3, bio), rating=COALESCE($4, rating), interests=COALESCE($5, interests), profile_image_url=COALESCE($6, profile_image_url), preferred_language=COALESCE($7, preferred_language), updated_at=now() WHERE user_id=$1`

### `DELETE /users/me`
**Database Impact:** DELETE + DELETE
- **Tables:** `user_roles`, `users`
- **Operations:**
  - `DELETE FROM user_roles WHERE user_id=$1` - Remove roles first (FK constraint)
  - `DELETE FROM users WHERE user_id=$1` - Delete user (CASCADE removes related records)
- **Redis:** Cleans up all user tokens

---

## 📡 Presence & Status APIs

### `GET /users/me/status`
**Database Impact:** READ
- **Tables:** `user_status`
- **Operations:**
  - `SELECT * FROM user_status WHERE user_id = $1`

### `PUT /users/me/status`
**Database Impact:** UPDATE
- **Tables:** `user_status`
- **Operations:**
  - `UPDATE user_status SET is_online = $2, is_busy = $3, wait_time = $4, updated_at = now() WHERE user_id = $1`
- **Redis:** Broadcasts status update via WebSocket

### `POST /users/me/heartbeat`
**Database Impact:** UPDATE
- **Tables:** `user_status`
- **Operations:**
  - `UPDATE user_status SET last_seen = now(), updated_at = now() WHERE user_id = $1`
- **Redis:** Broadcasts status update

### `GET /users/{user_id}/presence`
**Database Impact:** READ
- **Tables:** `user_status`, `users`
- **Operations:**
  - `SELECT us.user_id, u.username, us.is_online, us.is_busy, us.wait_time FROM user_status us JOIN users u ON us.user_id = u.user_id WHERE us.user_id = $1`

### `GET /users/presence`
**Database Impact:** READ
- **Tables:** `user_status`, `users`
- **Operations:**
  - `SELECT us.user_id, u.username, us.is_online, us.is_busy, us.wait_time FROM user_status us JOIN users u ON us.user_id = u.user_id WHERE us.user_id = ANY($1)`

### `POST /admin/cleanup-presence`
**Database Impact:** UPDATE + UPDATE
- **Tables:** `user_status` (multiple rows)
- **Operations:**
  - Marks inactive users offline
  - Clears expired busy status
- **Redis:** Broadcasts status changes

---

## 📰 Feed APIs

### `GET /feed/listeners`
**Database Impact:** READ
- **Tables:** `users`, `user_roles`, `user_status`, `user_blocks`
- **Operations:**
  - Complex query with JOINs to get listeners with status, excluding blocked users
  - Filters by online status, gender, rating, interests, language
  - Pagination support

### `GET /feed/stats`
**Database Impact:** READ
- **Tables:** `users`, `user_status`
- **Operations:**
  - Multiple COUNT queries for statistics
  - Aggregates by gender, language, interests

---

## ⭐ Favorites APIs

### `POST /favorites/add`
**Database Impact:** INSERT
- **Tables:** `user_favorites`
- **Operations:**
  - `INSERT INTO user_favorites (favoriter_id, favoritee_id, created_at) VALUES ($1, $2, now())`

### `DELETE /favorites/remove`
**Database Impact:** DELETE
- **Tables:** `user_favorites`
- **Operations:**
  - `DELETE FROM user_favorites WHERE favoriter_id = $1 AND favoritee_id = $2`

### `GET /favorites`
**Database Impact:** READ
- **Tables:** `user_favorites`, `users`, `user_status`
- **Operations:**
  - `SELECT uf.*, u.username, u.sex, u.bio, u.profile_image_url, u.rating, us.is_online, us.is_busy, us.last_seen FROM user_favorites uf JOIN users u ON uf.favoritee_id = u.user_id LEFT JOIN user_status us ON u.user_id = us.user_id WHERE uf.favoriter_id = $1`

### `GET /favorites/check/{listener_id}`
**Database Impact:** READ
- **Tables:** `user_favorites`, `users`
- **Operations:**
  - `SELECT uf.favoriter_id FROM user_favorites uf WHERE uf.favoriter_id = $1 AND uf.favoritee_id = $2`

---

## 💰 Wallet APIs

### `GET /wallet/balance`
**Database Impact:** READ
- **Tables:** `user_wallets`
- **Operations:**
  - `SELECT * FROM user_wallets WHERE user_id = $1`

### `POST /wallet/add-coins`
**Database Impact:** INSERT + UPDATE + INSERT
- **Tables:** `user_wallets`, `user_transactions`
- **Operations:**
  - `INSERT INTO user_wallets (user_id, balance_coins, created_at, updated_at) VALUES ($1, 0, now(), now()) ON CONFLICT (user_id) DO NOTHING` - Create wallet if not exists
  - `UPDATE user_wallets SET balance_coins = $1, updated_at = now() WHERE wallet_id = $2` - Update balance
  - `INSERT INTO user_transactions (wallet_id, tx_type, coins_change, money_change, created_at, updated_at) VALUES ($1, $2, $3, $4, now(), now())` - Record transaction

### `GET /wallet/earnings`
**Database Impact:** READ
- **Tables:** `user_transactions`, `user_wallets`
- **Operations:**
  - `SELECT SUM(coins_change) FROM user_transactions WHERE wallet_id = $1 AND tx_type = 'earn'`

### `POST /wallet/withdraw`
**Database Impact:** INSERT
- **Tables:** `user_withdrawals`
- **Operations:**
  - `INSERT INTO user_withdrawals (user_id, amount, bank_account_number, ifsc_code, account_holder_name, status, created_at) VALUES ($1, $2, $3, $4, $5, 'pending', now())`

### `GET /wallet/withdrawals`
**Database Impact:** READ
- **Tables:** `user_withdrawals`
- **Operations:**
  - `SELECT * FROM user_withdrawals WHERE user_id = $1 ORDER BY created_at DESC`

### `PUT /wallet/bank-details`
**Database Impact:** UPDATE
- **Tables:** `user_wallets`
- **Operations:**
  - `UPDATE user_wallets SET bank_account_number = $2, ifsc_code = $3, account_holder_name = $4, updated_at = now() WHERE user_id = $1`

### `GET /wallet/bank-details`
**Database Impact:** READ
- **Tables:** `user_wallets`
- **Operations:**
  - `SELECT bank_account_number, ifsc_code, account_holder_name FROM user_wallets WHERE user_id = $1`

---

## 🚫 Blocking APIs

### `POST /block`
**Database Impact:** INSERT
- **Tables:** `user_blocks`
- **Operations:**
  - `INSERT INTO user_blocks (blocker_id, blocked_id, action_type, reason, created_at) VALUES ($1, $2, $3, $4, now())`

### `DELETE /block`
**Database Impact:** DELETE
- **Tables:** `user_blocks`
- **Operations:**
  - `DELETE FROM user_blocks WHERE blocker_id = $1 AND blocked_id = $2`

### `GET /blocked`
**Database Impact:** READ
- **Tables:** `user_blocks`, `users`
- **Operations:**
  - `SELECT ub.*, u.username, u.sex, u.bio, u.profile_image_url FROM user_blocks ub JOIN users u ON ub.blocked_id = u.user_id WHERE ub.blocker_id = $1`

### `GET /block/check/{user_id}`
**Database Impact:** READ
- **Tables:** `user_blocks`
- **Operations:**
  - `SELECT blocker_id FROM user_blocks WHERE blocker_id = $1 AND blocked_id = $2`

---

## ✅ Verification APIs

### `POST /verification/upload-audio-file`
**Database Impact:** INSERT
- **Tables:** `listener_verifications`
- **Operations:**
  - `INSERT INTO listener_verifications (user_id, audio_url, status, submitted_at) VALUES ($1, $2, 'pending', now())`
- **S3:** Uploads audio file

### `POST /verification/upload-audio-url`
**Database Impact:** INSERT
- **Tables:** `listener_verifications`
- **Operations:**
  - `INSERT INTO listener_verifications (user_id, audio_url, status, submitted_at) VALUES ($1, $2, 'pending', now())`

### `GET /verification/status`
**Database Impact:** READ
- **Tables:** `listener_verifications`
- **Operations:**
  - `SELECT * FROM listener_verifications WHERE user_id = $1 ORDER BY submitted_at DESC LIMIT 1`

### `GET /verification/history`
**Database Impact:** READ
- **Tables:** `listener_verifications`
- **Operations:**
  - `SELECT * FROM listener_verifications WHERE user_id = $1 ORDER BY submitted_at DESC`

### `GET /admin/verification/pending`
**Database Impact:** READ
- **Tables:** `listener_verifications`, `users`
- **Operations:**
  - `SELECT lv.*, u.username FROM listener_verifications lv JOIN users u ON lv.user_id = u.user_id WHERE lv.status = 'pending'`

### `POST /admin/verification/review`
**Database Impact:** UPDATE
- **Tables:** `listener_verifications`
- **Operations:**
  - `UPDATE listener_verifications SET status = $2, reviewer_notes = $3, reviewed_at = now(), reviewer_id = $4 WHERE verification_id = $1`

---

## 📞 Call Management APIs

### `POST /calls/start`
**Database Impact:** INSERT + UPDATE + UPDATE + INSERT
- **Tables:** `user_wallets`, `user_calls`, `user_status` (2 rows)
- **Operations:**
  - `INSERT INTO user_wallets (user_id, balance_coins, created_at) VALUES ($1, 0, now()) ON CONFLICT (user_id) DO NOTHING` - Ensure wallet exists
  - `UPDATE user_wallets SET balance_coins = balance_coins - $2 WHERE user_id = $1` - Reserve coins
  - `INSERT INTO user_calls (user_id, listener_id, call_type, status, coins_spent, listener_money_earned) VALUES ($1, $2, $3, 'ongoing', $4, 0)` - Create call record
  - `UPDATE user_status SET is_busy = TRUE, wait_time = $2, updated_at = now() WHERE user_id = $1` - Set caller busy
  - `UPDATE user_status SET is_busy = TRUE, wait_time = $2, updated_at = now() WHERE user_id = $1` - Set listener busy
- **Redis:** Stores call info for real-time tracking

### `POST /calls/end`
**Database Impact:** UPDATE + UPDATE + UPDATE + UPDATE
- **Tables:** `user_calls`, `user_wallets` (2 rows), `user_status` (2 rows)
- **Operations:**
  - `UPDATE user_calls SET end_time = $1, duration_seconds = $2, duration_minutes = $3, coins_spent = $4, listener_money_earned = $5, status = $6, updated_at = now() WHERE call_id = $7` - Update call record
  - `UPDATE user_wallets SET balance_coins = balance_coins - $2 WHERE user_id = $1` - Deduct additional coins from caller
  - `UPDATE user_wallets SET balance_coins = balance_coins + $2 WHERE user_id = $1` - Add earnings to listener
  - `UPDATE user_status SET is_busy = FALSE, wait_time = NULL, updated_at = now() WHERE user_id = $1` - Set caller available
  - `UPDATE user_status SET is_busy = FALSE, wait_time = NULL, updated_at = now() WHERE user_id = $1` - Set listener available
- **Redis:** Removes call info

### `GET /calls/ongoing`
**Database Impact:** READ
- **Tables:** `user_calls`, `users` (2 rows)
- **Operations:**
  - `SELECT uc.*, u1.username as caller_username, u2.username as listener_username FROM user_calls uc LEFT JOIN users u1 ON uc.user_id = u1.user_id LEFT JOIN users u2 ON uc.listener_id = u2.user_id WHERE (uc.user_id = $1 OR uc.listener_id = $1) AND uc.status = 'ongoing'`

### `GET /calls/history`
**Database Impact:** READ
- **Tables:** `user_calls`, `users` (2 rows)
- **Operations:**
  - Complex query with JOINs, filtering, and pagination
  - `SELECT uc.*, u1.username as caller_username, u2.username as listener_username FROM user_calls uc LEFT JOIN users u1 ON uc.user_id = u1.user_id LEFT JOIN users u2 ON uc.listener_id = u2.user_id WHERE (uc.user_id = $1 OR uc.listener_id = $1) ORDER BY uc.created_at DESC`

### `GET /calls/history/summary`
**Database Impact:** READ
- **Tables:** `user_calls`
- **Operations:**
  - Multiple aggregation queries for call statistics

### `GET /calls/balance`
**Database Impact:** READ
- **Tables:** `user_wallets`
- **Operations:**
  - `SELECT balance_coins FROM user_wallets WHERE user_id = $1`

### `POST /calls/recharge`
**Database Impact:** INSERT + UPDATE + INSERT
- **Tables:** `user_wallets`, `user_transactions`
- **Operations:**
  - `INSERT INTO user_wallets (user_id, balance_coins, created_at) VALUES ($1, 0, now()) ON CONFLICT (user_id) DO NOTHING` - Ensure wallet exists
  - `UPDATE user_wallets SET balance_coins = balance_coins + $2 WHERE user_id = $1` - Add coins
  - `INSERT INTO user_transactions (wallet_id, tx_type, coins_change, money_change, created_at, updated_at) VALUES ($1, 'purchase', $2, $3, now(), now())` - Record transaction

### `GET /calls/recharge/history`
**Database Impact:** READ
- **Tables:** `user_transactions`, `user_wallets`
- **Operations:**
  - `SELECT ut.* FROM user_transactions ut JOIN user_wallets uw ON ut.wallet_id = uw.wallet_id WHERE uw.user_id = $1 AND ut.tx_type = 'purchase' ORDER BY ut.created_at DESC`

### `POST /calls/bill-minute/{call_id}`
**Database Impact:** UPDATE + UPDATE
- **Tables:** `user_calls`, `user_wallets`
- **Operations:**
  - `UPDATE user_calls SET coins_spent = coins_spent + $2, updated_at = now() WHERE call_id = $1` - Update call billing
  - `UPDATE user_wallets SET balance_coins = balance_coins - $2 WHERE user_id = $1` - Deduct coins

### `POST /calls/emergency-end/{call_id}`
**Database Impact:** UPDATE + UPDATE + UPDATE + UPDATE
- **Tables:** `user_calls`, `user_wallets` (2 rows), `user_status` (2 rows)
- **Operations:**
  - Similar to regular call end but with emergency status
  - Updates call record, wallet balances, and user status

### `POST /calls/cleanup`
**Database Impact:** UPDATE + UPDATE
- **Tables:** `user_calls`, `user_status` (multiple rows)
- **Operations:**
  - Cleans up expired calls
  - Resets user busy status

### `GET /calls/status`
**Database Impact:** READ
- **Tables:** `user_calls`, `user_status`
- **Operations:**
  - Multiple aggregation queries for system statistics

### `GET /calls/rates`
**Database Impact:** None
- **Operations:** Returns static configuration data

---

## 📊 Transaction APIs

### `GET /transactions/user`
**Database Impact:** READ
- **Tables:** `user_transactions`, `user_wallets`
- **Operations:**
  - `SELECT ut.* FROM user_transactions ut JOIN user_wallets uw ON ut.wallet_id = uw.wallet_id WHERE uw.user_id = $1 ORDER BY ut.created_at DESC`

### `GET /transactions/listener`
**Database Impact:** READ
- **Tables:** `user_transactions`, `user_wallets`
- **Operations:**
  - `SELECT ut.* FROM user_transactions ut JOIN user_wallets uw ON ut.wallet_id = uw.wallet_id WHERE uw.user_id = $1 AND ut.tx_type = 'earn' ORDER BY ut.created_at DESC`

---

## 🔌 WebSocket APIs

### `WS /ws/feed`
**Database Impact:** None
- **Redis Only:** Manages WebSocket connections and broadcasts

### `WS /ws/presence`
**Database Impact:** None
- **Redis Only:** Manages WebSocket connections and broadcasts

---

## Summary

- **Most Read Operations:** Feed, presence, favorites, call history
- **Most Write Operations:** Call management, wallet transactions, user status
- **Heavy Database Impact:** Call start/end (multiple table updates)
- **Redis Intensive:** Authentication, presence updates, real-time features
- **Cascade Deletes:** User deletion removes all related records
- **Transaction Safety:** Wallet operations use database transactions
- **Real-time Updates:** Status changes broadcast via Redis/WebSocket
