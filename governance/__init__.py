"""
governance/ — الحدود الصلبة للنظام العصبي.

قاعدة: لا وكيل ولا أداة تكتب في هذا المجلد. تغييره = commit موقّع من المالك.
وكيل التطوير الليلي ممنوع من لمسه (يُفرض في nervous/conflicts).
"""
from governance.limits import LIMITS
from governance.killswitch import KillSwitch
from governance.budget import AIBudget

__all__ = ["LIMITS", "KillSwitch", "AIBudget"]
