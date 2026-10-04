"""
nervous/conflicts.py — فاحص التعارض بين الأدوات.

يفحص المستودع فعليًا (لا افتراضات) ويرفع تقريرًا بأي اصطدام في:
1. معرّفات الوكلاء (AGENT_ID مكرر عبر الأقسام)
2. مسارات HTTP (نفس method+path معرّف مرتين)
3. أسماء الجداول (migration يعرّف جدولًا موجودًا)
4. مفاتيح الـ cache (أداة في nervous تستخدم مفتاحًا غير مسبوق بـ nervous:)
5. متغيرات البيئة الجديدة بلا بادئة NERVOUS_
6. التحقق أن nervous/ لا يستورد anthropic (قاعدة: بلا LLM هنا)

يُستدعى من tests/test_nervous.py فيفشل CI عند أي تعارض.
"""
from __future__ import annotations

import re
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
NERVOUS_ENV_PREFIX = "NERVOUS_"


class ConflictChecker:
    def __init__(self, root: Path = ROOT):
        self.root = root
        self.issues: list[str] = []

    # 1 ───────────────────────────────────────────────────────────────
    def check_agent_ids(self):
        """
        مصدر الحقيقة هو AGENT_REGISTRY نفسه (يلتقط الوكلاء المولَّدين في حلقات).
        تعارض = معرّف مكرر عبر الأقسام، أو مفتاح سجل لا يطابق AGENT_ID الخاص بالصنف.
        """
        ids = Counter()
        try:
            from agents.registry import AGENT_REGISTRY
        except Exception as ex:  # بيئة بلا تبعيات → مسح نصي احتياطي
            self.issues.append(f"تعذر استيراد السجل ({ex}); سقط إلى المسح النصي")
            return self._scan_agent_ids_text()
        for dept, agents in AGENT_REGISTRY.items():
            for key, cls in agents.items():
                ids[key] += 1
                real = getattr(cls, "AGENT_ID", None)
                if real and real != key:
                    self.issues.append(f"مفتاح السجل '{key}' في {dept} لا يطابق AGENT_ID='{real}'")
        for k, n in ids.items():
            if n > 1:
                self.issues.append(f"agent_id مكرر {n} مرات: {k}")
        return ids

    def _scan_agent_ids_text(self) -> Counter:
        ids = Counter()
        pats = [re.compile(r'AGENT_ID\s*(?::\s*str)?\s*=\s*["\']([a-z0-9_]+)["\']'),
                re.compile(r'create_agent_class\(\s*(?:agent_id\s*=\s*)?["\']([a-z0-9_]+)["\']')]
        for f in (self.root / "agents").rglob("*.py"):
            if f.name == "agent_factory.py":
                continue
            txt = f.read_text(encoding="utf-8")
            for pat in pats:
                for m in pat.finditer(txt):
                    ids[m.group(1)] += 1
        for k, n in ids.items():
            if n > 1:
                self.issues.append(f"agent_id مكرر {n} مرات: {k}")
        return ids

    # 2 ───────────────────────────────────────────────────────────────
    def check_routes(self):
        routes = defaultdict(list)
        pat = re.compile(r'@(?:app|router)\.(get|post|put|delete|patch)\(\s*["\']([^"\']+)["\']')
        prefix_pat = re.compile(r'APIRouter\([^)]*prefix\s*=\s*["\']([^"\']+)["\']')
        for f in self.root.rglob("*.py"):
            if any(p in f.parts for p in (".git", "tests", "node_modules", "scripts")):
                continue
            # api/main.py تطبيق منفصل (ازدواجية معروفة) — لا يُحسب تعارضًا مع main.py
            if f.relative_to(self.root).as_posix() == "api/main.py":
                continue
            txt = f.read_text(encoding="utf-8")
            pm = prefix_pat.search(txt)
            prefix = pm.group(1) if pm else ""
            for m in pat.finditer(txt):
                routes[(m.group(1).upper(), prefix + m.group(2))].append(f.relative_to(self.root).as_posix())
        for (method, path), files in routes.items():
            if len(files) > 1:
                self.issues.append(f"مسار مكرر {method} {path}: {files}")
        return routes

    # 3 ───────────────────────────────────────────────────────────────
    def check_tables(self):
        tables = defaultdict(list)
        for f in sorted((self.root / "db" / "migrations").glob("*.sql")):
            for m in re.finditer(r'CREATE TABLE(?: IF NOT EXISTS)?\s+([a-z_]+)', f.read_text(encoding="utf-8"), re.I):
                tables[m.group(1).lower()].append(f.name)
        for t, files in tables.items():
            if len(files) > 1:
                self.issues.append(f"جدول معرّف في أكثر من migration: {t} {files}")
        return tables

    # 4 + 5 + 6 ───────────────────────────────────────────────────────
    def check_nervous_isolation(self):
        for f in (self.root / "nervous").glob("*.py"):
            txt = f.read_text(encoding="utf-8")
            if re.search(r'^\s*(import anthropic|from anthropic)', txt, re.M):
                self.issues.append(f"{f.name}: nervous/ لا يستدعي LLM مباشرة")
            for m in re.finditer(r'Cache\.make_key\(\s*["\']([^"\']+)', txt):
                if not m.group(1).startswith("nervous"):
                    self.issues.append(f"{f.name}: مفتاح cache بلا بادئة nervous: {m.group(1)}")
            # متغيرات المنصة الموجودة في .env.example مسموح قراءتها؛ أي متغير جديد يجب أن يبدأ بـ NERVOUS_
            known = self._known_env_keys()
            for m in re.finditer(r'os\.getenv\(\s*["\']([A-Z_]+)["\']', txt):
                k = m.group(1)
                if not k.startswith(NERVOUS_ENV_PREFIX) and k not in known:
                    self.issues.append(f"{f.name}: متغير بيئة جديد بلا بادئة NERVOUS_: {k}")

    # 7 ───────────────────────────────────────────────────────────────
    def check_governance_untouched_by_agents(self):
        """لا ملف في nervous/ أو agents/ يفتح ملفًا داخل governance/ للكتابة."""
        pat = re.compile(r'(open|write_text|write_bytes)\(\s*[^)]*governance/[^)]*["\'](w|a|wb)["\']')
        for d in ("nervous", "agents"):
            for f in (self.root / d).rglob("*.py"):
                if f.name == "conflicts.py":
                    continue
                if pat.search(f.read_text(encoding="utf-8")):
                    self.issues.append(f"{f.relative_to(self.root)}: يحاول الكتابة في governance/")

    def _known_env_keys(self) -> set[str]:
        env = self.root / ".env.example"
        if not env.exists():
            return {"APP_ENV"}
        return {ln.split("=", 1)[0].strip() for ln in env.read_text(encoding="utf-8").splitlines()
                if "=" in ln and not ln.lstrip().startswith("#")} | {"APP_ENV"}

    def run(self) -> dict:
        self.issues = []
        self.check_governance_untouched_by_agents()
        agents = self.check_agent_ids()
        routes = self.check_routes()
        tables = self.check_tables()
        self.check_nervous_isolation()
        return {"ok": not self.issues, "issues": self.issues,
                "counts": {"agents": len(agents), "routes": len(routes), "tables": len(tables)}}
