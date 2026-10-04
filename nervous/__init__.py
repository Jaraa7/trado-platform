"""
nervous — الطبقة الحسابية الحتمية للنظام العصبي في TRADO.

قاعدة التصميم (لتجنب أي تعارض مع الوكلاء الـ87 الموجودين):
- لا استدعاءات LLM هنا إطلاقًا. كل أداة حسابية، قابلة للاختبار بلا شبكة.
- الوكلاء الموجودون (market_researcher, regime_detector, performance_tuner,
  feature_prioritizer ...) يستهلكون مخرجات هذه الأدوات كأرقام موثوقة.
- كل الأسماء العامة مسبوقة بـ nervous_: الجداول، المسارات (/nervous/*)،
  متغيرات البيئة (NERVOUS_*)، مفاتيح الـ cache (nervous:*).
"""
from nervous.goals import GoalEngine, Goal
from nervous.market import MarketResearch
from nervous.performance import PerformanceTracker
from nervous.conflicts import ConflictChecker

__all__ = ["GoalEngine", "Goal", "MarketResearch", "PerformanceTracker", "ConflictChecker"]
