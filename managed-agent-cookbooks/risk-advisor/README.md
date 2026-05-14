# Risk Advisor — managed-agent template

## 概述

投资组合风险诊断 Agent，覆盖：持仓解析 → 风险指标计算 → 压力测试 → 集中度分析 → C1-C5 匹配度诊断 → 风险评估报告。

与 [`risk-advisor`](../../plugins/agent-plugins/risk-advisor) Cowork plugin 共享同一份 system prompt 和 skills — 本目录是 `POST /v1/agents` 的 CMA (Claude Managed Agent) cookbook。

## 部署

```bash
export ANTHROPIC_API_KEY=sk-ant-...
export AKSHARE_MCP_URL=...
py scripts/deploy-managed-agent.py risk-advisor
```

## Steering events

见 [`steering-examples.json`](./steering-examples.json)。可从投顾系统或客户端风险诊断请求触发。

## 安全与 handoff

持仓清单和账户对账单属于高度敏感的不受信任文档。三层安全隔离：

| 层级 | 接触不受信任文档? | 工具 | MCP Connectors |
|---|---|---|---|
| **`portfolio-reader`** | **是** | `Read`, `Grep` only | 无 |
| `risk-calculator` / Orchestrator | 否 | `Read`, `Grep`, `Glob` | AKShare（只读） |
| **`report-writer`** (Write 持有者) | 否 | `Read`, `Write`, `Edit` | 无 |

`portfolio-reader` 绝不要求用户提供账户号或密码，仅解析用户主动上传的脱敏组合清单。返回 schema 校验的 JSON，长度受限（最多 200 个持仓）。`report-writer` 产出 `./out/` 目录下的 `.md` 或 `.xlsx` 文件。

**重要合规提示:** 报告仅做描述性诊断，不包含调仓建议、买卖时点建议或仓位配置建议。报告必须包含免责声明。
