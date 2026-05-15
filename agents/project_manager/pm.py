"""
🎯 TRADO Project Manager — مدير مشروعك الشخصي
بقوة 30 مساعد بشري + 30 سنة خبرة
"""
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional
from agents._shared.base_agent import BaseAgent, AgentContext, AgentResponse


class TaskStatus(str, Enum):
    BACKLOG = "backlog"
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    REVIEW = "review"
    DONE = "done"
    BLOCKED = "blocked"


class Priority(str, Enum):
    P0 = "p0_critical"   # حاسم — نفّذ الآن
    P1 = "p1_high"       # مهم — هذا الأسبوع
    P2 = "p2_medium"     # متوسط — هذا الشهر
    P3 = "p3_low"        # منخفض — متى ما أمكن


@dataclass
class Task:
    id: str
    title: str
    description: str
    priority: Priority
    status: TaskStatus = TaskStatus.BACKLOG
    estimated_hours: float = 0
    actual_hours: float = 0
    blockers: list[str] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)
    assigned_to: str = ""
    deadline: Optional[str] = None
    notes: list[str] = field(default_factory=list)


@dataclass
class Risk:
    id: str
    description: str
    impact: str          # low / medium / high / critical
    probability: str     # low / medium / high
    mitigation: str
    owner: str = "PM"


@dataclass
class Milestone:
    week: int
    name: str
    deliverables: list[str]
    success_criteria: list[str]
    blockers: list[str] = field(default_factory=list)


class TRADOProjectManager(BaseAgent):
    """
    مدير المشروع الشخصي — قوة 30 مساعد + 30 سنة خبرة.

    شخصية الـ PM:
    - حازم ومنظم لكن مرن
    - استراتيجي يرى الصورة الكبيرة
    - تكتيكي يهتم بالتفاصيل
    - يكشف المخاطر قبل حدوثها
    - يحوّل الأفكار لخطط قابلة للتنفيذ
    - يتحدث بالعربية والإنجليزية بطلاقة
    """

    AGENT_ID = "trado_pm"
    AGENT_NAME = "TRADO Project Manager 🎯"
    MODEL = "claude-sonnet-4-20250514"
    MAX_TOKENS = 4000

    @property
    def system_prompt(self) -> str:
        return """أنت TRADO Project Manager، مدير المشروع الشخصي للمؤسس.

🎯 شخصيتك:
خبرتك المركّبة: 30 سنة × 30 مساعد = 900 سنة-مهارة عاملة لخدمة هذا المشروع.

عملت سابقاً في:
- Goldman Sachs (Trading Operations)
- BlackRock (Portfolio Risk)
- McKinsey (Strategy Consulting)
- Y Combinator (Startup Mentor)
- Andreessen Horowitz (Crypto Investments)
- Coinbase (Product Management)

أتقن:
✅ Agile + Scrum + Kanban
✅ OKRs + KPIs
✅ Risk Management
✅ Stakeholder Communication
✅ Resource Planning
✅ Strategic Thinking
✅ Crisis Management
✅ Vendor Negotiation
✅ Team Leadership
✅ Financial Planning

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎯 دورك مع المؤسس:

1️⃣ **الذراع التنفيذية**
   - تترجم أفكاره لخطط عمل قابلة للتنفيذ
   - تقسم المشاريع الكبيرة لمهام يومية واضحة
   - تذكّره بالأولويات

2️⃣ **المستشار الاستراتيجي**
   - ترى الصورة الكبيرة
   - تحذره من قرارات خاطئة
   - تقترح بدائل أفضل

3️⃣ **حارس الجدول الزمني**
   - تتابع كل deadline
   - تنبه قبل الـ delays
   - تعيد التخطيط عند الحاجة

4️⃣ **مدير المخاطر**
   - تكتشف المخاطر قبل حدوثها
   - تقترح خطط بديلة
   - تحمي المشروع من الفشل

5️⃣ **مدير التواصل**
   - تصيغ رسائل احترافية للمستثمرين/الشركاء
   - تترجم المتطلبات للفريق التقني
   - تعد التقارير الدورية

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📋 منهجيتك:

عند أي طلب جديد، تسأل نفسك:
1. ما الهدف الحقيقي؟ (ليس الظاهر فقط)
2. ما الأولوية؟ (P0/P1/P2/P3)
3. ما المخاطر؟
4. ما البدائل؟
5. ما الخطوة التالية الواحدة؟

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🗣️ أسلوب تواصلك:

- مباشر وواضح (لا حشو)
- يقدم القرار قبل التفسير
- يستخدم bullet points للأفكار المتعددة
- يطرح سؤالاً واحداً مركّزاً عند الحاجة
- يقدم 2-3 خيارات (لا أكثر) عند القرارات
- بالعربية الفصحى السهلة + إنجليزية تقنية
- يستخدم emojis بحساب (للوضوح فقط)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 صيغة المخرجات الافتراضية:

```
🎯 الموقف الحالي:
[فهمي للوضع - جملتان]

💡 توصيتي:
[القرار/الإجراء المقترح]

📋 الخطوات (مرتبة):
1. [خطوة 1] - [الوقت المتوقع]
2. [خطوة 2]
3. [خطوة 3]

⚠️ المخاطر التي يجب مراقبتها:
• [خطر 1]
• [خطر 2]

🔜 الخطوة التالية الواحدة:
[شيء واحد فقط للبدء به الآن]
```

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🚀 معلومات المشروع الحالية:

المشروع: TRADO Platform
الحالة: بناء مكتمل (87/87 agent)
المستودع: github.com/Jaraa7/trado-platform
الخطة: 12 أسبوع للإطلاق
المرحلة الحالية: نهاية الأسبوع 4

ما تم إنجازه:
✅ البنية التحتية كاملة
✅ 87 agent معرّفون ومسجّلون
✅ FastAPI + Docker + Fly.io
✅ 37 اختبار ناجح
✅ مرفوع على GitHub

ما لم يتم إنجازه:
🔲 تكامل APIs الحقيقية (Anthropic + Bybit)
🔲 اختبار E2E على testnet
🔲 إعداد قاعدة البيانات (Supabase)
🔲 إعداد Telegram Bot
🔲 صفحة Landing + التسويق
🔲 المدفوعات (Lemon Squeezy)
🔲 Beta testing
🔲 الإطلاق الرسمي

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

❌ ما لا تفعله أبداً:
- لا تقول "كل شيء ممكن" — كن واقعياً
- لا تخفي المخاطر
- لا تقترح > 3 خيارات في القرار الواحد
- لا تطيل بدون فائدة
- لا تنفّذ بدون أولوية واضحة
"""

    async def daily_standup(self, user_id: str = "founder") -> AgentResponse:
        """اجتماع الـ daily standup الصباحي"""
        context = AgentContext(
            user_id=user_id,
            user_message="""اجتماع صباح اليوم.

أعطني:
1. أهم 3 أولويات لليوم
2. مخاطر أو blockers أحتاج معرفتها
3. سؤال واحد محوري يحتاج قراري"""
        )
        return await self.think(context)

    async def weekly_review(self, user_id: str = "founder") -> AgentResponse:
        """مراجعة أسبوعية شاملة"""
        context = AgentContext(
            user_id=user_id,
            user_message="""المراجعة الأسبوعية.

قدم:
1. ما تحقق هذا الأسبوع (3-5 نقاط)
2. ما تأخر ولماذا
3. خطة الأسبوع القادم (أولويات + deadlines)
4. تحذير: أهم خطر يلوح في الأفق"""
        )
        return await self.think(context)

    async def make_decision(self, question: str, options: list[str] = None, user_id: str = "founder") -> AgentResponse:
        """مساعدة في اتخاذ قرار"""
        opts_text = ""
        if options:
            opts_text = "\n\nالخيارات المطروحة:\n" + "\n".join([f"  • {o}" for o in options])

        context = AgentContext(
            user_id=user_id,
            user_message=f"""قرار يحتاج مساعدتك:

{question}{opts_text}

حلل + قدم توصيتك مع المبررات + اذكر المخاطر."""
        )
        return await self.think(context)

    async def task_breakdown(self, big_task: str, user_id: str = "founder") -> AgentResponse:
        """تقسيم مهمة كبيرة لخطوات صغيرة"""
        context = AgentContext(
            user_id=user_id,
            user_message=f"""قسّم هذه المهمة لخطوات قابلة للتنفيذ:

"{big_task}"

أريد:
- 5-10 خطوات محددة (لا أكثر)
- الوقت المتوقع لكل خطوة
- ترتيب الأولوية
- الخطوة الأولى الواحدة للبدء فوراً"""
        )
        return await self.think(context)

    async def risk_assessment(self, situation: str, user_id: str = "founder") -> AgentResponse:
        """تقييم المخاطر"""
        context = AgentContext(
            user_id=user_id,
            user_message=f"""قيّم المخاطر في:

"{situation}"

أعطني:
- أهم 3 مخاطر (مرتبة بالخطورة)
- احتمالية حدوث كل منها
- التأثير المتوقع
- خطة تخفيف لكل خطر"""
        )
        return await self.think(context)


# ═════════════════════════════════════════════════════════════════════
# جلسة استشارية فورية
# ═════════════════════════════════════════════════════════════════════

class PMSession:
    """جلسة عمل مع مدير المشروع"""

    def __init__(self, user_id: str = "founder"):
        self.pm = TRADOProjectManager(user_id=user_id)
        self.user_id = user_id
        self.history = []

    async def ask(self, question: str) -> str:
        """سؤال مفتوح للـ PM"""
        context = AgentContext(
            user_id=self.user_id,
            user_message=question,
            conversation_history=self.history[-10:]  # آخر 10 رسائل
        )
        response = await self.pm.think(context)

        self.history.append({"role": "user", "content": question})
        self.history.append({"role": "assistant", "content": response.content})

        return response.content


if __name__ == "__main__":
    import asyncio

    async def demo():
        pm = TRADOProjectManager(user_id="founder")
        print("🎯 TRADO PM جاهز للعمل!")
        print(f"الـ system prompt: {len(pm.system_prompt)} حرف")
        print(f"الذاكرة: مفعّلة")
        print(f"RAG: مفعّل")
        print()
        print("جرّب: pm.daily_standup() / pm.weekly_review() / pm.make_decision(...)")

    asyncio.run(demo())
