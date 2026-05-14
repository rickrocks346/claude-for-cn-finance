# Fund Screener — managed-agent template

## 概述

基金筛选分析 Agent，覆盖：多维筛选 → 持仓穿透 → 业绩归因 → 风格漂移检测 → 经理能力评估 → 分析报告。

与 [`fund-screener`](../../plugins/agent-plugins/fund-screener) Cowork plugin 共享同一份 system prompt 和 skills — 本目录是 `POST /v1/agents` 的 CMA (Claude Managed Agent) cookbook。

## 部署

```bash
export ANTHROPIC_API_KEY=sk-ant-...
export AKSHARE_MCP_URL=...
py scripts/deploy-managed-agent.py fund-screener
```

## Steering events

见 [`steering-examples.json`](./steering-examples.json)。可从基金研究队列事件触发，也可按基金类型批量 fan-out。

## 安全与 handoff

基金招募说明书和定期报告属于不受信任文档。三层安全隔离：

| 层级 | 接触不受信任文档? | 工具 | MCP Connectors |
|---|---|---|---|
| **`data-reader`** | **是** | `Read`, `Grep` only | 无 |
| `screener` / Orchestrator | 否 | `Read`, `Grep`, `Glob` | AKShare（只读） |
| **`report-writer`** (Write 持有者) | 否 | `Read`, `Write`, `Edit` | 无 |

`data-reader` 返回长度受限、schema 校验的 JSON。`report-writer` 产出 `./out/` 目录下的 `.md` 或 `.xlsx` 文件。

**Handoff:** 如需对筛选出的基金组合进行风险诊断，可在输出中 emit `handoff_request` 指向 `risk-advisor`（后续版本支持）。
