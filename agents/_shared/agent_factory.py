"""
TRADO Agent Factory
مصنع الـ agents — يولّد agents من تعريفات مختصرة
"""
from typing import Type, Optional
from agents._shared.base_agent import BaseAgent, AgentContext, AgentResponse


def create_agent_class(
    agent_id: str,
    agent_name: str,
    role_description: str,
    expertise: str,
    output_format: str,
    skills: list[str],
    model: str = "claude-sonnet-4-5",
    max_tokens: int = 2000,
    knowledge_dir: Optional[str] = None,
) -> Type[BaseAgent]:
    """
    صانع الـ agents — يولّد class كامل من المعطيات
    """

    skills_text = "\n".join([f"  {i+1}. {s}" for i, s in enumerate(skills)])

    full_system_prompt = f"""{role_description}

🎓 الخبرة:
{expertise}

🛠️ المهارات الـ 20:
{skills_text}

📋 صيغة المخرجات:
{output_format}

قواعدك:
- الدقة قبل السرعة
- البيانات قبل الآراء
- الأمان قبل الربح
- التوثيق قبل التنفيذ
"""

    class GeneratedAgent(BaseAgent):
        AGENT_ID = agent_id
        AGENT_NAME = agent_name
        MODEL = model
        MAX_TOKENS = max_tokens
        KNOWLEDGE_DIR = knowledge_dir

        @property
        def system_prompt(self) -> str:
            return full_system_prompt

        async def execute(self, task: str, context_data: dict = None, user_id: str = "system") -> AgentResponse:
            context = AgentContext(
                user_id=user_id,
                user_message=task,
                additional=context_data or {}
            )
            return await self.think(context)

    GeneratedAgent.__name__ = "".join(w.capitalize() for w in agent_id.split("_"))
    return GeneratedAgent
