"""Scope-aware, versioned structural rule inspection for USG-SEM/1.0."""
from .analyzer import PROFILE_ID, ScopeAwareRuleAnalyzer, ScopeAwareRuleError, analyze_scope

__all__ = ["PROFILE_ID", "ScopeAwareRuleAnalyzer", "ScopeAwareRuleError", "analyze_scope"]
