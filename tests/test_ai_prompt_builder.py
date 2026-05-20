# -*- coding: utf-8 -*-

from src.fundamental_skill.ai_analyst.evidence_pack import EvidencePackBuilder
from src.fundamental_skill.ai_analyst.prompt_builder import PromptBuilder

from tests.ai_test_fixtures import sample_fundamental, sample_raw


def test_prompt_builder_generates_prompt_with_required_limits():
    pack = EvidencePackBuilder().build(sample_fundamental(), sample_raw())
    prompt = PromptBuilder().build(pack)

    assert "不得编造 evidence pack 没有的数据" in prompt
    assert "缺失数据不足以判断" in prompt
    assert "fundamental_ai_report.v1" in prompt
    assert "enhanced_must_track_indicators" in prompt
    assert "Markdown 报告中使用表格" in prompt
    assert "display_value" in prompt
    assert "analyst_summary" in prompt
    assert "trader_summary" not in prompt
    assert "action_hint_for_trader" not in prompt
    assert "交易员 Agent" not in prompt


def test_prompt_policy_terms_are_allowed_only_as_policy_context():
    pack = EvidencePackBuilder().build(sample_fundamental(), sample_raw())
    prompt = PromptBuilder().build(pack)
    safety = PromptBuilder().safety_summary(prompt)

    assert safety["safe"] is True
    assert safety["blocked_count"] == 0
