-- TRADO-100: daily AI reviewer output + LLM spend counter.
-- RLS enabled with NO policies: service role (worker) only.

CREATE TABLE IF NOT EXISTS t100_reviews (
    id          BIGSERIAL PRIMARY KEY,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    trigger     TEXT        NOT NULL DEFAULT 'daily' CHECK (trigger IN ('daily','death','manual')),
    model       TEXT,
    summary     TEXT        NOT NULL,
    findings    JSONB       NOT NULL DEFAULT '[]'::jsonb,
    snapshot    JSONB       NOT NULL DEFAULT '{}'::jsonb,
    issue_urls  JSONB       NOT NULL DEFAULT '[]'::jsonb
);
CREATE INDEX IF NOT EXISTS idx_t100_reviews_created ON t100_reviews(created_at DESC);

CREATE TABLE IF NOT EXISTS t100_llm_costs (
    id            BIGSERIAL PRIMARY KEY,
    ts            TIMESTAMPTZ NOT NULL DEFAULT now(),
    agent         TEXT        NOT NULL,
    model         TEXT        NOT NULL,
    input_tokens  INT         NOT NULL DEFAULT 0,
    output_tokens INT         NOT NULL DEFAULT 0,
    cost_usd      NUMERIC(12,6) NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_t100_llm_costs_ts ON t100_llm_costs(ts DESC);

ALTER TABLE t100_reviews   ENABLE ROW LEVEL SECURITY;
ALTER TABLE t100_llm_costs ENABLE ROW LEVEL SECURITY;
