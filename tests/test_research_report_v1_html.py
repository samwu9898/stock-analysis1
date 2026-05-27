# -*- coding: utf-8 -*-

import copy
import inspect
import re

import pytest

from src.fundamental_skill.research_report.research_report_v1 import (
    ResearchReportArtifactBoundaryError,
    ResearchReportBuildError,
    ResearchReportSecretError,
)
from src.fundamental_skill.research_report.research_report_v1_html import (
    HTML_OUTPUT_FILENAME,
    render_research_report_v1_html,
    write_research_report_v1_html,
)
import src.fundamental_skill.research_report.research_report_v1_html as html_module


FORBIDDEN_RENDERED_TERMS = (
    "买入",
    "卖出",
    "持有建议",
    "目标价",
    "仓位",
    "加仓",
    "减仓",
    "止损",
    "技术面交易信号",
    "确定性上涨",
    "必然兑现",
    "强烈推荐",
)


def _sample_markdown(
    code: str = "600406",
    company: str = "国电南瑞",
    opportunity: str = "电网设备 / 数字电网 / 电力自动化",
) -> str:
    return f"""# {code} {company} 基本面研究报告 V1

## 重要声明
- 本报告仅用于基本面研究展示，不构成账户操作依据。
- 所有判断必须服从 evidence label、数据质量说明和证据缺口。

## 一句话结论
{company} 当前更适合作为 {opportunity} 的证据约束型研究样本。

## 投研速读
- 核心机会：{opportunity} 需要公司层面的订单、收入、利润和现金流证据。
- 核心风险：如果行业线索无法传导到公司经营数据，结论强度应保持克制。
- 最大证据缺口：主营构成、官方主营业务来源和估值日期仍需复核。

## 研究员判断
当前结论保持候选证据边界，不把行业叙事写成公司兑现。

## 数据质量说明
- 数据质量状态：manual_review_required caveats 必须可见。
- candidate 不等于 verified fact。

## 宏观与行业逻辑
- 行业逻辑只能作为传导路径，不能自动成为公司经营事实。

## 公司基本面
- 公司基本面仍需结合收入、毛利率、经营现金流和应收账款验证。

## 机会分析
- {opportunity} 是机会路径，但仍需要公司层面证据。

## 风险分析
- 回款、毛利率和订单转化不足会削弱基本面判断。

## 证据缺口
- 主营构成口径仍需复核。
- 官方主营业务来源仍需补充。

## 反证条件
- 如果订单、收入和现金流无法共同验证，则机会路径降级为待验证假设。

## 后续跟踪清单
- [ ] 订单与收入确认
- [ ] 毛利率与经营现金流
- [ ] 主营构成口径

## 技术附注
- presentation_profile_id: `stable_growth_grid_equipment`
- presentation_profile_selected_by: `strategy_type_expected`
"""


def _sample_report() -> dict:
    return {
        "code": "600406",
        "not_for_trading_advice": True,
        "presentation_profile": {
            "presentation_profile_id": "stable_growth_grid_equipment",
            "presentation_profile_selected_by": "strategy_type_expected",
        },
        "company_fundamentals": {
            "stock": {
                "stock_code": "600406",
                "stock_name": "国电南瑞",
            }
        },
        "executive_summary": {
            "one_sentence_fundamental_judgement": {
                "analysis": "SHOULD_NOT_REWRITE_MARKDOWN_CONCLUSION",
                "evidence_label": "manual_review_required",
                "caveat": "Executive summary caveat remains visible.",
            }
        },
        "company_metrics": [
            {
                "field_path": "financial_metrics.revenue",
                "evidence_label": "auto_accepted_candidate",
                "caveats": ["Candidate metric caveat remains visible."],
            }
        ],
        "evidence_gaps": [
            {
                "field_path": "basic_info.main_business",
                "evidence_label": "manual_review_required",
                "caveat": "Official source caveat remains visible.",
            }
        ],
        "follow_up_variables": [
            {
                "variable": "订单与收入确认",
                "evidence_label": "forward_tracking_variable",
                "caveat": "Forward variable is not proof.",
            }
        ],
        "source_artifact_refs": {
            "fundamental": ["research_reports/ts/code/fundamental_research_report_v1.json"],
            "presentation": ["research_reports/ts/code/fundamental_research_report_v1.md"],
        },
    }


def test_render_html_from_markdown_and_structure():
    html = render_research_report_v1_html(_sample_markdown(), _sample_report())

    assert html.startswith("<!doctype html>")
    assert '<section id="quick-read"' in html
    assert '<section id="research-body"' in html
    assert '<section id="technical-appendix"' in html
    assert "Investment Manager Quick Read" in html
    assert "投资经理速读区" in html
    assert "研究主体区" in html
    assert "技术附注区" in html
    assert "not_for_trading_advice=true" in html
    assert "基本面研究报告 V1" in html
    assert "一句话结论" in html
    assert "机会分析" in html
    assert "风险分析" in html
    assert "证据缺口" in html
    assert "反证条件" in html


def test_optional_report_metadata_does_not_rewrite_markdown_or_mutate_inputs():
    markdown = _sample_markdown()
    original_markdown = markdown
    report = _sample_report()
    before = copy.deepcopy(report)

    html = render_research_report_v1_html(markdown, report)

    assert markdown == original_markdown
    assert report == before
    assert "SHOULD_NOT_REWRITE_MARKDOWN_CONCLUSION" not in html
    assert "当前更适合作为 电网设备 / 数字电网 / 电力自动化 的证据约束型研究样本" in html
    assert "presentation_profile_id" in html
    assert "stable_growth_grid_equipment" in html


def test_evidence_badges_caveats_source_refs_and_follow_up_are_visible():
    html = render_research_report_v1_html(_sample_markdown(), _sample_report())

    assert 'data-evidence-label="auto_accepted_candidate"' in html
    assert 'data-evidence-label="manual_review_required"' in html
    assert 'data-evidence-label="forward_tracking_variable"' in html
    assert "Candidate metric caveat remains visible." in html
    assert "Official source caveat remains visible." in html
    assert "Forward variable is not proof." in html
    assert "data-quality caveats visible:" in html
    assert "research_reports/ts/code/fundamental_research_report_v1.json" in html
    assert '<ul class="checklist">' in html
    assert 'input type="checkbox" disabled' in html


def test_html_escaping_blocks_unsanitized_raw_html():
    markdown = _sample_markdown() + "\n## 附加\n<script>alert('x')</script>\n<img src=x onerror=alert(1)>\n"
    report = _sample_report()
    report["presentation_profile"]["profile_selection_warning"] = "<b onclick='x'>unsafe</b>"

    html = render_research_report_v1_html(markdown, report)

    assert "<script>alert" not in html
    assert "<img src=x" not in html
    assert "&lt;script&gt;alert" in html
    assert "&lt;img src=x" in html
    assert "&lt;b onclick=&#x27;x&#x27;&gt;unsafe&lt;/b&gt;" in html


def test_no_external_resources_or_javascript():
    html = render_research_report_v1_html(_sample_markdown(), _sample_report())
    html_lower = html.lower()

    assert "<script" not in html_lower
    assert "<link" not in html_lower
    assert "<img" not in html_lower
    assert "http://" not in html_lower
    assert "https://" not in html_lower
    assert "@import" not in html_lower
    assert "url(" not in html_lower
    assert "cdn" not in html_lower


@pytest.mark.parametrize(
    "term",
    [
        "买入",
        "卖出",
        "持有建议",
        "目标价",
        "仓位",
        "加仓",
        "减仓",
        "止损",
        "技术面交易信号",
        "确定性上涨",
        "必然兑现",
        "强烈推荐",
        "buy",
        "sell",
        "hold recommendation",
        "target price",
        "position sizing",
        "increase position",
        "reduce position",
        "stop loss",
        "technical trading signal",
        "certain upside",
        "inevitable realization",
        "strong recommend",
    ],
)
def test_forbidden_investment_action_terms_are_blocked(term):
    markdown = _sample_markdown() + f"\n## 附加\n{term}\n"

    with pytest.raises(ResearchReportBuildError):
        render_research_report_v1_html(markdown)


def test_secret_mcp_dotenv_and_local_paths_are_blocked():
    with pytest.raises(ResearchReportSecretError):
        render_research_report_v1_html(_sample_markdown() + "\ntoken=A9abcdefABCDEF1234567890abcdefABCDEF1234567890z\n")

    with pytest.raises(ResearchReportSecretError):
        render_research_report_v1_html(_sample_markdown() + "\nmcp://local-secret-endpoint\n")

    with pytest.raises(ResearchReportSecretError):
        render_research_report_v1_html(_sample_markdown() + "\nload path/to/.env.local\n")

    with pytest.raises(ResearchReportSecretError):
        render_research_report_v1_html(_sample_markdown() + "\nC:\\Users\\Admin\\secret.txt\n")


def test_candidate_label_is_not_promoted_to_verified_fact():
    html = render_research_report_v1_html(_sample_markdown(), _sample_report())

    assert "auto_accepted_candidate" in html
    assert "Candidate-level evidence; not a reviewed fact." in html
    assert "Candidate metric caveat remains visible." in html


def test_profile_language_does_not_cross_contaminate_fake_samples():
    samples = {
        "600406": (
            _sample_markdown("600406", "国电南瑞", "电网设备 / 数字电网 / 电力自动化"),
            ("电网设备", "数字电网", "电力自动化"),
            ("半导体设备", "国产替代", "晶圆厂 capex", "热管理", "制冷控制", "新能源车"),
        ),
        "002371": (
            _sample_markdown("002371", "北方华创", "半导体设备 / 国产替代 / 晶圆厂 capex"),
            ("半导体设备", "国产替代", "晶圆厂 capex"),
            ("电网设备", "数字电网", "热管理", "制冷控制", "新能源车"),
        ),
        "002050": (
            _sample_markdown("002050", "三花智控", "热管理 / 制冷控制 / 新能源车 / 新业务可选项"),
            ("热管理", "制冷控制", "新能源车", "新业务可选项"),
            ("电网设备", "数字电网", "半导体设备", "国产替代", "晶圆厂 capex"),
        ),
    }

    for markdown, expected_terms, blocked_terms in samples.values():
        html = render_research_report_v1_html(markdown)
        for term in expected_terms:
            assert term in html
        for term in blocked_terms:
            assert term not in html


def test_writer_only_writes_html_under_tmpdir(tmp_path):
    html = render_research_report_v1_html(_sample_markdown(), _sample_report())
    output_root = tmp_path / "research_reports"

    path = write_research_report_v1_html(html, output_root, "20260528T120000", "600406")

    assert path == output_root / "20260528T120000" / "600406" / HTML_OUTPUT_FILENAME
    assert path.suffix == ".html"
    assert path.read_text(encoding="utf-8").startswith("<!doctype html>")
    assert [item for item in output_root.rglob("*") if item.is_file()] == [path]


def test_writer_path_traversal_blocked(tmp_path):
    html = render_research_report_v1_html(_sample_markdown())

    with pytest.raises(ResearchReportArtifactBoundaryError):
        write_research_report_v1_html(html, tmp_path / "research_reports", "..\\escape", "600406")

    with pytest.raises(ResearchReportArtifactBoundaryError):
        write_research_report_v1_html(html, tmp_path / "research_reports", "20260528T120000", "..\\escape")


def test_writer_secret_scan_blocks_bad_html(tmp_path):
    with pytest.raises(ResearchReportSecretError) as exc_info:
        write_research_report_v1_html(
            "<!doctype html><html><body>token=A9abcdefABCDEF1234567890abcdefABCDEF1234567890z</body></html>",
            tmp_path / "research_reports",
            "20260528T120000",
            "600406",
        )
    assert "A9abcdefABCDEF1234567890abcdefABCDEF1234567890z" not in str(exc_info.value)


def test_writer_blocks_external_resources(tmp_path):
    with pytest.raises(ResearchReportBuildError):
        write_research_report_v1_html(
            '<!doctype html><html><body><script src="https://example.com/a.js"></script></body></html>',
            tmp_path / "research_reports",
            "20260528T120000",
            "600406",
        )


def test_html_module_has_no_provider_env_network_or_mcp_runtime_imports():
    source = inspect.getsource(html_module)

    assert "data_providers" not in source
    assert "tushare_provider" not in source
    assert "akshare_provider" not in source
    assert "provider_router" not in source
    assert "import os" not in source
    assert "os.environ" not in source
    assert "getenv" not in source
    assert "requests" not in source
    assert "socket" not in source
    assert "urllib" not in source
    assert "list_mcp" not in source
    assert "mcp__" not in source
    assert "scoring_engine" not in source
    assert "readiness" not in source
    assert "validator" not in source


def test_rendered_html_contains_no_forbidden_terms_for_clean_report():
    html = render_research_report_v1_html(_sample_markdown(), _sample_report())

    for term in FORBIDDEN_RENDERED_TERMS:
        assert term not in html
    assert not re.search(r"\bbuy\b|\bsell\b|\btarget\s+price\b|\bstop\s+loss\b", html, flags=re.IGNORECASE)
