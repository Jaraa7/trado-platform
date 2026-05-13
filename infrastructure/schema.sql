-- TRADO Schema
CREATE TABLE IF NOT EXISTS trades (id UUID PRIMARY KEY DEFAULT gen_random_uuid(), symbol TEXT, exchange TEXT, side TEXT, entry_price DECIMAL, exit_price DECIMAL, stop_loss DECIMAL, take_profit_1 DECIMAL, position_value DECIMAL, net_pnl DECIMAL, status TEXT DEFAULT 'open', confidence INTEGER, strategy TEXT, reason TEXT, opened_at TIMESTAMPTZ DEFAULT NOW(), closed_at TIMESTAMPTZ);

CREATE TABLE IF NOT EXISTS users (id UUID PRIMARY KEY DEFAULT gen_random_uuid(), email TEXT UNIQUE NOT NULL, plan_type TEXT DEFAULT 'free', telegram_id TEXT, created_at TIMESTAMPTZ DEFAULT NOW(), subscription_expires TIMESTAMPTZ);

CREATE TABLE IF NOT EXISTS portfolio_history (id UUID PRIMARY KEY DEFAULT gen_random_uuid(), balance DECIMAL, daily_pnl DECIMAL, daily_loss DECIMAL DEFAULT 0, weekly_loss DECIMAL DEFAULT 0, hard_stop BOOLEAN DEFAULT FALSE, recorded_at TIMESTAMPTZ DEFAULT NOW());

CREATE TABLE IF NOT EXISTS affiliate_codes (id UUID PRIMARY KEY DEFAULT gen_random_uuid(), user_id UUID REFERENCES users(id), code TEXT UNIQUE, level INTEGER DEFAULT 1, total_earned DECIMAL DEFAULT 0, pending_balance DECIMAL DEFAULT 0, created_at TIMESTAMPTZ DEFAULT NOW());

ALTER TABLE trades ENABLE ROW LEVEL SECURITY;
ALTER TABLE users ENABLE ROW LEVEL SECURITY;