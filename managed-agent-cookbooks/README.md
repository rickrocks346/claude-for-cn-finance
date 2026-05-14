# Managed-agent cookbooks for claude-for-cn-finance

每个 Agent 提供两种部署方式：Cowork plugin 和 Claude Managed Agent (CMA)。**同一份 system prompt，同一套 skills — 选择你的运行环境。** 每个目录下的 `agent.yaml` 是 CMA 部署清单，引用了对应 plugin 的标准 system prompt 和 skills，确保单一来来源。

运行 `py scripts/deploy-managed-agent.py <slug>` 上传 skills、创建 leaf worker 并 `POST /v1/agents`。每个 cookbook 附带 [`steering-examples.json`](./market-researcher/steering-examples.json) 和说明安全层级与 handoff 的 README。

| Agent | Vertical plugin | Cowork tile | CMA steering event | Leaf workers |
|---|---|---|---|---|
| [`market-researcher`](./market-researcher/) | financial-analysis + a-share-research | 行业/公司/政策/板块 → 研究报告 | `分析贵州茅台2025年年报` / `AI产业链全景分析` | doc-reader · comps-builder · **note-writer** |
| [`fund-screener`](./fund-screener/) | financial-analysis + fund-analysis | 筛选/穿透/归因/漂移/经理 → 分析报告 | `筛选近3年收益前10%的偏股混合基金` / `分析易方达蓝筹持仓风格漂移` | data-reader · screener · **report-writer** |
| [`risk-advisor`](./risk-advisor/) | financial-analysis + risk-profiling | 指标/压力/集中度/匹配度 → 诊断报告 | `诊断组合风险，C4等级` / `2024年924行情压力测试` | portfolio-reader · risk-calculator · **report-writer** |

**加粗** leaf = 唯一持有 `Write` 权限的 worker。

## Manifest vs API

`agent.yaml` 使用 `POST /v1/agents` 的实际字段名，加上 deploy 脚本在提交前解析的几个便捷写法：

| Manifest 写法 | 解析为 |
|---|---|
| `system: {file: ../../plugins/agent-plugins/<slug>/agents/<slug>.md, append: "..."}` | `system: "<内联内容 + append>"` |
| `system: {text: "..."}` | `system: "<text>"` |
| `skills: [{from_plugin: ../../plugins/agent-plugins/<slug>}]` | 上传该目录下所有 `skills/*` → `[{type: custom, skill_id: ...}, ...]` |
| `skills: [{path: ../../...}]` | `skills: [{type: custom, skill_id: <uploaded-id>}]` |
| `callable_agents: [{manifest: ./subagents/x.yaml}]` | `callable_agents: [{type: agent, id: <created-id>, version: latest}]` |

> **Research Preview:** `callable_agents`（多 agent 委托）支持**一级委托**。Orchestrator 可调用 worker；worker 不可再调用其他 subagent。

## 跨 Agent Handoff

命名 Agent 之间不直接互相调用。当一个 Agent 需要另一个 Agent 时，在输出中 emit `handoff_request`；由业务流程引擎（Temporal/Airflow/自研调度）将其路由为目标 Agent 的 steering event。

## 安全分层

所有 cookbook 遵循三层安全隔离，将不受信任文档的读取隔离在最外层：

| Tier | 接触不受信任文档? | 工具 | 数据连接器 |
|---|---|---|---|
| **Tier 1** (Reader) | **是** | `Read`, `Grep` only | 无 |
| Tier 2 (Analyzer + Orchestrator) | 否 | `Read`, `Grep`, `Glob` | AKShare（只读） |
| **Tier 3** (Writer) | 否 | `Read`, `Write`, `Edit` | 无 |
