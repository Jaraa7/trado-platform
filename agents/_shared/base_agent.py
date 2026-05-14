"""
TRADO Base Agent — الكلاس الأساسي لجميع الـ 87 agent
"""
import time
import asyncio
from abc import ABC, abstractmethod
from typing import Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
from loguru import logger
import anthropic

from agents._shared.memory import MemorySystem
from agents._shared.rag import RAGSystem
from config.settings import settings


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
    MODEL: str = "claude-sonnet-4-20250514"
    MAX_TOKENS: int = 2000
    KNOWLEDGE_DIR: Optional[str] = None

    # تكاليف النماذج (USD per 1M tokens)
    MODEL_COSTS = {
        "claude-sonnet-4-20250514": {"input": 3.0, "output": 15.0},
        "claude-haiku-4-5-20251001": {"input": 0.25, "output": 1.25},
    }

    def __init__(self, user_id: str = "system"):
        self.user_id = user_id
        self.memory = MemorySystem(agent_id=self.AGENT_ID, user_id=user_id)
        self.rag = RAGSystem(agent_id=self.AGENT_ID)
        self._client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
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

            # 5. الاستدعاء
            response = self._client.messages.create(
                model=self.MODEL,
                max_tokens=self.MAX_TOKENS,
                system=full_system,
                messages=messages
            )

            content = response.content[0].text
            input_tokens = response.usage.input_tokens
            output_tokens = response.usage.output_tokens
            cost = self._calculate_cost(input_tokens, output_tokens)

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
                    "model": self.MODEL
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
        costs = self.MODEL_COSTS.get(self.MODEL, {"input": 3.0, "output": 15.0})
        return (input_tokens * costs["input"] + output_tokens * costs["output"]) / 1_000_000

    @property
    def total_cost(self) -> float:
        return self._total_cost

    @property
    def call_count(self) -> int:
        return self._call_count

    def __repr__(self):
        return f"<{self.AGENT_NAME} | calls={self._call_count} | cost=${self._total_cost:.4f}>"
