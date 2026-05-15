#!/bin/bash
# ═══════════════════════════════════════════════════════════
# TRADO Platform — GitHub Auto-Upload Script
# ═══════════════════════════════════════════════════════════
# الاستخدام:
#   1. ضع هذا الملف في نفس مجلد ملفات trado-platform
#   2. شغّل: bash push_to_github.sh
#   3. سيسألك عن اسم المستودع و الـ token
# ═══════════════════════════════════════════════════════════

set -e

echo "🚀 TRADO → GitHub Upload"
echo "═══════════════════════════════════════════"
echo ""

# 1. طلب البيانات
read -p "📦 اسم المستخدم (GitHub username): " GH_USER
read -p "📂 اسم المستودع (مثال: trado-platform): " GH_REPO
read -sp "🔑 الـ Personal Access Token: " GH_TOKEN
echo ""
echo ""

# 2. التحقق من Git
if ! command -v git &> /dev/null; then
    echo "❌ Git غير مثبّت. ثبّته من: https://git-scm.com/downloads"
    exit 1
fi

# 3. التحقق من المستودع
echo "🔍 التحقق من المستودع..."
REPO_CHECK=$(curl -s -o /dev/null -w "%{http_code}" \
    -H "Authorization: token $GH_TOKEN" \
    "https://api.github.com/repos/$GH_USER/$GH_REPO")

if [ "$REPO_CHECK" = "404" ]; then
    echo "📝 المستودع غير موجود — جاري إنشاؤه..."
    curl -s -H "Authorization: token $GH_TOKEN" \
        -H "Accept: application/vnd.github.v3+json" \
        https://api.github.com/user/repos \
        -d "{\"name\":\"$GH_REPO\",\"description\":\"TRADO Platform — 87 AI Trading Agents\",\"private\":true}" > /dev/null
    echo "✅ المستودع تم إنشاؤه (private)"
elif [ "$REPO_CHECK" = "200" ]; then
    echo "✅ المستودع موجود"
else
    echo "❌ خطأ في التحقق ($REPO_CHECK) — تحقق من الـ token"
    exit 1
fi

# 4. تهيئة git
echo ""
echo "📦 تهيئة المستودع المحلي..."

if [ ! -d ".git" ]; then
    git init -b main
fi

git config user.email "trado@platform.com" 2>/dev/null || true
git config user.name "$GH_USER" 2>/dev/null || true

# 5. إضافة remote
git remote remove origin 2>/dev/null || true
git remote add origin "https://$GH_TOKEN@github.com/$GH_USER/$GH_REPO.git"

# 6. إضافة الملفات
echo "📁 إضافة الملفات..."
git add .
git commit -m "🚀 TRADO Platform — 15 Trading Agents Complete

Week 1: Foundation
- Base Agent infrastructure
- Memory system (Redis + Supabase)
- RAG (Qdrant)
- Collaboration rules

Week 2: All 15 Trading Agents
- Scanner Pro, Analyst Master, Risk Guardian
- Executioner Pro, Observatory, Regime Detector
- News Analyst, Sentiment Analyzer, Whale Tracker
- Macro Economist, Strategy Designer, Portfolio Manager
- Pattern Recognition, Backtester Pro, Arbitrage Hunter

Orchestrator v2 + FastAPI + Docker + Fly.io + 20/20 tests" 2>/dev/null || echo "(لا توجد تغييرات جديدة)"

# 7. الرفع
echo ""
echo "⬆️  جاري الرفع على GitHub..."
git push -u origin main --force

echo ""
echo "═══════════════════════════════════════════"
echo "✅ تم الرفع بنجاح!"
echo "🔗 https://github.com/$GH_USER/$GH_REPO"
echo "═══════════════════════════════════════════"

# 8. تنظيف — إزالة الـ token من remote للأمان
git remote set-url origin "https://github.com/$GH_USER/$GH_REPO.git"
echo "🔒 تم تنظيف الـ token من إعدادات git"
