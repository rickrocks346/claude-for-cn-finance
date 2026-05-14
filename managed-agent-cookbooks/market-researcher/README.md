# Market Researcher — managed-agent template

## 概述

A 股市场研究 Agent，覆盖：公司财报分析 → 行业比较 → 估值建模 → 政策影响 → 板块轮动 → 研究输出。

与 [`market-researcher`](../../plugins/agent-plugins/market-researcher) Cowork plugin 共享同一份 system prompt 和 skills — 本目录是 `POST /v1/agents` 的 CMA (Claude Managed Agent) cookbook。

## 部署

```bash
export ANTHROPIC_API_KEY=sk-ant-...
export AKSHARE_MCP_URL=...
py scripts/deploy-managed-agent.py market-researcher
```

## Steering events

见 [`steering-examples.json`](./steering-examples.json)。可从研究队列事件触发，也可按行业覆盖矩阵批量 fan-out。

## 安全与 handoff

财报和研究报告属于不受信任文档。三层安全隔离：

| 层级 | 接触不受信任文档? | 工具 | MCP Connectors |
|---|---|---|---|
| **`doc-reader`** | **是** | `Read`, `Grep` only | 无 |
| `comps-builder` / Orchestrator | 否 | `Read`, `Grep`, `Glob` | AKShare（只读） |
| **`note-writer`** (Write 持有者) | 否 | `Read`, `Write`, `Edit` | 无 |

`doc-reader` 返回长度受限、schema 校验的 JSON。`note-writer` 产出 `./out/` 目录下的 `.md` 或 `.xlsx` 文件。

**Handoff:** 如需对研究报告中识别的单个标的进行深度估值建模，可在输出中 emit `handoff_request` 指向 `model-builder`（后续版本支持）。
