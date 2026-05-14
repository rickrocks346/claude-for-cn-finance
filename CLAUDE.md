# Claude Code 项目配置

## 项目信息

本项目是 [Anthropic financial-services](https://github.com/anthropics/financial-services) 的中国本土化版本，面向中国金融从业者提供 Claude plugin 工具集。

## 核心原则

- 所有 skill 内容使用中文编写
- 不提供投资建议，只做分析工具
- 合规红线参见 [docs/compliance-redlines.md](docs/compliance-redlines.md)
- 数据源方案参见 [docs/data-sources.md](docs/data-sources.md)

## 目录结构

```
plugins/vertical-plugins/   ← skill 源文件（在此编辑）
plugins/agent-plugins/      ← 同步副本（由 sync-agent-skills.py 生成）
scripts/                    ← 校验与同步脚本
```

## 开发工作流

1. 在 `plugins/vertical-plugins/<vertical>/skills/` 中编写/编辑 skill
2. 运行 `python3 scripts/check.py` 校验所有 manifest
3. 运行 `python3 scripts/sync-agent-skills.py` 同步到 agent-plugins
4. 运行 `python3 scripts/validate.py` 验证 SKILL.md 格式

## 数据源

- **AKShare**: 免费开源金融数据接口（无需注册）
- **Tushare**: 需注册 token，数据更全面

## 注意事项

- 所有 financial-analysis 相关的 MCP 连接器统一放在 `plugins/vertical-plugins/financial-analysis/`
- agent-plugins 目录留空，Phase 9 再填充
- 禁止在 skill 中给出买卖建议或价格预测
