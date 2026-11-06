-- TRADO-100: six tables for the evolutionary manager system.
-- Prefixed t100_ because public.trades already exists (SaaS user trades).
-- RLS is enabled with NO policies: only the service role (worker) can access.

CREATE TABLE IF NOT EXISTS t100_managers (
    id             BIGSERIAL PRIMARY KEY,
    family         TEXT        NOT NULL,
    variant        INT         NOT NULL DEFAULT 0,
    generation     INT         NOT NULL DEFAULT 1,
    parent_id      BIGINT      REFERENCES t100_managers(id),
    status         TEXT        NOT NULL DEFAULT 'alive'
                   CHECK (status IN ('born','alive','frozen','watch','dead')),
    stage          TEXT        NOT NULL DEFAULT 'A'
                   CHECK (stage IN ('A','B','C','D','E')),
    genome         JSONB       NOT NULL DEFAULT '{}'::jsonb,
    universe       JSONB       NOT NULL DEFAULT '[]'::jsonb,
    risk_profile   JSONB       NOT NULL DEFAULT '{}'::jsonb,
    brain          JSONB       NOT NULL DEFAULT '{}'::jsonb,
    start_balance  NUMERIC(18,4) NOT NULL DEFAULT 1000,
    balance        NUMERIC(18,4) NOT NULL DEFAULT 1000,
    peak_balance   NUMERIC(18,4) NOT NULL DEFAULT 1000,
    frozen_until   TIMESTAMPTZ,
    born_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
    died_at        TIMESTAMPTZ,
    last_trade_at  TIMESTAMPTZ
);
CREATE INDEX IF NOT EXISTS idx_t100_managers_status ON t100_managers(status);
CREATE INDEX IF NOT EXISTS idx_t100_managers_family ON t100_managers(family) WHERE status <> 'dead';

CREATE TABLE IF NOT EXISTS t100_trades (
    id           BIGSERIAL PRIMARY KEY,
    manager_id   BIGINT      NOT NULL REFERENCES t100_managers(id),
    symbol       TEXT        NOT NULL,
    side         TEXT        NOT NULL CHECK (side IN ('long','short')),
    mode         TEXT        NOT NULL DEFAULT 'paper' CHECK (mode IN ('paper','real')),
    leverage     NUMERIC(6,2) NOT NULL DEFAULT 1,
    entry_price  NUMERIC(24,8) NOT NULL,
    exit_price   NUMERIC(24,8),
    qty          NUMERIC(28,10) NOT NULL,
    stop_price   NUMERIC(24,8),
    target_price NUMERIC(24,8),
    fees         NUMERIC(18,6) NOT NULL DEFAULT 0,
    pnl          NUMERIC(18,6),
    reason_in    TEXT,
    reason_out   TEXT,
    opened_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    closed_at    TIMESTAMPTZ
);
CREATE INDEX IF NOT EXISTS idx_t100_trades_manager ON t100_trades(manager_id, opened_at DESC);
CREATE INDEX IF NOT EXISTS idx_t100_trades_open ON t100_trades(manager_id) WHERE closed_at IS NULL;

CREATE TABLE IF NOT EXISTS t100_deaths (
    id             BIGSERIAL PRIMARY KEY,
    manager_id     BIGINT      NOT NULL REFERENCES t100_managers(id),
    cause          TEXT        NOT NULL,
    final_balance  NUMERIC(18,4),
    max_drawdown   NUMERIC(8,4),
    trades_count   INT,
    post_mortem    TEXT,
    heir_id        BIGINT      REFERENCES t100_managers(id),
    died_at        TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS t100_lessons (
    id           BIGSERIAL PRIMARY KEY,
    family       TEXT        NOT NULL,
    lesson       TEXT        NOT NULL,
    source_death BIGINT      REFERENCES t100_deaths(id),
    confirmations INT        NOT NULL DEFAULT 1,
    active       BOOLEAN     NOT NULL DEFAULT false,  -- true after 2 consecutive weekly post-mortems agree
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    retired_at   TIMESTAMPTZ
);
CREATE INDEX IF NOT EXISTS idx_t100_lessons_family ON t100_lessons(family) WHERE active;

CREATE TABLE IF NOT EXISTS t100_regime_stats (
    id          BIGSERIAL PRIMARY KEY,
    family      TEXT        NOT NULL,
    regime      TEXT        NOT NULL,
    trades      INT         NOT NULL DEFAULT 0,
    wins        INT         NOT NULL DEFAULT 0,
    pnl         NUMERIC(18,4) NOT NULL DEFAULT 0,
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (family, regime)
);

CREATE TABLE IF NOT EXISTS t100_treasury (
    id            BIGSERIAL PRIMARY KEY,
    ts            TIMESTAMPTZ NOT NULL DEFAULT now(),
    mode          TEXT        NOT NULL DEFAULT 'paper' CHECK (mode IN ('paper','real')),
    equity        NUMERIC(18,4) NOT NULL,
    peak_equity   NUMERIC(18,4) NOT NULL,
    drawdown      NUMERIC(8,4) NOT NULL DEFAULT 0,
    kill_switch   BOOLEAN     NOT NULL DEFAULT false,
    note          TEXT
);
CREATE INDEX IF NOT EXISTS idx_t100_treasury_ts ON t100_treasury(ts DESC);

ALTER TABLE t100_managers     ENABLE ROW LEVEL SECURITY;
ALTER TABLE t100_trades       ENABLE ROW LEVEL SECURITY;
ALTER TABLE t100_deaths       ENABLE ROW LEVEL SECURITY;
ALTER TABLE t100_lessons      ENABLE ROW LEVEL SECURITY;
ALTER TABLE t100_regime_stats ENABLE ROW LEVEL SECURITY;
ALTER TABLE t100_treasury     ENABLE ROW LEVEL SECURITY;
