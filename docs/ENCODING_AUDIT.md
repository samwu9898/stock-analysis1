# 编码审计记录

本文件记录 `scripts/check_encoding.py` 对关键文件的只读检查结果。当前阶段不自动修复历史文件乱码，只记录风险。

运行方式：

```bash
python scripts/check_encoding.py
```

如检测到 `can_decode_utf8=false` 或 `suspicious_garbled_text_count > 0`，说明文件可能存在非 UTF-8 编码或中文乱码。后续阶段应先确认原始编码来源，再做小步修复，避免破坏现有逻辑。

## 2026-05-15 检查结果

本次检查的 6 个目标文件均可按 UTF-8 解码，`suspicious_garbled_text_count` 均为 0。

需要注意：PowerShell 控制台可能因输出编码设置显示为乱码，但文件本身经 Python UTF-8 读取未发现明显乱码。
