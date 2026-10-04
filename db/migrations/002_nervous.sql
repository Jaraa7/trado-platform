-- ════════════════════════════════════════════════════════════════════
-- 002 — جداول الطبقة العصبية (كلها مسبوقة بـ nervous_ لتجنب التعارض)
-- ════════════════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS nervous_goals (
    id          VARCHAR(64) PRIMARY KEY,
    title       TEXT NOT NULL,
    impact      NUMERIC(4,1) NOT NULL CHECK (impact BETWEEN 1 AND 10),
    urgency     NUMERIC(4,1) NOT NULL CHECK (urgency BETWEEN 1 AND 10),
    effort      NUMERIC(4,1) NOT NULL CHECK (effort BETWEEN 1 AND 10),
    confidence  NUMERIC(4,1) NOT NULL DEFAULT 7,
    metric      VARCHAR(32),
    depends_on  TEXT[] DEFAULT '{}',
    status      VARCHAR(16) DEFAULT 'open',
    notes       TEXT,
    created_at  TIMESTAMPTZ DEFAULT NOW(),
    updated_at  TIMESTAMPTZ DEFAULT NOW()
);

-- كل قرار يتخذه النظام: قبل التنفيذ، ثم نتيجته لاحقًا
CREATE TABLE IF NOT EXISTS nervous_decisions (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    actor           VARCHAR(64) NOT NULL,        -- الوكيل أو الأداة
    level           SMALLINT NOT NULL CHECK (level IN (0,1,2)),
    action          VARCHAR(64) NOT NULL,
    target          VARCHAR(128),
    reason          TEXT,
    evidence        JSONB,                       -- الأرقام التي استند إليها
    status          VARCHAR(16) DEFAULT 'proposed', -- proposed|approved|rejected|executed|reverted|expired
    approved_by     VARCHAR(64),
    executed_at     TIMESTAMPTZ,
    outcome_24h     JSONB,
    outcome_7d      JSONB,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_nervous_decisions_status ON nervous_decisions(status);
CREATE INDEX IF NOT EXISTS idx_nervous_decisions_created ON nervous_decisions(created_at DESC);

-- نتائج الإشارات (تكمّل جدول signals دون تعديله)
CREATE TABLE IF NOT EXISTS nervous_signal_outcomes (
    signal_id    UUID PRIMARY KEY REFERENCES signals(id) ON DELETE CASCADE,
    status       VARCHAR(16) NOT NULL,           -- hit_tp|hit_sl|expired|active
    r_multiple   NUMERIC(8,3) NOT NULL DEFAULT 0,
    bars         INTEGER NOT NULL DEFAULT 0,
    evaluated_at TIMESTAMPTZ DEFAULT NOW()
);

-- لقطات المقاييس الحاكمة
CREATE TABLE IF NOT EXISTS nervous_metrics (
    id          BIGSERIAL PRIMARY KEY,
    name        VARCHAR(64) NOT NULL,            -- profit_per_user | retention | prod_errors | ai_cost_usd ...
    value       NUMERIC(18,6) NOT NULL,
    dims        JSONB DEFAULT '{}',
    ts          TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_nervous_metrics_name_ts ON nervous_metrics(name, ts DESC);
