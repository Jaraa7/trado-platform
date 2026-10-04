# Freqtrade — محرك الاختبار التاريخي (لا للتنفيذ)

يعمل عبر صورة Docker الرسمية، منفصلًا عن تطبيق TRADO. التنفيذ والمخاطر والحوكمة تبقى في TRADO.

```bash
cd freqtrade
# 1) سحب 3 سنوات شموع 1h/4h لـ25 زوجًا من Bybit (مرة واحدة، ~10 دقائق)
docker compose run --rm freqtrade download-data --exchange bybit \
  --pairs-file user_data/pairs.json --timeframes 1h 4h --days 1095

# 2) اختبار استراتيجية (walk-forward: ضبط 2023–2024، تحقق 2025–2026)
docker compose run --rm freqtrade backtesting --strategy TradoTrendV1 \
  --timeframe 1h --timerange 20250101-  --export trades

# 3) النتيجة → scripts/import_backtest.py يحولها إلى صيغة nervous/performance
```

قواعد (من governance/limits.py): المعاملات تُجمَّد قبل paper؛ أقصى 30 صيغة؛ ما ينجح
على بيانات لم يرها فقط ينتقل إلى paper.
