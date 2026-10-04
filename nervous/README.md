# nervous/ — الطبقة الحسابية للنظام العصبي

| الأداة | ماذا تفعل | من يستهلكها |
|---|---|---|
| `goals.py` — GoalEngine | ترتيب الأهداف: الأهم / المهم / لاحقًا بدرجة WSJF مع احترام التبعيات | أنت + feature_prioritizer |
| `market.py` — MarketResearch | نظام السوق (ADX/EMA/ATR)، التقلب، المحركات، الاتساع، وضعية الاستراتيجيات | regime_detector, market_researcher, scanner_pro |
| `performance.py` — PerformanceTracker | نتيجة كل إشارة (TP/SL/R)، إحصاءات لكل وكيل ورمز، توصيات مصنفة بدرجة الصلاحية 0/1/2 | performance_tuner, risk_guardian |
| `conflicts.py` — ConflictChecker | يفحص الوكلاء/المسارات/الجداول/العزل ويفشل CI عند أي تعارض | tests/test_nervous.py |

## القواعد
- بلا LLM داخل `nervous/` — أرقام حتمية قابلة للاختبار بلا شبكة.
- كل اسم عام مسبوق بـ `nervous_` / `/nervous/` / `NERVOUS_` / `nervous:`.
- `data_ok=false` في أي مخرج = لا تبنِ قرارًا عليه.

## الاستخدام السريع
```python
from nervous import GoalEngine, Goal
e = GoalEngine(); e.add(Goal("staging","بيئة staging",impact=8,urgency=7,effort=2)); e.save()
print(e.report())

from nervous import PerformanceTracker
PerformanceTracker.from_supabase(days=30).report()
```
## API (تتطلب JWT)
`GET/POST /nervous/goals` · `PATCH /nervous/goals/{id}/status` · `GET /nervous/market/brief` · `GET /nervous/performance` · `GET /nervous/conflicts`

## قاعدة البيانات
شغّل `db/migrations/002_nervous.sql` في Supabase SQL editor.
