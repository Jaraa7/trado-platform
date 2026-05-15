# 🚀 تشغيل TRADO على جهازك

> دليل تشغيل سريع — من 0 إلى أول صفقة testnet في 10 دقائق

---

## ⚡ التشغيل السريع (Quickstart)

### 1️⃣ تجهيز البيئة

```bash
# نزّل المشروع
git clone https://github.com/Jaraa7/trado-platform.git
cd trado-platform

# Python virtualenv (اختياري لكن منصوح)
python3 -m venv venv
source venv/bin/activate     # على macOS/Linux
# venv\Scripts\activate       # على Windows

# تثبيت المتطلبات
pip install -r requirements.txt
```

### 2️⃣ إعداد المفاتيح

```bash
# نسخ ملف البيئة
cp .env.example .env

# عدّل .env وأضف مفاتيحك:
# ANTHROPIC_API_KEY=sk-ant-...
# BYBIT_API_KEY=...
# BYBIT_SECRET=...
# BYBIT_TESTNET=true
```

### 3️⃣ تشغيل الـ Pipeline

```bash
python scripts/test_live_pipeline.py
```

سترى:
- ✅ اتصال بـ Bybit Testnet
- 💰 رصيدك ($10,000 USDT وهمية)
- 📊 سعر BTC الحالي + بيانات السوق
- 🤖 تحليل AI من Analyst Master
- 🛡️ قرار Risk Guardian
- ⚡ خيار تنفيذ صفقة testnet حقيقية

---

## 🧪 ما تتوقع تراه:

```
╔════════════════════════════════════════════════════════════════════╗
║  🚀 TRADO Platform — Live Testnet Pipeline                        ║
║  2026-05-15 17:35:42                                              ║
╚════════════════════════════════════════════════════════════════════╝

═══════════════════════════════════════════════════════════════════════
  🧪 الخطوة 1: اختبار الاتصال بـ Bybit Testnet
═══════════════════════════════════════════════════════════════════════
  ✅ الاتصال نجح!
  💰 رصيد USDT متاح: $10,000.00
  💰 إجمالي USDT:    $10,000.00

═══════════════════════════════════════════════════════════════════════
  📊 الخطوة 2: جلب بيانات السوق
═══════════════════════════════════════════════════════════════════════
  💰 BTC/USDT: $65,432.10
  📊 تغيير 24h: +2.45%
  📈 نسبة الحجم: 1.85x المتوسط

═══════════════════════════════════════════════════════════════════════
  🤖 الخطوة 3: تحليل AI (Analyst Master)
═══════════════════════════════════════════════════════════════════════
  ✅ التحليل نجح!
  💰 التكلفة: $0.025
  ⏱️  الوقت: 12500ms

  📝 ملخص التحليل:
  📊 TECHNICAL ANALYSIS — BTC/USDT
  📈 TREND: Bullish
  ⚡ STRENGTH: 7/10
  ...

═══════════════════════════════════════════════════════════════════════
  🛡️ الخطوة 4: فحص Risk Guardian
═══════════════════════════════════════════════════════════════════════
  📊 الاقتراح:
     Entry: $65,432.10
     SL:    $63,469.14 (-3%)
     TP:    $69,357.79 (+6%)

  🔍 القرار: ✅ APPROVED
     💵 الحجم: $3,000.00
     📊 % من رأس المال: 30.0%
     📉 الخسارة المحتملة: 0.92%
     🎯 R:R: 2.0

  ⚠️  هل تريد تنفيذ صفقة testnet حقيقية؟
  اكتب 'yes' للتنفيذ:
```

---

## 🔍 إذا واجهت مشاكل:

### مشكلة: `ModuleNotFoundError`
```bash
pip install -r requirements.txt --upgrade
```

### مشكلة: `Bybit Connection Error`
- تأكد من `BYBIT_TESTNET=true` في `.env`
- تأكد من المفاتيح صحيحة
- جرّب: `curl https://api-testnet.bybit.com/v5/market/time`

### مشكلة: `Anthropic API Error`
- تأكد من الـ key يبدأ بـ `sk-ant-api03-`
- تحقق من رصيد API: https://console.anthropic.com/settings/billing

---

## 🎯 الخطوة التالية:

بعد نجاح أول صفقة testnet، نتقدم لـ:
1. ✅ Telegram bot للإشعارات
2. ✅ Dashboard للمتابعة الـ real-time
3. ✅ Caching layer (تقليل التكلفة 60%+)
4. ✅ Multi-exchange (Binance + OKX)
5. ✅ Backtester على بيانات حقيقية

---

📞 **مشكلة؟** فتح issue على GitHub: 
https://github.com/Jaraa7/trado-platform/issues
