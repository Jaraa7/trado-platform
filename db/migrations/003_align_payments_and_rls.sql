-- ════════════════════════════════════════════════════════════════════
-- 003 — مواءمة المخطط مع كود الدفع + إغلاق جداول مكشوفة
-- إضافات فقط؛ لا حذف ولا تعديل لبيانات قائمة.
-- ════════════════════════════════════════════════════════════════════

-- كود Tap يحفظ معرّف الاشتراك هنا ويعتمد عليه لفحص الملكية وتجنّب التكرار
ALTER TABLE subscriptions ADD COLUMN IF NOT EXISTS tap_subscription_id VARCHAR(100);
CREATE UNIQUE INDEX IF NOT EXISTS idx_subs_tap_id ON subscriptions(tap_subscription_id);

-- waitlist (بريد العملاء) وaudit_logs كانا بلا RLS → مقروءان بالمفتاح العام.
-- الخادم يستخدم service role فيتجاوز RLS؛ بلا سياسات = لا وصول عام.
ALTER TABLE waitlist ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_logs ENABLE ROW LEVEL SECURITY;
