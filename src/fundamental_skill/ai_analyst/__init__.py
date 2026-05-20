# -*- coding: utf-8 -*-
"""AI analyst support layer for fundamental_skill.

This package prepares evidence packs and prompts for an external AI analyst.
It does not call model APIs, alter the deterministic pipeline, connect to
accounts, or produce execution guidance.
"""

from .evidence_pack import EvidencePackBuilder
from .prompt_builder import PromptBuilder
from .report_schema import validate_ai_report
from .safety import SafetyViolation, check_text_safety

__all__ = [
    "EvidencePackBuilder",
    "PromptBuilder",
    "SafetyViolation",
    "check_text_safety",
    "validate_ai_report",
]
