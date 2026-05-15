"""
TRADO Agent Registry — السجل الكامل للـ 87 agent
"""
from typing import Type
from agents._shared.base_agent import BaseAgent

# ─── Trading Intelligence (15 agents) ─────────────────────────────────
from agents.trading.scanner.agent import ScannerPro
from agents.trading.analyst.agent import AnalystMaster
from agents.trading.risk_guardian.agent import RiskGuardian
from agents.trading.executioner.agent import ExecutionerPro
from agents.trading.observatory.agent import Observatory
from agents.trading.regime_detector.agent import RegimeDetector
from agents.trading.news_analyst.agent import NewsAnalyst
from agents.trading.sentiment.agent import SentimentAnalyzer
from agents.trading.whale_tracker.agent import WhaleTracker
from agents.trading.macro.agent import MacroEconomist
from agents.trading.strategy.agent import StrategyDesigner
from agents.trading.portfolio.agent import PortfolioManager
from agents.trading.pattern.agent import PatternRecognition
from agents.trading.backtester.agent import BacktesterPro
from agents.trading.arbitrage.agent import ArbitrageHunter

# ─── Other Departments ────────────────────────────────────────────────
from agents.engineering.agents import ENGINEERING_AGENTS
from agents.security.agents import SECURITY_AGENTS
from agents.financial.agents import FINANCIAL_AGENTS
from agents.customer.agents import CUSTOMER_AGENTS
from agents.marketing.agents import MARKETING_AGENTS
from agents.design.agents import DESIGN_AGENTS
from agents.product.agents import PRODUCT_AGENTS
from agents.operations.agents import OPERATIONS_AGENTS


# ═════════════════════════════════════════════════════════════════════
# المخطط الكامل للأقسام
# ═════════════════════════════════════════════════════════════════════

TRADING_AGENTS = {
    "scanner_pro": ScannerPro,
    "analyst_master": AnalystMaster,
    "risk_guardian": RiskGuardian,
    "executioner_pro": ExecutionerPro,
    "observatory": Observatory,
    "regime_detector": RegimeDetector,
    "news_analyst": NewsAnalyst,
    "sentiment_analyzer": SentimentAnalyzer,
    "whale_tracker": WhaleTracker,
    "macro_economist": MacroEconomist,
    "strategy_designer": StrategyDesigner,
    "portfolio_manager": PortfolioManager,
    "pattern_recognition": PatternRecognition,
    "backtester_pro": BacktesterPro,
    "arbitrage_hunter": ArbitrageHunter,
}


# ═════════════════════════════════════════════════════════════════════
# الـ Registry الكامل
# ═════════════════════════════════════════════════════════════════════

AGENT_REGISTRY: dict[str, dict[str, Type[BaseAgent]]] = {
    "trading":     TRADING_AGENTS,        # 15
    "engineering": ENGINEERING_AGENTS,    # 10
    "security":    SECURITY_AGENTS,       # 7
    "financial":   FINANCIAL_AGENTS,      # 12
    "customer":    CUSTOMER_AGENTS,       # 11
    "marketing":   MARKETING_AGENTS,      # 12
    "design":      DESIGN_AGENTS,         # 7
    "product":     PRODUCT_AGENTS,        # 7
    "operations":  OPERATIONS_AGENTS,     # 6
}


def get_agent(agent_id: str, user_id: str = "system") -> BaseAgent:
    """جلب agent بالاسم من أي قسم"""
    for dept_name, dept_agents in AGENT_REGISTRY.items():
        if agent_id in dept_agents:
            agent_class = dept_agents[agent_id]
            return agent_class(user_id=user_id)
    raise ValueError(f"Agent not found: {agent_id}")


def list_all_agents() -> dict:
    """قائمة بكل الـ 87 agent"""
    result = {}
    for dept, agents in AGENT_REGISTRY.items():
        result[dept] = {
            "count": len(agents),
            "agents": list(agents.keys())
        }
    result["total"] = sum(len(a) for a in AGENT_REGISTRY.values())
    return result


def get_department_count() -> dict[str, int]:
    return {dept: len(agents) for dept, agents in AGENT_REGISTRY.items()}


if __name__ == "__main__":
    counts = get_department_count()
    total = sum(counts.values())
    print(f"\n🏛️  TRADO Platform — {total} Agents Active\n")
    for dept, count in counts.items():
        print(f"  {dept:15} → {count} agents")
    print()
