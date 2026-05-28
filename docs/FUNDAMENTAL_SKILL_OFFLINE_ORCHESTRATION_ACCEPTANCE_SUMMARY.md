# Fundamental Skill Offline Orchestration Acceptance Summary

Date: 2026-05-28

Stage: Fundamental Skill Single-Stock Offline Orchestration Three-Sample
Acceptance Summary.

Status: documentation-only acceptance closeout. This summary records that the
single-stock offline orchestration implementation, the Chinese summary patch,
and the three accepted local runtime samples have passed end-to-end acceptance
for one-sentence local report invocation. It does not modify code, tests,
fixtures, pipeline behavior, scoring / readiness, Research Intelligence P1.1,
regression expected files, provider-primary behavior, or runtime artifacts. It
does not run smoke tests, read `TUSHARE_TOKEN`, use the network, call Tushare
or AkShare, connect MCP, generate output, stage output, or provide investment
advice.

Latest verification results are quoted from the accepted stage input and were
not rerun in this documentation-only stage:

- targeted tests `147 passed`
- full pytest `795 passed, 1 skipped`
- regression `passed=47 failed=0 total=47`

## 1. Final status

- Single-stock offline orchestration implementation accepted.
- Chinese summary patch accepted.
- `600406` runtime accepted.
- `002371` runtime accepted.
- `002050` runtime accepted.
- One-sentence local report invocation baseline frozen.

## 2. Accepted runtime table

| code | company | user prompt | selected HTML artifact | selected Markdown artifact | selected JSON artifact | status | result summary source | acceptance result |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `600406` | 国电南瑞 | `帮我生成 600406 国电南瑞的基本面投研报告。` | `output/research_reports/20260528T012952/600406/fundamental_research_report_v1.html` | `output/research_reports/20260527T210301/600406/fundamental_research_report_v1.md` | `output/research_reports/20260527T103241/600406/fundamental_research_report_v1.json` | Runtime accepted | Accepted Markdown Chinese summary extraction | Accepted: one-sentence offline local report invocation returned HTML / Markdown / JSON paths, opportunity / risk / evidence gap / data-quality summary, and not-for-trading-advice statement. |
| `002371` | 北方华创 | `分析一下北方华创的基本面，输出 HTML 报告。` | `output/research_reports/20260528T090024/002371/fundamental_research_report_v1.html` | `output/research_reports/20260527T220148/002371/fundamental_research_report_v1.md` | `output/research_reports/20260527T220148/002371/fundamental_research_report_v1.json` | Runtime accepted | Accepted Markdown Chinese summary extraction | Accepted: one-sentence offline local report invocation returned HTML / Markdown / JSON paths, opportunity / risk / evidence gap / data-quality summary, and not-for-trading-advice statement. |
| `002050` | 三花智控 | `用当前本地数据给我生成三花智控的研究报告。` | `output/research_reports/20260528T091133/002050/fundamental_research_report_v1.html` | `output/research_reports/20260528T003826/002050/fundamental_research_report_v1.md` | `output/research_reports/20260527T222558/002050/fundamental_research_report_v1.json` | Runtime accepted | Accepted Markdown Chinese summary extraction | Accepted: one-sentence offline local report invocation returned HTML / Markdown / JSON paths, opportunity / risk / evidence gap / data-quality summary, and not-for-trading-advice statement. |

## 3. Validated flow

The three accepted runtime samples validated the same default V1 flow:

```text
user natural-language request
  -> normalize request
  -> safe offline flags
  -> locate local artifacts
  -> reuse accepted HTML
  -> extract Chinese summary from Markdown
  -> return HTML / Markdown / JSON paths
  -> return opportunity / risk / evidence gap / data quality
  -> not-for-trading-advice statement
```

The accepted baseline is a local orchestration path over already accepted
artifacts. It is not a live data path and not a free-written model report.

## 4. Safety / boundary

The accepted offline orchestration runtime boundary is:

- no token read;
- no network;
- no provider call;
- no MCP;
- no live provider;
- no old runner reuse;
- no free-written report;
- no fixture write;
- no scoring / P1.1 change;
- no regression expected change;
- no runtime artifact committed;
- no buy / sell / target price / position sizing / trading signal.

## 5. Known limitations

- Current behavior is offline local artifact orchestration only.
- Live provider mode has not been implemented.
- Codex natural language to CLI / command-layer invocation has not been
  formally packaged.
- Batch / Dashboard has not been implemented for this path.
- Official parser / CNInfo has not been implemented.
- Validator, fixture promotion, and Tushare primary remain later work.
- Runtime artifacts remain under ignored `output/` paths and do not enter git.
- `002371` and `002050` content thickness still depends on future evidence
  enrichment.

## 6. Next recommended stage

1. Commit this documentation summary.
2. Enter user invocation CLI / command wrapper design or implementation.
3. Let Codex call orchestration through one command, for example:

```bash
python -m src.fundamental_skill.research_report.generate_report --code 600406 --format html --data-mode offline_local_artifacts
```

4. Do batch / Dashboard only after the single-stock CLI is accepted.
5. Keep live provider, Tushare token, MCP, CNInfo, and validator later.

## 7. Safety confirmation

This documentation-only acceptance summary confirms:

- no token read;
- no network use;
- no provider call;
- no MCP connection;
- no output generated;
- no runtime artifact submitted;
- no investment advice output.
