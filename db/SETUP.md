# 🏛️ TRADO Database Setup

## الخطوات (10 دقائق):

### 1. افتح Supabase Dashboard
🔗 https://supabase.com/dashboard

### 2. اختر مشروعك: `mmuupwishkejogasopez`

### 3. اذهب إلى SQL Editor
في الشريط الأيسر: **SQL Editor** → **New Query**

### 4. انسخ كل محتوى الملف:
`db/migrations/001_initial_schema.sql`

والصقه في SQL Editor.

### 5. اضغط **Run** (أو Cmd+Enter)

⏳ سيأخذ 5-10 ثوانٍ.

### 6. تحقق من النجاح:
- يجب أن ترى: **Success. No rows returned**
- اذهب لـ **Table Editor** في الشريط الأيسر
- ستجد 11 جدول جديد:

```
✅ users
✅ subscriptions
✅ exchange_accounts
✅ signals
✅ trades
✅ payments
✅ notifications
✅ user_settings
✅ agent_usage
✅ audit_logs
✅ waitlist
```

---

## 7. اختبر الاتصال محلياً:

```bash
cd ~/trado-platform
python3 -c "
from db.client import get_supabase
sb = get_supabase()
print('✅ Supabase متصل بنجاح')
print('Tables:', sb.table('users').select('*', count='exact').limit(0).execute().count, 'users')
"
```

---

## 8. أضف Encryption Secret لـ Fly.io:

```bash
# توليد secret عشوائي
SECRET=$(openssl rand -base64 32)
echo "Your encryption secret: $SECRET"

# أضفه لـ Fly
flyctl secrets set ENCRYPTION_SECRET="$SECRET" -a trado-bot
```

---

## ✅ بعد إكمال هذه الخطوات:

أعطني rebort: 
- هل ظهرت الجداول الـ 11؟
- هل نجح اختبار الاتصال؟

ثم ننتقل للخطوة التالية: **Authentication + Landing Page**.
