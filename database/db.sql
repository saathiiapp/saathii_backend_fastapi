-- 1) Users (profile data)
CREATE TABLE IF NOT EXISTS users (
  user_id       SERIAL PRIMARY KEY,
  username      VARCHAR(10) UNIQUE NOT NULL,
  sex           VARCHAR(10) CHECK (sex IN ('male','female')),
  dob           DATE NOT NULL,
  phone         VARCHAR(20) UNIQUE NOT NULL,
  preferred_language VARCHAR(50),
  profile_image_url TEXT,  -- S3 URL for profile picture
  rating        NUMERIC(3,2) DEFAULT 0,
  interests     TEXT[],
  bio           TEXT,
  country       VARCHAR(100) DEFAULT 'India',
  updated_at    TIMESTAMPTZ DEFAULT now(),
  created_at      TIMESTAMPTZ DEFAULT now()
);

-- 2) Roles (a user can have multiple roles)
CREATE TABLE IF NOT EXISTS user_roles (
  user_id   INT REFERENCES users(user_id) ON DELETE CASCADE,
  role      VARCHAR(20) CHECK (role IN ('customer','listener')),
  active    BOOLEAN DEFAULT TRUE,
  assigned_at TIMESTAMPTZ DEFAULT now(),
  PRIMARY KEY (user_id, role)
);

-- 3) Wallets (one per user)
CREATE TABLE IF NOT EXISTS user_wallets (
  wallet_id        SERIAL PRIMARY KEY,
  user_id          INT UNIQUE REFERENCES users(user_id) ON DELETE CASCADE,
  balance_coins    BIGINT DEFAULT 0,               -- integer coins
  withdrawable_money NUMERIC(12,2) DEFAULT 0.00,   -- money ready for bank withdrawal
  updated_at    TIMESTAMPTZ DEFAULT now(),
  created_at      TIMESTAMPTZ DEFAULT now()
);

-- 4) Transactions (wallet audit trail)
CREATE TABLE IF NOT EXISTS user_transactions (
  transaction_id  SERIAL PRIMARY KEY,
  wallet_id       INT REFERENCES user_wallets(wallet_id) ON DELETE CASCADE,
  tx_type         VARCHAR(20) CHECK (tx_type IN ('purchase','spend','earn','withdraw','bonus', 'referral_bonus')),
  coins_change    BIGINT DEFAULT 0,           -- positive = credit, negative = debit
  money_change    NUMERIC(12,2) DEFAULT 0.00, -- positive/negative
  updated_at    TIMESTAMPTZ DEFAULT now(),
  created_at      TIMESTAMPTZ DEFAULT now()
);

-- 5) User status
CREATE TABLE IF NOT EXISTS user_status (
  user_id   INT PRIMARY KEY REFERENCES users(user_id) ON DELETE CASCADE,
  is_online     BOOLEAN DEFAULT FALSE,   -- online/offline presence
  last_seen     TIMESTAMPTZ DEFAULT now(),
  is_busy       BOOLEAN DEFAULT FALSE,   -- whether currently on a call
  wait_time     INT,                     -- if on call, expected duration in minutes
  is_active     BOOLEAN DEFAULT TRUE,    -- whether user account is active
  updated_at    TIMESTAMPTZ DEFAULT now(),
  created_at      TIMESTAMPTZ DEFAULT now()
);

-- 6) Calls (history + ongoing)
CREATE TABLE IF NOT EXISTS user_calls (
  call_id         SERIAL PRIMARY KEY,
  user_id         INT REFERENCES users(user_id) ON DELETE CASCADE,
  listener_id     INT REFERENCES users(user_id) ON DELETE CASCADE,
  call_type       VARCHAR(10) CHECK (call_type IN ('audio','video')),
  start_time      TIMESTAMPTZ NOT NULL DEFAULT now(),
  end_time        TIMESTAMPTZ,
  duration_seconds INT,
  duration_minutes INT,
  coins_spent     BIGINT DEFAULT 0,
  listener_money_earned BIGINT DEFAULT 0,
  status          VARCHAR(20) CHECK (status IN ('ongoing','completed','dropped')) DEFAULT 'ongoing',
  updated_at    TIMESTAMPTZ DEFAULT now(),
  created_at      TIMESTAMPTZ DEFAULT now()
);

-- 7) Streak
CREATE TABLE IF NOT EXISTS user_streaks (
  user_id        INT PRIMARY KEY REFERENCES users(user_id) ON DELETE CASCADE,
  current_streak INT DEFAULT 0,              -- ongoing streak in days
  longest_streak INT DEFAULT 0,              -- best ever streak
  last_active    DATE,                       -- last day they were active
  updated_at     TIMESTAMPTZ DEFAULT now()
);

-- 8) Favorites (users can favorites others)
CREATE TABLE IF NOT EXISTS user_favorites (
  favoriter_id  INT REFERENCES users(user_id) ON DELETE CASCADE,  -- who favorites
  favoritee_id  INT REFERENCES users(user_id) ON DELETE CASCADE,  -- who is favorited
  created_at    TIMESTAMPTZ DEFAULT now(),
  updated_at    TIMESTAMPTZ DEFAULT now(),
  PRIMARY KEY (favoriter_id, favoritee_id),
  CHECK (favoriter_id <> favoritee_id)  -- prevent self-favorite
);

-- 9) Blocked (users can block others)
CREATE TABLE IF NOT EXISTS user_blocks (
  blocker_id   INT REFERENCES users(user_id) ON DELETE CASCADE,  -- who blocked
  blocked_id   INT REFERENCES users(user_id) ON DELETE CASCADE,  -- who got blocked
  action_type  VARCHAR(20) CHECK (action_type IN ('block','report')),
  reason       TEXT,                                             -- optional reason
  PRIMARY KEY (blocker_id, blocked_id),
  created_at   TIMESTAMPTZ DEFAULT now()
);

-- 10) Listener badges (daily badge assignment for next day earnings)
CREATE TABLE IF NOT EXISTS listener_badges (
  listener_id INT REFERENCES users(user_id) ON DELETE CASCADE,
  date        DATE NOT NULL,
  badge       VARCHAR(20) CHECK (badge IN ('gold','silver','bronze','basic')),
  audio_rate_per_minute NUMERIC(5,2) NOT NULL,  -- INR per minute for audio calls
  video_rate_per_minute NUMERIC(5,2) NOT NULL,  -- INR per minute for video calls
  assigned_at TIMESTAMPTZ DEFAULT now(),
  PRIMARY KEY (listener_id, date),
  updated_at    TIMESTAMPTZ DEFAULT now(),
  created_at      TIMESTAMPTZ DEFAULT now()
);

-- 11) Listener Bank Details (payout/account info only)
CREATE TABLE IF NOT EXISTS listener_payout (
  user_id         INT PRIMARY KEY REFERENCES users(user_id) ON DELETE CASCADE,
  payout_account  JSONB,        -- store bank/UPI/payout metadata encrypted at app level
  updated_at    TIMESTAMPTZ DEFAULT now(),
  created_at      TIMESTAMPTZ DEFAULT now()
);

-- 12) Listener Profile (verification, permissions, and call configuration)
CREATE TABLE IF NOT EXISTS listener_profile (
  listener_id                INT PRIMARY KEY REFERENCES users(user_id) ON DELETE CASCADE,
  verification_status        BOOLEAN DEFAULT FALSE,  -- true = verified, false = not verified
  verified_on                TIMESTAMPTZ,
  verification_message       TEXT,
  audio_file_url             TEXT,  -- S3 URL for verification audio sample
  listener_allowed_call_type TEXT[] CHECK (
                                listener_allowed_call_type <@ ARRAY['audio','video','both']
                              ) DEFAULT ARRAY['audio', 'video'],
  listener_audio_call_enable BOOLEAN DEFAULT TRUE,
  listener_video_call_enable BOOLEAN DEFAULT TRUE,
  updated_at                 TIMESTAMPTZ DEFAULT now(),
  created_at                 TIMESTAMPTZ DEFAULT now()
);

-- 13) User Rewards (generic table for referrals, streaks, etc.)
CREATE TABLE IF NOT EXISTS user_rewards (
  reward_id     SERIAL PRIMARY KEY,
  user_id       INT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,  -- who gets the reward
  reward_type   VARCHAR(50) NOT NULL 
                  CHECK (reward_type IN ('referral', 'streak', 'special_event')),
  related_user  INT REFERENCES users(user_id) ON DELETE CASCADE, -- for referral: who referred/referred, else NULL
  reward_coins  BIGINT DEFAULT 0,      -- coins rewarded
  reward_meta   JSONB,                 -- extra info (streak_days, campaign_id, etc.)
  created_at    TIMESTAMPTZ DEFAULT now(),
  updated_at    TIMESTAMPTZ DEFAULT now(),
  
  -- prevent same referrer from referring same user multiple times
  CONSTRAINT uq_unique_referral UNIQUE (user_id, related_user) 
    DEFERRABLE INITIALLY IMMEDIATE
);

-- Indexes for common filters/queries
CREATE INDEX idx_calls_user ON user_calls(user_id);
CREATE INDEX idx_calls_listener ON user_calls(listener_id);



-- DROP SCHEMA public CASCADE;
-- CREATE SCHEMA public;