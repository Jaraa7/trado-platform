"""
TRADO Base Agent — الكلاس الأساسي لجميع الـ 87 agent
"""
import time
from abc import ABC, abstractmethod
from typing import Optional
from dataclasses import dataclass, field
from datetime import datetime
from loguru import logger

from agents._shared.memory import MemorySystem
from agents._shared.rag import RAGSystem


@dataclass
class AgentResponse:
    agent_id: str
    content: str
    confidence: float = 1.0
    cost_usd: float = 0.0
    tokens_used: int = 0
    processing_time_ms: float = 0.0
    metadata: dict = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    @property
    def success(self) -> bool:
        return bool(self.content)


@dataclass
class AgentContext:
    """السياق المُمرَّر للـ agent"""
    user_id: str
    user_message: str
    conversation_history: list = field(default_factory=list)
    market_data: dict = field(default_factory=dict)
    portfolio: dict = field(default_factory=dict)
    additional: dict = field(default_factory=dict)


class BaseAgent(ABC):
    """
    الكلاس الأساسي لجميع agents في TRADO.
    كل agent يرث من هنا ويحصل على:
    - Memory System (قصير + طويل + episodic)
    - RAG System (معرفة متخصصة)
    - Cost tracking
    - Error handling
    - Logging
    """

    # يجب تعريفها في كل agent
    AGENT_ID: str = "base"
    AGENT_NAME: str = "Base Agent"
    # TIER هو ما يعلنه الوكيل؛ MODEL يبقى للتوافق الخلفي فقط (يُترجم عبر config/models.py)
    TIER: str = "standard"             # frontier | standard | cheap
    MODEL: str = ""                    # فارغ = اتبع TIER
    MAX_TOKENS: int = 2000
    KNOWLEDGE_DIR: Optional[str] = None

    def __init__(self, user_id: str = "system"):
        self.user_id = user_id
        self.memory = MemorySystem(agent_id=self.AGENT_ID, user_id=user_id)
        self.rag = RAGSystem(agent_id=self.AGENT_ID)
        from core.llm_router import get_router
        self._router = get_router()
        self._total_cost = 0.0
        self._call_count = 0

        logger.info(f"🤖 {self.AGENT_NAME} initialized for user {user_id}")

    @property
    @abstractmethod
    def system_prompt(self) -> str:
        """كل agent يعرّف system prompt خاص به"""
        pass

    async def think(self, context: AgentContext) -> AgentResponse:
        """
        الوظيفة الرئيسية: يُعطى السياق ويرجع الرد.
        """
        start_time = time.time()
        self._call_count += 1

        try:
            # 1. استرجاع المعرفة ذات الصلة
            knowledge_chunks = await self.rag.retrieve(context.user_message)
            knowledge_context = self.rag.format_context(knowledge_chunks)

            # 2. استرجاع الذاكرة القصيرة
            recent_memory = await self.memory.recall("recent_context") or {}

            # 3. بناء الـ system prompt الكامل
            full_system = self.system_prompt
            if knowledge_context:
                full_system += knowledge_context
            if recent_memory:
                full_system += f"\n\n[RECENT CONTEXT]\n{recent_memory}\n[/RECENT CONTEXT]"

            # 4. بناء رسائل المحادثة
            messages = []
            for msg in context.conversation_history[-6:]:  # آخر 6 رسائل
                messages.append({"role": msg["role"], "content": msg["content"]})
            messages.append({"role": "user", "content": context.user_message})

            # 5. الاستدعاء عبر الموجّه (فئة → نموذج، مع بديل تلقائي وتسجيل تكلفة)
            result = self._router.complete(
                tier=self.TIER, system=full_system, messages=messages,
                agent_id=self.AGENT_ID, max_tokens=self.MAX_TOKENS,
                force_model=self.MODEL or None,  # توافق خلفي لوكيل يحدد نموذجًا صراحة
            )
            content = result.text
            input_tokens = result.input_tokens
            output_tokens = result.output_tokens
            cost = result.cost_usd
            used_model = result.model

            self._total_cost += cost

            # 6. تحديث الذاكرة القصيرة
            await self.memory.remember("recent_context", {
                "last_query": context.user_message,
                "last_response_summary": content[:200],
                "timestamp": datetime.utcnow().isoformat()
            }, ttl_seconds=7200)

            processing_time = (time.time() - start_time) * 1000

            logger.info(
                f"✅ {self.AGENT_NAME} | {processing_time:.0f}ms | "
                f"${cost:.4f} | {input_tokens+output_tokens} tokens"
            )

            return AgentResponse(
                agent_id=self.AGENT_ID,
                content=content,
                cost_usd=cost,
                tokens_used=input_tokens + output_tokens,
                processing_time_ms=processing_time,
                metadata={
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "model": used_model,
                    "tier": self.TIER,
                    "fallback_used": result.fallback_used,
                }
            )

        except Exception as e:
            processing_time = (time.time() - start_time) * 1000
            logger.error(f"❌ {self.AGENT_NAME} error: {e}")
            return AgentResponse(
                agent_id=self.AGENT_ID,
                content=f"عذراً، حدث خطأ: {str(e)}",
                confidence=0.0,
                processing_time_ms=processing_time
            )

    def _calculate_cost(self, input_tokens: int, output_tokens: int) -> float:
        from config.models import cost_usd, TIERS
        key = self.MODEL or TIERS[self.TIER][0]
        return cost_usd(key, input_tokens, output_tokens)

    @property
    def total_cost(self) -> float:
        return self._total_cost

    @property
    def call_count(self) -> int:
        return self._call_count

    def __repr__(self):
        return f"<{self.AGENT_NAME} | calls={self._call_count} | cost=${self._total_cost:.4f}>"
