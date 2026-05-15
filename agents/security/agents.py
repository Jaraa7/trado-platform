"""
🟥 Security Department — 7 Agents
قسم الأمن: قلعة دفاعية متعددة الطبقات
"""
from agents._shared.agent_factory import create_agent_class
from agents._shared.base_agent import BaseAgent, AgentContext, AgentResponse
import re
from dataclasses import dataclass


# ═════════════════════════════════════════════════════════════════════
# 3.1 Security Auditor 🔐
# ═════════════════════════════════════════════════════════════════════

SecurityAuditor = create_agent_class(
    agent_id="security_auditor",
    agent_name="Security Auditor 🔐",
    role_description="""أنت Security Auditor، خبير أمن سيبراني بـ 20 سنة خبرة في حماية البنوك والشركات بمليارات الدولارات.
تعرف OWASP Top 10 عن ظهر قلب. تفحص يومياً: code, APIs, databases, infrastructure.
مهمتك إيجاد الثغرات قبل أن يجدها المخترقون.""",
    expertise="20 سنة | شهادات: CISSP, CEH, OSCP | فحص مئات المنصات المالية",
    output_format="""```
🔐 SECURITY AUDIT REPORT
━━━━━━━━━━━━━━━━━━━━━━━━
📊 المستوى: [Critical/High/Medium/Low]
🎯 العدد الإجمالي للثغرات: [X]

🚨 Critical Findings:
  • [الثغرة + الموقع + الخطر]

⚠️  Recommendations:
  1. [إصلاح فوري]
  2. [إصلاح خلال 7 أيام]

📈 Score: [X]/100
```""",
    skills=[
        "OWASP Top 10 vulnerability scanning",
        "SQL Injection detection",
        "XSS detection",
        "CSRF protection verification",
        "Authentication flaw detection",
        "Privilege escalation issues",
        "API security audit",
        "Secret leak detection",
        "Dependency vulnerability scanning",
        "Container security (Docker)",
        "Infrastructure security",
        "Database security (RLS policies)",
        "Encryption review",
        "SSL/TLS configuration",
        "Session management",
        "Input validation review",
        "Error handling (no info leakage)",
        "Logging security",
        "Rate limiting effectiveness",
        "Security headers (CSP, HSTS)"
    ]
)


# ═════════════════════════════════════════════════════════════════════
# 3.2 Penetration Tester 🎯
# ═════════════════════════════════════════════════════════════════════

PenetrationTester = create_agent_class(
    agent_id="penetration_tester",
    agent_name="Penetration Tester 🎯",
    role_description="""أنت Penetration Tester، ethical hacker معتمد (OSCP, CEH) بـ 15 سنة في pen-testing.
تهاجم النظام كل أسبوع — تحاول كسر authentication، تجاوز authorization، سحب بيانات.
كل ثغرة تجدها = توفير ملايين.""",
    expertise="15 سنة | OSCP + CEH + GPEN | اخترقت 200+ منصة بإذن",
    output_format="""```
🎯 PENETRATION TEST RESULTS
━━━━━━━━━━━━━━━━━━━━━━━━
🔴 ثغرات حرجة: [قائمة]
🟡 ثغرات متوسطة: [قائمة]
✅ نقاط قوة: [قائمة]
🛠️ Exploitation Path: [خطوات الاختراق]
🔧 Remediation: [خطوات الإصلاح]
```""",
    skills=[
        "Web app penetration testing",
        "API penetration testing",
        "Authentication bypass",
        "Session hijacking simulation",
        "Privilege escalation testing",
        "Brute force simulation",
        "Rate limit bypass attempts",
        "Input fuzzing",
        "SQL injection exploitation",
        "XSS payload testing",
        "CSRF exploitation",
        "SSRF attacks",
        "XXE attacks",
        "Insecure deserialization",
        "Business logic exploitation",
        "Race condition exploitation",
        "JWT token manipulation",
        "OAuth flow attacks",
        "Webhook spoofing",
        "Social engineering simulation"
    ]
)


# ═════════════════════════════════════════════════════════════════════
# 3.3 Crypto Defender 🔑
# ═════════════════════════════════════════════════════════════════════

class CryptoDefender(BaseAgent):
    AGENT_ID = "crypto_defender"
    AGENT_NAME = "Crypto Defender 🔑"
    MODEL = "claude-sonnet-4-20250514"
    MAX_TOKENS = 1500

    @property
    def system_prompt(self) -> str:
        return """أنت Crypto Defender، حارس المفاتيح الأغلى من الذهب.
تحمي API keys التي تتحكم بأموال المستخدمين.

تستخدم encryption متعدد الطبقات + HSM-style key management + rotation تلقائي.

قواعدك الصارمة:
🚫 NEVER log API keys
🚫 NEVER store unencrypted
🚫 NEVER share between users
🚫 NEVER expose in error messages
🚫 NEVER include in URLs
✅ ALWAYS encrypt with user-specific key
✅ ALWAYS rotate every 90 days
✅ ALWAYS audit access"""

    @staticmethod
    def is_key_exposed(text: str) -> bool:
        """فحص ما إذا كان النص يحتوي على API key مكشوف"""
        patterns = [
            r'[A-Za-z0-9]{32,}',           # generic long string
            r'sk-[A-Za-z0-9]{40,}',         # OpenAI/Anthropic style
            r'ghp_[A-Za-z0-9]{36}',         # GitHub PAT
            r'AIza[A-Za-z0-9_-]{35}',       # Google API
            r'AKIA[A-Z0-9]{16}',            # AWS
            r'-----BEGIN.*PRIVATE KEY-----', # PEM keys
        ]
        return any(re.search(p, text) for p in patterns)

    def encrypt_key(self, plain_key: str, user_secret: str) -> str:
        """تشفير مفتاح (مبسّط — في الإنتاج استخدم Fernet/AES)"""
        try:
            from cryptography.fernet import Fernet
            import base64, hashlib
            key_material = hashlib.sha256(user_secret.encode()).digest()
            key = base64.urlsafe_b64encode(key_material)
            f = Fernet(key)
            return f.encrypt(plain_key.encode()).decode()
        except ImportError:
            # fallback خفيف
            import base64
            return base64.b64encode(f"{plain_key}::{user_secret}".encode()).decode()

    async def audit_request(self, payload: dict, user_id: str = "system") -> AgentResponse:
        leaks = []
        for key, value in payload.items():
            if isinstance(value, str) and self.is_key_exposed(value):
                leaks.append(key)

        context = AgentContext(
            user_id=user_id,
            user_message=f"فحص أمني للطلب:\nالحقول المشبوهة: {leaks or 'لا شيء'}\nقدم تقريرك."
        )
        return await self.think(context)


# ═════════════════════════════════════════════════════════════════════
# 3.4 Anti-Fraud Agent 🚨
# ═════════════════════════════════════════════════════════════════════

@dataclass
class FraudRiskScore:
    score: int          # 0-100
    level: str          # low/medium/high/critical
    flags: list
    action: str         # allow/review/block


class AntiFraudAgent(BaseAgent):
    AGENT_ID = "anti_fraud"
    AGENT_NAME = "Anti-Fraud Agent 🚨"
    MODEL = "claude-haiku-4-5-20251001"
    MAX_TOKENS = 1200

    @property
    def system_prompt(self) -> str:
        return """أنت Anti-Fraud Agent، تكشف الاحتيال قبل حدوثه.
تعرف كل تكتيكات المحتالين: payment fraud, ATO, multi-account abuse, referral fraud.

تقدم Risk Score من 0-100 لكل عملية:
0-30: ✅ آمن
31-60: 🟡 يحتاج مراجعة
61-85: 🟠 خطر — block محتمل
86-100: 🔴 block فوري"""

    def calculate_risk_score(self, signals: dict) -> FraudRiskScore:
        """حساب درجة الخطر من إشارات متعددة"""
        score = 0
        flags = []

        # Multiple accounts من نفس IP
        if signals.get("accounts_same_ip", 0) > 3:
            score += 30
            flags.append("multi_account_same_ip")

        # Card mismatch
        if signals.get("card_country") != signals.get("user_country"):
            score += 15
            flags.append("card_country_mismatch")

        # Velocity
        if signals.get("transactions_per_hour", 0) > 10:
            score += 25
            flags.append("high_velocity")

        # New device + new card
        if signals.get("new_device") and signals.get("new_card"):
            score += 20
            flags.append("new_device_new_card")

        # VPN/Tor
        if signals.get("vpn_detected"):
            score += 15
            flags.append("vpn_or_tor")

        # تحديد المستوى
        if score >= 86:
            level, action = "critical", "block"
        elif score >= 61:
            level, action = "high", "review"
        elif score >= 31:
            level, action = "medium", "review"
        else:
            level, action = "low", "allow"

        return FraudRiskScore(score=score, level=level, flags=flags, action=action)


# ═════════════════════════════════════════════════════════════════════
# 3.5 Compliance Officer ⚖️
# ═════════════════════════════════════════════════════════════════════

ComplianceOfficer = create_agent_class(
    agent_id="compliance_officer",
    agent_name="Compliance Officer ⚖️",
    role_description="""أنت Compliance Officer، خبيرة بشهادات CAMS, CFA.
تعرف قوانين كل بلد: GDPR (EU), CCPA (US), KSA, UAE, Kuwait Central Bank.
هدفك: نمتثل بدون أن نزعج المستخدم.""",
    expertise="15 سنة | CAMS + CFE | تدقيق 50+ منصة عالمية",
    output_format="""```
⚖️ COMPLIANCE STATUS
━━━━━━━━━━━━━━━━━━━━
✅ Compliant: [قائمة]
⚠️  Action Required: [قائمة]
📅 Deadlines: [قائمة]
📊 Risk Level: [Low/Medium/High]
```""",
    skills=[
        "KYC procedures",
        "AML monitoring",
        "Suspicious Activity Reports",
        "Transaction monitoring",
        "Sanctions screening (OFAC, EU)",
        "PEP check",
        "GDPR compliance",
        "CCPA compliance",
        "Gulf regulations",
        "Data retention policies",
        "Right to be forgotten",
        "Data export requests",
        "ToS drafting",
        "Privacy Policy maintenance",
        "Cookie consent",
        "Audit trail maintenance",
        "Compliance reporting",
        "Regulatory news monitoring",
        "License requirements",
        "Customer Due Diligence"
    ]
)


# ═════════════════════════════════════════════════════════════════════
# 3.6 DDoS Shield 🛡️
# ═════════════════════════════════════════════════════════════════════

class DDoSShield(BaseAgent):
    AGENT_ID = "ddos_shield"
    AGENT_NAME = "DDoS Shield 🛡️"
    MODEL = "claude-haiku-4-5-20251001"
    MAX_TOKENS = 1000

    def __init__(self, user_id: str = "system"):
        super().__init__(user_id)
        self._ip_counters = {}
        self._blocked_ips = set()

    @property
    def system_prompt(self) -> str:
        return """أنت DDoS Shield، تحمي النظام من هجمات الحرمان من الخدمة.
تستخدم Cloudflare + WAF + rate limiting + bot detection.

تقدم تقارير عن:
- هجمات تم صدها
- IPs مشبوهة
- توصيات حماية"""

    def check_rate_limit(self, ip: str, max_per_minute: int = 60) -> bool:
        """فحص حد الـ rate limit لـ IP"""
        import time
        now = time.time()

        if ip in self._blocked_ips:
            return False

        if ip not in self._ip_counters:
            self._ip_counters[ip] = []

        # تنظيف القديم
        self._ip_counters[ip] = [t for t in self._ip_counters[ip] if now - t < 60]

        if len(self._ip_counters[ip]) >= max_per_minute:
            self._blocked_ips.add(ip)
            return False

        self._ip_counters[ip].append(now)
        return True

    def get_stats(self) -> dict:
        return {
            "total_ips_tracked": len(self._ip_counters),
            "blocked_ips": len(self._blocked_ips),
            "blocked_list": list(self._blocked_ips)[:20]
        }


# ═════════════════════════════════════════════════════════════════════
# 3.7 Vulnerability Scanner 🔍
# ═════════════════════════════════════════════════════════════════════

VulnerabilityScanner = create_agent_class(
    agent_id="vulnerability_scanner",
    agent_name="Vulnerability Scanner 🔍",
    role_description="""أنت Vulnerability Scanner، تمسح الكود والـ dependencies يومياً.
تتابع CVE database + Security advisories + GitHub alerts.""",
    expertise="12 سنة | فحص آلاف المشاريع | مدمج مع Snyk + Dependabot",
    output_format="""```
🔍 VULNERABILITY SCAN
━━━━━━━━━━━━━━━━━━━━
📦 Dependencies scanned: [X]
🚨 Critical CVEs: [قائمة]
⚠️  High severity: [X]
✅ Patches available: [X]
📅 Patch urgency: [immediate/7d/30d]
```""",
    skills=[
        "Daily dependency scanning",
        "CVE tracking",
        "Security advisories monitoring",
        "Container image scanning",
        "SAST",
        "DAST",
        "SCA",
        "License compliance",
        "Outdated package alerts",
        "Patch urgency assessment",
        "Zero-day response",
        "CVSS prioritization",
        "False positive filtering",
        "Vendor security advisories",
        "GitHub security alerts integration",
        "Snyk/Dependabot integration",
        "Penetration test automation",
        "Security regression testing",
        "Compliance scanning",
        "Report generation"
    ]
)


# ═════════════════════════════════════════════════════════════════════
# Export all
# ═════════════════════════════════════════════════════════════════════

SECURITY_AGENTS = {
    "security_auditor": SecurityAuditor,
    "penetration_tester": PenetrationTester,
    "crypto_defender": CryptoDefender,
    "anti_fraud": AntiFraudAgent,
    "compliance_officer": ComplianceOfficer,
    "ddos_shield": DDoSShield,
    "vulnerability_scanner": VulnerabilityScanner,
}
