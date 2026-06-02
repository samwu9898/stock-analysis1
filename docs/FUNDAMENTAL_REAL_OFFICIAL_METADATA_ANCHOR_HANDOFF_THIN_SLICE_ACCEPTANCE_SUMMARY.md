# Real Official Metadata Discovery for Anchor Handoff Thin Slice Acceptance Summary

## 1. 阶段名称

Real Official Metadata Discovery for Anchor Handoff Thin Slice

## 2. Baseline Commits

- implementation commit: `ec12e983a9fb1a0a82aaeb8a8e99828f87dc922e`
- previous completed stage: Provider Queue -> Official Disclosure Anchor acceptance summary commit `ecb86b7`

## 3. 本阶段目标

本阶段目标是将 `official_disclosure_discovery_request.v1` 通过真实官方 CNInfo metadata discovery 转换为 real official metadata records，并将 metadata records 交给 existing `official_source_discovery_adapter`，再将 adapter candidates 交给 existing `provider_metric_official_anchor_map`，完成 metadata-only real official discovery -> anchor handoff。

本阶段明确不做 PDF 下载、不做 PDF 解析、不做指标抽取、不生成 `official_metric_fact`、不生成 `provider_official_conflict`、不接 Report V1。matched anchor 仍不等于 `official_verified`。

## 4. 修改文件清单

本阶段 implementation commit 只包含以下 3 个 expected files：

- `src/fundamental_skill/data_verification/real_official_metadata_anchor_handoff.py`
- `tests/test_real_official_metadata_anchor_handoff.py`
- `tests/test_real_official_metadata_anchor_handoff_safety.py`

## 5. 功能摘要

- 新增 `real_official_metadata_anchor_handoff_result.v1`。
- 新增 `real_official_metadata_discovery_result.v1`。
- 新增 `real_official_metadata_record.v1`。
- `source_family` 第一版仅支持 `cninfo`。
- CNInfo metadata endpoint 固定为 `https://www.cninfo.com.cn/new/hisAnnouncement/query`。
- metadata request host 只允许 `www.cninfo.com.cn`。
- metadata record source host 只允许 `www.cninfo.com.cn` / `static.cninfo.com.cn`。
- 默认 `allow_network=False`。
- 只有 `allow_network=True` 才可执行真实 metadata request。
- response size limit: 2MB。
- timeout: 15s。
- content-type only allows `application/json` / `text/html` / `text/plain`。
- PDF URL 只作为 metadata 字符串保留。
- PDF URL 会附加 `pdf_url_preserved_metadata_only` caveat。
- 不下载 PDF。
- 不读取 PDF bytes。
- 不解析 PDF。

## 6. Handoff 摘要

metadata records 先交给 existing `discover_official_sources_from_metadata`，adapter result 通过 `validate_official_source_discovery_adapter_result`，adapter candidates 再交给 existing `build_provider_metric_official_disclosure_anchor_map`，anchor map result 通过 `validate_provider_metric_official_disclosure_anchor_map`。

本阶段不绕过 adapter，不绕过 anchor map，不生成 official facts。anchor matched 只是公告定位，不是指标核验。

## 7. Live Smoke 摘要

manual live smoke 已执行并成功。

600406 / 2025FY：

- 找到 1 条。
- 标题：国电南瑞2025年年度报告。
- 披露日：2026-04-29。
- domain: `static.cninfo.com.cn`。
- adapter: `candidate_found`。
- anchor: `matched`。

600406 / 2026Q1：

- 找到 1 条。
- 标题：国电南瑞2026年第一季度报告。
- 披露日：2026-04-29。
- domain: `static.cninfo.com.cn`。
- adapter: `candidate_found`。
- anchor: `matched`。

smoke 只输出 metadata summary；未下载 PDF；未解析 PDF；未写 output / fixtures / manifest。

## 8. 三方审计和 Patch 摘要

- Gemini: PASS，但提示 urllib redirect 风险。
- DeepSeek: PASS_WITH_PATCH_NEEDED，要求 commit 前检查重定向后的 final host。
- Kimi: PASS_WITH_PATCH_NEEDED，将 urllib 默认跟随重定向列为 commit 前 blocker。
- 主策划裁定：PASS_WITH_PATCH_NEEDED。
- patch 已完成。
- patch 后无 blocker。

Patch 内容：

- `_default_cninfo_http_client` 读取 response 后调用 `response.geturl()`。
- 校验 final host 仍在 `ALLOWED_CNINFO_METADATA_REQUEST_HOSTS`。
- 非 allowlist final host 抛出固定 `ValueError("non_allowlist_redirect_final_host")`。
- 上层结构化为 `official_metadata_transport_error`。
- 不输出 final URL。
- 新增 non-allowlist redirect 测试。
- 新增 allowlist final host 正常解析测试。
- 新增 `application/pdf` content-type rejection 测试。
- 新增 response size 超限 fail-closed 测试。

## 9. Tests 结果

- pre-patch targeted tests: 75 passed。
- pre-patch related tests: 285 passed。
- patch 后 targeted tests: 79 passed。
- patch 后 related tests: 285 passed。
- system python 不可用时使用 Codex bundled Python。

## 10. 明确未触碰的禁区

本阶段确认未触碰以下禁区：

- `official_disclosure_request.py`
- `official_source_discovery_adapter.py`
- `provider_metric_official_anchor.py`
- `provider_candidate_verification_queue.py`
- Tushare provider module
- Research Report V1 generator
- HTML renderer
- Dashboard
- `schemas.py` / `validators.py`
- accepted manifest
- output baseline
- fixtures
- output 读取/写入
- token / `.env` / `tushare_token` 文件读取
- `.local_experiments`
- unrelated mojibake files
- unrelated examples file
- PDF download / parser
- table extraction
- metric extraction
- `official_metric_fact`
- `provider_official_conflict`
- provider-vs-official reconciliation
- 买入 / 卖出 / 持有
- 目标价
- 仓位
- 技术信号

## 11. 当前剩余 Untracked 项

当前阶段记录的剩余 untracked / 不得处理项包括：

- `.local_experiments/`
- `output/`
- `tushare_token.txt`
- unrelated mojibake files
- unrelated examples file

## 12. 当前阶段结论

- implementation accepted。
- no blocker。
- summary doc is docs-only。
- 项目已从 explicit official metadata candidate anchor 推进到 real official metadata discovery + anchor handoff。
- 这仍然不是 PDF 下载 / official evidence extraction。
- 这仍然不是 `official_metric_fact`。
- 这仍然不是 formal Research Pack / Report V1。
- 下一阶段应先 reassess。
- 后续建议评估是否进入 Official Artifact Download / Cache Acquisition Thin Slice，或先扩展 metadata discovery 多 source / 多交易所。
- 不要直接进入 Report V1 或交易建议。
