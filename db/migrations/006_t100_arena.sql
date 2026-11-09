-- TRADO-100: second arena (volatile coins). Existing rows become arena='main'.
ALTER TABLE t100_managers ADD COLUMN IF NOT EXISTS arena TEXT NOT NULL DEFAULT 'main';
ALTER TABLE t100_treasury ADD COLUMN IF NOT EXISTS arena TEXT NOT NULL DEFAULT 'main';
CREATE INDEX IF NOT EXISTS idx_t100_managers_arena ON t100_managers(arena) WHERE status <> 'dead';
