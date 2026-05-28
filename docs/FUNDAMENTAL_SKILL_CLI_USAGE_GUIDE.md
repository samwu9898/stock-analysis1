# Fundamental Skill CLI Usage Guide

Date: 2026-05-28

Stage: Fundamental Skill CLI Usage Documentation.

Status: documentation-only usage guide. This guide records how Codex and
developers should call the accepted single-stock offline CLI / command wrapper
after the CLI implementation and the `600406` / `002371` / `002050` CLI
runtime runs were accepted. It does not modify code, tests, fixtures, pipeline
behavior, scoring / readiness, Research Intelligence P1.1, regression expected
files, provider-primary behavior, or runtime artifacts. It does not run smoke
tests, read `TUSHARE_TOKEN`, use the network, call Tushare or AkShare, connect
MCP, generate output, stage output, or provide investment advice.

Latest verification results are quoted from the accepted stage input and were
not rerun in this documentation-only stage:

- targeted tests `163 passed`
- full pytest `811 passed, 1 skipped`
- regression `passed=47 failed=0 total=47`

## 1. 使用目标

The user can ask Codex for a single-stock fundamental research report in
natural language. Codex can then use one stable CLI command to trigger the
accepted offline orchestration for Research Report V1.

Usage goals:

- 用户在 Codex 中自然语言请求某只股票报告。
- Codex 用 CLI 命令触发 accepted offline orchestration。
- 用户不需要手动运行 candidate builder、review decision builder、Research
  Report V1 JSON builder、Markdown renderer 或 HTML renderer。
- CLI 返回 HTML / Markdown / JSON 路径和中文摘要。
- 当前只支持 `offline_local_artifacts`。
- 默认路径不联网、不读 token、不调用 provider、不接 MCP。

## 2. 推荐命令

Accepted stock-code invocation:

```bat
python -m src.fundamental_skill.research_report.generate_report --code 600406 --format html --data-mode offline_local_artifacts
```

Accepted company-name invocations:

```bat
python -m src.fundamental_skill.research_report.generate_report --company-name 北方华创 --format html
```

```bat
python -m src.fundamental_skill.research_report.generate_report --company-name 三花智控 --format html
```

These commands are the accepted single-stock offline CLI baseline. They should
not be replaced by old runner entry points.

## 3. Codex 调用方式

When Codex receives a user request for a single-stock Research Report V1, it
should:

1. 识别 `code` / `company-name`。
2. 选择默认 `offline_local_artifacts`。
3. 执行 CLI。
4. 返回 stdout 中的 HTML / Markdown / JSON 路径和中文摘要。
5. 不复制整份报告正文，除非用户明确要求。
6. 不主动请求 token。
7. 不联网。
8. 不调用 provider。

Codex should keep the response short and operational: report status, paths,
summary, opportunity, risk, evidence gap, data-quality status, and the
not-for-trading-advice statement.

## 4. 参数说明

| Parameter | Meaning | Current accepted use |
| --- | --- | --- |
| `--code` | A-share stock code, such as `600406`. | Primary target selector. Required unless `--company-name` is present. |
| `--company-name` | Local company name or alias, such as `北方华创`. | Resolve from local metadata / accepted artifacts only. Required unless `--code` is present. |
| `--format` | Output selection: `json`, `markdown`, `html`, or `all`. | Default and accepted user-facing mode is `html`; stdout should still include JSON / Markdown paths when available. |
| `--data-mode` | Input data mode. | Current accepted default is `offline_local_artifacts`. Current CLI usage guide does not enable live provider mode. |
| `--provider-comparison-root` | Optional local root for already generated provider-comparison artifacts. | Local-artifact-only input when a separately accepted local comparison path is used; never triggers live provider calls. |
| `--output-root` | Root for located or generated Research Report V1 outputs. | Default `output/research_reports`; runtime outputs remain ignored artifacts. |
| `--timestamp` | Optional deterministic timestamp for local output routing. | Does not imply fixture promotion or regression expected updates. |
| `--no-network` | Safety flag. | Effective default is true; CLI must fail closed if a path attempts network access. |
| `--no-token-read` | Safety flag. | Effective default is true; CLI must not read `TUSHARE_TOKEN` or provider tokens. |
| `--not-for-trading-advice` | Safety / product-boundary flag. | Required for all user-facing report outputs. |
| `--strict-evidence-boundary` | Evidence-boundary flag. | Required; missing, candidate, or disputed evidence must not be upgraded by wording. |

If both `--code` and `--company-name` are supplied, `--code` is primary and
`--company-name` is only a consistency hint.

## 5. 输出说明

Successful stdout is Chinese and operational. It should include:

- report status;
- HTML path;
- Markdown path;
- JSON path;
- 中文摘要;
- 最大机会;
- 最大风险;
- 最大证据缺口;
- 数据质量状态;
- 重要声明。

The CLI should not dump the full report body. It should return artifact paths
and a concise summary so the user can open the accepted HTML / Markdown /
JSON artifacts as needed.

## 6. 错误处理

Suggested accepted exit-code behavior:

| Exit code | Meaning |
| --- | --- |
| `2` | 缺 `--code` / `--company-name` or invalid request. |
| `3` | Missing local artifacts. |
| `4` | Safety boundary violation. |
| `5` | Unsupported mode or unsupported argument combination. |

Error handling rules:

- 缺本地 artifacts 时返回 missing checklist。
- 不自动联网。
- 不主动建议 live provider。
- 不自由生成报告。
- 不使用模型绕过 accepted artifact chain 编写最终报告。

## 7. Safety / guardrails

The accepted CLI usage boundary is:

- 不读 `TUSHARE_TOKEN`;
- 不联网;
- 不调用 Tushare / AkShare / provider;
- 不接 MCP;
- 不读 MCP config;
- 不写 fixture;
- 不改 scoring / P1.1 / regression;
- 不提交 runtime output;
- 不输出买卖建议、目标价、仓位、技术面交易信号。

Negative disclaimer wording such as "not trading advice", "no target price",
and "no position sizing" is allowed as boundary clarification. Positive
investment-action language remains prohibited.

## 8. 已验收 baseline

- `600406` CLI runtime accepted.
- `002371` CLI runtime accepted.
- `002050` CLI runtime accepted.
- Single-stock offline CLI baseline frozen.
- Docs closeout:
  `docs/FUNDAMENTAL_SKILL_CLI_RUNTIME_ACCEPTANCE_SUMMARY.md`.
- Default CLI mode remains offline local artifacts / no live provider / no
  token / no network / no MCP.

Accepted runtime commands:

```bat
python -m src.fundamental_skill.research_report.generate_report --code 600406 --format html --data-mode offline_local_artifacts
python -m src.fundamental_skill.research_report.generate_report --company-name 北方华创 --format html
python -m src.fundamental_skill.research_report.generate_report --company-name 三花智控 --format html
```

## 9. 后续路线

1. 提交 CLI usage guide documentation patch。
2. 后续进入 batch / dashboard design。
3. Keep live provider / Tushare token / MCP / CNInfo / official parser /
   validator for later separately accepted stages.
