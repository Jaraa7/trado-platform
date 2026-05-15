# 🚀 TRADO Platform

> **منصة تداول ذكية من 87 AI Agent يعملون 24/7 لخدمة المتداول العربي**

[![Tests](https://img.shields.io/badge/tests-37%2F37-brightgreen)]()
[![Agents](https://img.shields.io/badge/agents-87%2F87-blue)]()
[![Python](https://img.shields.io/badge/python-3.11+-yellow)]()
[![License](https://img.shields.io/badge/license-Private-red)]()

---

## 🏛️ الأقسام التسعة

| # | القسم | عدد الـ Agents | الحالة |
|---|-------|----------------|--------|
| 1 | 🟦 **Trading Intelligence** | 15 | ✅ |
| 2 | 🟩 **Engineering** | 10 | ✅ |
| 3 | 🟥 **Security** | 7 | ✅ |
| 4 | 🟫 **Financial** | 12 | ✅ |
| 5 | 🟧 **Customer Success** | 11 | ✅ |
| 6 | 🟪 **Marketing** | 12 | ✅ |
| 7 | 🎨 **Design** | 7 | ✅ |
| 8 | 🟨 **Product** | 7 | ✅ |
| 9 | ⚙️ **Operations** | 6 | ✅ |
| | **المجموع** | **87** | **🎯** |

## 🚀 البداية السريعة

```bash
# 1. Clone
git clone https://github.com/Jaraa7/trado-platform.git
cd trado-platform

# 2. Install
pip install -r requirements.txt

# 3. Configure
cp .env.example .env
# عدّل .env بمفاتيحك

# 4. Run
python main.py
```

افتح: http://localhost:8000/docs

## 📡 API Endpoints

| Endpoint | Method | الوظيفة |
|----------|--------|---------|
| `/` | GET | معلومات المنصة |
| `/agents` | GET | كل الـ 87 agent |
| `/agents/{dept}` | GET | agents قسم معين |
| `/agents/run` | POST | تشغيل agent |
| `/pipeline/run` | POST | pipeline التداول |
| `/status` | GET | حالة النظام |

## 🧪 الاختبارات

```bash
pytest tests/ -v
# 37/37 ✅
```

## 🏗️ هيكل المشروع

```
trado-platform/
├── agents/
│   ├── _shared/             # base_agent, memory, rag, factory
│   ├── trading/             # 15 trading agents
│   ├── engineering/         # 10 dev agents
│   ├── security/            # 7 security agents
│   ├── financial/           # 12 finance agents
│   ├── customer/            # 11 customer agents
│   ├── marketing/           # 12 marketing agents
│   ├── design/              # 7 design agents
│   ├── product/             # 7 product agents
│   ├── operations/          # 6 ops agents
│   └── registry.py          # ⭐ Master registry
├── orchestrator/            # المخ المركزي
├── config/                  # إعدادات
├── tests/                   # 37 tests
├── main.py                  # FastAPI app
├── Dockerfile               # Docker
├── fly.toml                 # Fly.io deployment
└── .github/workflows/       # CI/CD
```

## 🛡️ Risk Management

- ⚠️ Max **2%** risk per trade
- 🛑 Max **6%** daily loss
- 📉 Max **15%** monthly drawdown
- 🔒 Max **3x** leverage
- ✅ Min **1.5:1** R:R

## 💰 الأسعار (Tiers)

| Tier | الإشارات | السعر |
|------|----------|-------|
| 🌱 Micro | 5/يوم | $15/mo |
| 🚀 Starter | 15/يوم | $25/mo |
| 💎 Pro | 50/يوم | $50/mo |
| 👑 Elite | Unlimited | $100/mo |

## 🔐 الأمان

- ✅ OWASP Top 10 compliant
- ✅ API keys encrypted (AES-256)
- ✅ Multi-layer DDoS protection
- ✅ KYC/AML compliant (GDPR + Gulf regulations)
- ✅ Daily security audits

## 🚢 النشر

```bash
# Docker
docker build -t trado .
docker run -p 8000:8000 trado

# Fly.io
flyctl deploy
```

## 📈 الـ Roadmap

- ✅ **Week 1-2:** Foundation + 15 Trading Agents
- ✅ **Week 3-9:** كل الأقسام التسعة (87 agent)
- 🔜 **Week 10-12:** Beta + Launch

## 📞 التواصل

- 💬 Telegram: [@trado_platform](https://t.me/trado_platform)
- 🐦 Twitter: [@trado_platform](https://twitter.com/trado_platform)

---

**Built with ❤️ by the TRADO team**
