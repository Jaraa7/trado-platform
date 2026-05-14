"""
TRADO Collaboration System — التعاون بين الـ agents
"""
from dataclasses import dataclass, field
from typing import Optional
from enum import Enum
from loguru import logger


class Priority(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class AgentRole(str, Enum):
    SCANNER = "scanner_pro"
    ANALYST = "analyst_master"
    REGIME = "regime_detector"
    RISK = "risk_guardian"
    EXECUTOR = "executioner_pro"
    OBSERVATORY = "observatory"
    NEWS = "news_analyst"
    SENTIMENT = "sentiment_analyzer"
    WHALE = "whale_tracker"
    MACRO = "macro_economist"
    STRATEGY = "strategy_designer"
    PORTFOLIO = "portfolio_manager"
    PATTERN = "pattern_recognition"
    ARBITRAGE = "arbitrage_hunter"
    BACKTESTER = "backtester_pro"
    ORCHESTRATOR = "orchestrator"


@dataclass
class AgentMessage:
    """رسالة من agent إلى آخر"""
    sender: str
    receiver: str
    content: str
    priority: Priority = Priority.MEDIUM
    requires_response: bool = False
    metadata: dict = field(default_factory=dict)


@dataclass
class ConsultRequest:
    """طلب استشارة من agent آخر"""
    requesting_agent: str
    target_agent: str
    question: str
    context: dict = field(default_factory=dict)
    blocking: bool = True  # هل ينتظر الجواب؟


@dataclass
class VetoDecision:
    """قرار الـ veto من Risk Guardian"""
    vetoed_by: str = "risk_guardian"
    reason: str = ""
    blocked_action: str = ""
    alternative_suggestion: str = ""


class CollaborationRules:
    """
    قواعد التعاون بين الـ agents
    مَن يستشير مَن، ومتى
    """

    # خريطة الاستشارات الإلزامية
    MUST_CONSULT = {
        AgentRole.EXECUTOR: [AgentRole.RISK],          # Executioner يجب يسأل Risk
        AgentRole.STRATEGY: [AgentRole.REGIME, AgentRole.RISK],  # Strategy يسأل Regime + Risk
        AgentRole.PORTFOLIO: [AgentRole.RISK],         # Portfolio يسأل Risk
        AgentRole.ANALYST: [AgentRole.PATTERN, AgentRole.REGIME],  # Analyst يسأل Pattern + Regime
    }

    # من يملك حق الـ Veto
    VETO_AGENTS = [AgentRole.RISK]

    # حدود الاستقلالية (يقرر لوحده بدون استشارة)
    AUTONOMOUS_THRESHOLD = {
        AgentRole.SCANNER: 0.8,     # ثقة 80%+ = يرسل بدون استشارة
        AgentRole.NEWS: 0.9,
        AgentRole.WHALE: 0.85,
        AgentRole.SENTIMENT: 0.75,
    }

    @staticmethod
    def should_consult(agent_id: str, action: str, confidence: float) -> list[str]:
        """هل يجب استشارة agents أخرى؟"""
        role = AgentRole(agent_id) if agent_id in AgentRole._value2member_map_ else None
        if not role:
            return []

        required = CollaborationRules.MUST_CONSULT.get(role, [])

        # تحقق من حد الاستقلالية
        threshold = CollaborationRules.AUTONOMOUS_THRESHOLD.get(role, 0.7)
        if confidence >= threshold and not required:
            return []

        return [r.value for r in required]

    @staticmethod
    def can_veto(agent_id: str) -> bool:
        """هل يملك هذا الـ agent حق الـ veto؟"""
        try:
            return AgentRole(agent_id) in CollaborationRules.VETO_AGENTS
        except ValueError:
            return False
