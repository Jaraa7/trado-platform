-- ════════════════════════════════════════════════════════════════════
-- 🏛️ TRADO Platform — Database Schema v1.0
-- Supabase PostgreSQL + Row Level Security
-- ════════════════════════════════════════════════════════════════════

-- Extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ════════════════════════════════════════════════════════════════════
-- 1. USERS — المستخدمون
-- ════════════════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS users (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    auth_id         UUID UNIQUE,                                     -- Supabase auth.users.id
    email           VARCHAR(255) UNIQUE NOT NULL,
    full_name       VARCHAR(255),
    phone           VARCHAR(20),
    country_code    VARCHAR(2),                                       -- KW, SA, AE, etc.
    language        VARCHAR(5) DEFAULT 'ar',                          -- ar, en
    timezone        VARCHAR(50) DEFAULT 'Asia/Kuwait',
    
    -- Status
    status          VARCHAR(20) DEFAULT 'active',                     -- active, suspended, deleted
    email_verified  BOOLEAN DEFAULT FALSE,
    kyc_status      VARCHAR(20) DEFAULT 'pending',                    -- pending, verified, rejected
    
    -- Trading profile
    risk_profile    VARCHAR(20) DEFAULT 'moderate',                   -- conservative, moderate, aggressive
    trading_experience VARCHAR(20),                                   -- beginner, intermediate, expert
    portfolio_size_range VARCHAR(50),                                 -- "500-5000", "10000-100000", etc.
    
    -- Telegram integration
    telegram_chat_id BIGINT UNIQUE,
    telegram_username VARCHAR(100),
    
    -- Referral
    referral_code   VARCHAR(20) UNIQUE,
    referred_by     UUID REFERENCES users(id),
    
    -- Timestamps
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW(),
    last_active_at  TIMESTAMPTZ,
    deleted_at      TIMESTAMPTZ
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_auth_id ON users(auth_id);
CREATE INDEX idx_users_telegram ON users(telegram_chat_id);
CREATE INDEX idx_users_referral ON users(referral_code);

-- ════════════════════════════════════════════════════════════════════
-- 2. SUBSCRIPTIONS — الاشتراكات
-- ════════════════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS subscriptions (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Tier
    tier            VARCHAR(20) NOT NULL,                             -- trial, micro, starter, pro, elite, whale, institutional, founder, enterprise
    billing_cycle   VARCHAR(10) DEFAULT 'monthly',                    -- monthly, annual
    
    -- Status
    status          VARCHAR(20) DEFAULT 'active',                     -- active, paused, cancelled, expired, grace
    auto_renew      BOOLEAN DEFAULT TRUE,
    
    -- Pricing
    amount          DECIMAL(10,2) NOT NULL,
    currency        VARCHAR(3) DEFAULT 'USD',
    discount_pct    DECIMAL(5,2) DEFAULT 0,
    
    -- Lemon Squeezy
    ls_subscription_id VARCHAR(100) UNIQUE,
    ls_customer_id  VARCHAR(100),
    ls_variant_id   VARCHAR(100),
    
    -- Dates
    started_at      TIMESTAMPTZ DEFAULT NOW(),
    current_period_start TIMESTAMPTZ,
    current_period_end   TIMESTAMPTZ,
    cancelled_at    TIMESTAMPTZ,
    
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_subs_user ON subscriptions(user_id);
CREATE INDEX idx_subs_status ON subscriptions(status);
CREATE INDEX idx_subs_renewal ON subscriptions(current_period_end);

-- ════════════════════════════════════════════════════════════════════
-- 3. EXCHANGE_ACCOUNTS — حسابات المنصات
-- ════════════════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS exchange_accounts (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    exchange        VARCHAR(20) NOT NULL,                             -- bybit, binance, okx, kucoin, mexc
    account_label   VARCHAR(100),                                     -- "Main", "Long-term"
    is_testnet      BOOLEAN DEFAULT FALSE,
    
    -- Encrypted API credentials (using pgcrypto)
    api_key_encrypted   TEXT NOT NULL,                                -- AES encrypted
    api_secret_encrypted TEXT NOT NULL,
    passphrase_encrypted TEXT,                                        -- for OKX
    
    -- Status
    status          VARCHAR(20) DEFAULT 'active',                     -- active, disabled, expired
    last_verified_at TIMESTAMPTZ,
    
    -- Permissions
    can_read        BOOLEAN DEFAULT TRUE,
    can_trade       BOOLEAN DEFAULT FALSE,
    can_withdraw    BOOLEAN DEFAULT FALSE,                            -- NEVER true unless explicit
    
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW(),
    
    UNIQUE(user_id, exchange, account_label)
);

CREATE INDEX idx_exchange_user ON exchange_accounts(user_id);

-- ════════════════════════════════════════════════════════════════════
-- 4. SIGNALS — الإشارات
-- ════════════════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS signals (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Signal data
    symbol          VARCHAR(20) NOT NULL,                             -- BTC/USDT
    direction       VARCHAR(10) NOT NULL,                             -- long, short
    entry_price     DECIMAL(20,8) NOT NULL,
    stop_loss       DECIMAL(20,8) NOT NULL,
    take_profit_1   DECIMAL(20,8),
    take_profit_2   DECIMAL(20,8),
    take_profit_3   DECIMAL(20,8),
    
    -- Risk
    risk_reward     DECIMAL(5,2),
    confidence      INTEGER,                                          -- 0-100
    suggested_leverage INTEGER DEFAULT 1,
    
    -- AI metadata
    generated_by    VARCHAR(50),                                      -- agent_id who generated this
    ai_analysis     TEXT,                                             -- full AI reasoning
    ai_tokens_used  INTEGER,
    ai_cost_usd     DECIMAL(10,6),
    
    -- Multi-timeframe context
    trend_weekly    VARCHAR(20),
    trend_daily     VARCHAR(20),
    trend_h4        VARCHAR(20),
    
    -- Status
    status          VARCHAR(20) DEFAULT 'active',                     -- active, expired, hit_tp, hit_sl, manual_close
    expires_at      TIMESTAMPTZ,
    triggered_at    TIMESTAMPTZ,
    
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_signals_symbol ON signals(symbol);
CREATE INDEX idx_signals_status ON signals(status);
CREATE INDEX idx_signals_created ON signals(created_at DESC);

-- ════════════════════════════════════════════════════════════════════
-- 5. TRADES — الصفقات المنفذة
-- ════════════════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS trades (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id         UUID NOT NULL REFERENCES users(id),
    signal_id       UUID REFERENCES signals(id),
    exchange_account_id UUID REFERENCES exchange_accounts(id),
    
    -- Trade details
    symbol          VARCHAR(20) NOT NULL,
    direction       VARCHAR(10) NOT NULL,
    entry_price     DECIMAL(20,8) NOT NULL,
    exit_price      DECIMAL(20,8),
    
    quantity        DECIMAL(20,8) NOT NULL,
    notional_value  DECIMAL(20,2) NOT NULL,                           -- in USDT
    leverage        INTEGER DEFAULT 1,
    
    -- Risk management
    stop_loss       DECIMAL(20,8),
    take_profit     DECIMAL(20,8),
    
    -- Performance
    pnl_usd         DECIMAL(20,2),
    pnl_pct         DECIMAL(8,4),
    fees_usd        DECIMAL(10,4) DEFAULT 0,
    
    -- Exchange data
    exchange_order_id VARCHAR(100),
    exchange_trade_id VARCHAR(100),
    
    -- Status
    status          VARCHAR(20) DEFAULT 'open',                       -- open, closed, cancelled, liquidated
    opened_at       TIMESTAMPTZ DEFAULT NOW(),
    closed_at       TIMESTAMPTZ,
    
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_trades_user ON trades(user_id);
CREATE INDEX idx_trades_status ON trades(status);
CREATE INDEX idx_trades_opened ON trades(opened_at DESC);

-- ════════════════════════════════════════════════════════════════════
-- 6. PAYMENTS — المدفوعات
-- ════════════════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS payments (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id         UUID NOT NULL REFERENCES users(id),
    subscription_id UUID REFERENCES subscriptions(id),
    
    amount          DECIMAL(10,2) NOT NULL,
    currency        VARCHAR(3) DEFAULT 'USD',
    
    -- Tax
    subtotal        DECIMAL(10,2) NOT NULL,
    tax_amount      DECIMAL(10,2) DEFAULT 0,
    tax_rate        DECIMAL(5,4) DEFAULT 0,
    
    -- Provider
    provider        VARCHAR(20),                                      -- lemon_squeezy, stripe, knet, crypto
    provider_payment_id VARCHAR(100) UNIQUE,
    provider_invoice_url TEXT,
    
    -- Status
    status          VARCHAR(20) DEFAULT 'pending',                    -- pending, succeeded, failed, refunded
    failure_reason  TEXT,
    
    paid_at         TIMESTAMPTZ,
    refunded_at     TIMESTAMPTZ,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_payments_user ON payments(user_id);
CREATE INDEX idx_payments_status ON payments(status);
CREATE INDEX idx_payments_paid ON payments(paid_at DESC);

-- ════════════════════════════════════════════════════════════════════
-- 7. NOTIFICATIONS — الإشعارات
-- ════════════════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS notifications (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    type            VARCHAR(50) NOT NULL,                             -- signal, trade, payment, alert, system
    title           VARCHAR(200) NOT NULL,
    body            TEXT,
    data            JSONB,                                            -- additional context
    
    -- Channels
    sent_email      BOOLEAN DEFAULT FALSE,
    sent_telegram   BOOLEAN DEFAULT FALSE,
    sent_push       BOOLEAN DEFAULT FALSE,
    
    -- Status
    read            BOOLEAN DEFAULT FALSE,
    read_at         TIMESTAMPTZ,
    
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_notifs_user_unread ON notifications(user_id, read) WHERE read = FALSE;
CREATE INDEX idx_notifs_created ON notifications(created_at DESC);

-- ════════════════════════════════════════════════════════════════════
-- 8. USER_SETTINGS — إعدادات المستخدم
-- ════════════════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS user_settings (
    user_id         UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    
    -- Trading preferences
    max_risk_per_trade  DECIMAL(5,4) DEFAULT 0.02,                    -- 2%
    max_daily_loss      DECIMAL(5,4) DEFAULT 0.06,                    -- 6%
    max_leverage        INTEGER DEFAULT 3,
    min_risk_reward     DECIMAL(3,2) DEFAULT 1.5,
    max_concurrent_trades INTEGER DEFAULT 5,
    
    -- Watched pairs
    watched_pairs       TEXT[],                                       -- ["BTC/USDT", "ETH/USDT"]
    blacklisted_pairs   TEXT[],
    
    -- Notifications
    notify_signals      BOOLEAN DEFAULT TRUE,
    notify_trades       BOOLEAN DEFAULT TRUE,
    notify_news         BOOLEAN DEFAULT TRUE,
    notify_payments     BOOLEAN DEFAULT TRUE,
    
    notification_channel VARCHAR(20) DEFAULT 'telegram',              -- telegram, email, both
    quiet_hours_start   TIME,
    quiet_hours_end     TIME,
    
    -- Auto-trading
    auto_execute_enabled BOOLEAN DEFAULT FALSE,
    auto_execute_min_confidence INTEGER DEFAULT 75,
    
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ════════════════════════════════════════════════════════════════════
-- 9. AGENT_USAGE — استخدام الـ agents (للـ billing/limits)
-- ════════════════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS agent_usage (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    agent_id        VARCHAR(50) NOT NULL,                             -- analyst_master, etc.
    tokens_used     INTEGER NOT NULL,
    cost_usd        DECIMAL(10,6) NOT NULL,
    model           VARCHAR(50),                                      -- claude-sonnet-4-5
    
    -- Context
    triggered_by    VARCHAR(50),                                      -- user_request, scheduled, webhook
    cached          BOOLEAN DEFAULT FALSE,
    duration_ms     INTEGER,
    
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_usage_user_date ON agent_usage(user_id, created_at DESC);
CREATE INDEX idx_usage_cost ON agent_usage(cost_usd) WHERE cost_usd > 0;

-- ════════════════════════════════════════════════════════════════════
-- 10. AUDIT_LOGS — سجل المراجعة (للأمان والامتثال)
-- ════════════════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS audit_logs (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id         UUID REFERENCES users(id),
    
    action          VARCHAR(100) NOT NULL,                            -- login, trade_executed, settings_changed, etc.
    resource_type   VARCHAR(50),                                      -- user, trade, subscription
    resource_id     UUID,
    
    -- Details
    ip_address      INET,
    user_agent      TEXT,
    metadata        JSONB,
    
    -- Compliance
    pii_accessed    BOOLEAN DEFAULT FALSE,                            -- did this action involve PII?
    
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_audit_user ON audit_logs(user_id, created_at DESC);
CREATE INDEX idx_audit_action ON audit_logs(action);

-- ════════════════════════════════════════════════════════════════════
-- 11. WAITLIST — قائمة الانتظار قبل الإطلاق
-- ════════════════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS waitlist (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email           VARCHAR(255) UNIQUE NOT NULL,
    full_name       VARCHAR(255),
    country_code    VARCHAR(2),
    
    interested_tier VARCHAR(20),
    portfolio_size  VARCHAR(50),
    referral_source VARCHAR(100),
    
    invited         BOOLEAN DEFAULT FALSE,
    invited_at      TIMESTAMPTZ,
    converted       BOOLEAN DEFAULT FALSE,
    converted_at    TIMESTAMPTZ,
    
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_waitlist_email ON waitlist(email);
CREATE INDEX idx_waitlist_invited ON waitlist(invited);

-- ════════════════════════════════════════════════════════════════════
-- Row Level Security (RLS) — يمنع المستخدم من رؤية بيانات غيره
-- ════════════════════════════════════════════════════════════════════
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE subscriptions ENABLE ROW LEVEL SECURITY;
ALTER TABLE exchange_accounts ENABLE ROW LEVEL SECURITY;
ALTER TABLE trades ENABLE ROW LEVEL SECURITY;
ALTER TABLE payments ENABLE ROW LEVEL SECURITY;
ALTER TABLE notifications ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_settings ENABLE ROW LEVEL SECURITY;
ALTER TABLE agent_usage ENABLE ROW LEVEL SECURITY;

-- Users can only see their own data
CREATE POLICY users_self ON users
    FOR ALL USING (auth.uid() = auth_id);

CREATE POLICY subs_self ON subscriptions
    FOR ALL USING (user_id IN (SELECT id FROM users WHERE auth_id = auth.uid()));

CREATE POLICY exchange_self ON exchange_accounts
    FOR ALL USING (user_id IN (SELECT id FROM users WHERE auth_id = auth.uid()));

CREATE POLICY trades_self ON trades
    FOR SELECT USING (user_id IN (SELECT id FROM users WHERE auth_id = auth.uid()));

CREATE POLICY payments_self ON payments
    FOR SELECT USING (user_id IN (SELECT id FROM users WHERE auth_id = auth.uid()));

CREATE POLICY notifs_self ON notifications
    FOR ALL USING (user_id IN (SELECT id FROM users WHERE auth_id = auth.uid()));

CREATE POLICY settings_self ON user_settings
    FOR ALL USING (user_id IN (SELECT id FROM users WHERE auth_id = auth.uid()));

CREATE POLICY usage_self ON agent_usage
    FOR SELECT USING (user_id IN (SELECT id FROM users WHERE auth_id = auth.uid()));

-- Signals are public (visible to all authenticated users)
ALTER TABLE signals ENABLE ROW LEVEL SECURITY;
CREATE POLICY signals_public ON signals
    FOR SELECT USING (auth.role() = 'authenticated');

-- ════════════════════════════════════════════════════════════════════
-- Triggers — تحديث تلقائي للـ updated_at
-- ════════════════════════════════════════════════════════════════════
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER users_updated BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();
CREATE TRIGGER subs_updated BEFORE UPDATE ON subscriptions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();
CREATE TRIGGER exchange_updated BEFORE UPDATE ON exchange_accounts
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();
CREATE TRIGGER trades_updated BEFORE UPDATE ON trades
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- ════════════════════════════════════════════════════════════════════
-- Helpful Views
-- ════════════════════════════════════════════════════════════════════

-- Active subscriptions with user info
CREATE OR REPLACE VIEW active_subscribers AS
SELECT
    u.id, u.email, u.full_name, u.country_code,
    s.tier, s.amount, s.current_period_end,
    s.created_at as subscribed_at
FROM users u
JOIN subscriptions s ON s.user_id = u.id
WHERE s.status = 'active' AND u.status = 'active';

-- User stats summary
CREATE OR REPLACE VIEW user_stats AS
SELECT
    u.id, u.email,
    COUNT(DISTINCT t.id) as total_trades,
    COUNT(DISTINCT t.id) FILTER (WHERE t.status = 'closed' AND t.pnl_usd > 0) as winning_trades,
    SUM(t.pnl_usd) as total_pnl,
    SUM(t.fees_usd) as total_fees,
    MAX(t.opened_at) as last_trade_at
FROM users u
LEFT JOIN trades t ON t.user_id = u.id
GROUP BY u.id, u.email;

-- ════════════════════════════════════════════════════════════════════
-- ✅ END OF SCHEMA — 11 tables + RLS + Triggers + Views
-- ════════════════════════════════════════════════════════════════════
