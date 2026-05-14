# claude-for-cn-finance

面向中国金融从业者的 Claude plugin 工具集 — A股研究、基金分析、固收理财、风险画像。

本项目是 [Anthropic financial-services](https://github.com/anthropics/financial-services) 的中国本土化版本，采用同一套 skill 源文件双部署到 Claude Code plugin 和 Claude Cowork plugin。

> **重要声明**：本工具仅供分析研究使用，**不构成任何投资建议**。所有分析结果由 AI 生成，仅供参考。使用者应独立判断并承担投资风险。请咨询持牌专业人士后再做出投资决策。

---

## 功能总览

### financial-analysis（核心层）

所有其他 vertical 的基础依赖，提供通用金融建模工具 + MCP 数据连接器。

| Skills | Commands | 说明 |
|--------|----------|------|
| financial-statements | `/financial-report` | 中国上市公司财报分析（CAS准则、杜邦分析） |
| valuation-models | `/valuation` | DCF/DDM/可比公司估值模型框架 |
| industry-comparison | `/industry-compare` | 申万/中信行业分类下的多维度比较 |
| excel-audit | `/debug-model` | Excel 金融模型审计（公式/硬编码/平衡性） |
| data-cleaning | — | 金融数据清洗与标准化 |
| macro-indicators | `/macro-dashboard` | 中国宏观经济指标解读（GDP/CPI/PMI/M2/社融） |

### a-share-research

中国 A 股研究，完全按 A 股市场规则和逻辑设计。

| Skills | Commands | 说明 |
|--------|----------|------|
| earnings-analysis | `/earnings` | A股财报解读（披露节奏/业绩预告/CAS关键科目） |
| comparable-analysis | `/comps` | 可比公司筛选 + 估值分位分析 |
| sector-rotation | `/sector` | 板块轮动（周期/日历效应/政策-板块映射） |
| policy-impact | `/policy-brief` | 政策传导路径分析与影响矩阵 |
| company-profile | `/one-pager` | 公司一页纸速览（概况+财务+估值+股权+行业） |

### fund-analysis

中国公募/私募基金分析。

| Skills | Commands | 说明 |
|--------|----------|------|
| fund-screening | `/fund-screen` | 多维度基金筛选与比较 |
| holdings-analysis | `/holdings` | 持仓穿透（重仓股/行业配置/风格九宫格） |
| performance-attribution | `/attribution` | 业绩归因（Brinson/Barra/Sharpe） |
| style-drift | `/style-check` | 风格漂移检测（名称/仓位/市值/行业/基准） |
| manager-track-record | — | 基金经理历史业绩追踪与能力评估 |

### fixed-income

中国固收市场分析（银行间+交易所、利率债+信用债+可转债+银行理财）。

| Skills | Commands | 说明 |
|--------|----------|------|
| bond-analysis | `/bond-calc` | 债券 YTM/久期/凸性 + 信用利差分析 |
| yield-curve | `/yield-curve` | 中国国债收益率曲线形态与利率走势 |
| convertible-bond | `/cb-analysis` | 可转债（转股价值/溢价率/条款博弈） |
| bank-wealth-product | — | 银行理财产品分析（净值化/费率/风险匹配） |

### risk-profiling

投资组合风险画像诊断 — 本项目最核心的差异化功能。

| Skills | Commands | 说明 |
|--------|----------|------|
| risk-assessment | `/risk-check` | 组合风险指标计算（波动率/VaR/夏普/Beta） |
| profile-matching | `/profile-match` | C1-C5 五级风险偏好匹配度诊断 |
| concentration-analysis | — | 多维度集中度分析（个股/行业/资产/地域） |
| drawdown-analysis | `/stress-test` | 历史极端事件压力测试 |

---

## Agent Plugins（v0.1.0 新增）

自包含的 agent plugin，bundle 所需 vertical skills，可直接作为独立分析工具使用。

| Agent | Bundled Skills | 用途 |
|-------|---------------|------|
| `/market-researcher` | financial-analysis + a-share-research | A股市场研究（财报/估值/行业比较/政策/板块轮动） |
| `/fund-screener` | financial-analysis + fund-analysis | 基金筛选分析（筛选/持仓穿透/业绩归因/风格漂移） |
| `/risk-advisor` | financial-analysis + risk-profiling | 组合风险诊断（风险指标/回撤/集中度/匹配度） |

每个 agent 包含：角色定义、能力范围、合规边界、工作流程模板，位于 `agents/<slug>.md`。

---

## 安装方式

### Claude Code Plugin

```bash
claude plugin install financial-analysis@claude-for-cn-finance
# 安装全部 vertical:
claude plugin install a-share-research@claude-for-cn-finance
claude plugin install fund-analysis@claude-for-cn-finance
claude plugin install fixed-income@claude-for-cn-finance
claude plugin install risk-profiling@claude-for-cn-finance
```

### Claude Cowork Plugin

1. 打开 Cowork Plugin 设置
2. 粘贴本 repo URL
3. 选择需要的 vertical plugin

### 手动安装

```bash
git clone https://github.com/rickrocks346/claude-for-cn-finance.git
# 将 plugins/vertical-plugins/<vertical>/ 目录复制到 Claude Code plugins 目录
```

---

## 数据源配置

本项目不直接提供数据，只提供数据连接器模板。用户须自行注册和管理数据源。

### AKShare（免费，推荐）

```bash
pip install akshare
```

无需注册或 API key，安装后即可使用。

详见 [docs/data-sources.md](docs/data-sources.md) 完整配置指南。

### Tushare（需注册 token）

1. 注册 [https://tushare.pro/register](https://tushare.pro/register)
2. 获取 token
3. 设置环境变量：
   ```bash
   export TUSHARE_TOKEN=your_token_here
   ```
4. 安装：
   ```bash
   pip install tushare
   ```

---

## MCP 连接器

| 连接器 | 数据源 | Tools |
|--------|--------|-------|
| `akshare-server.py` | AKShare | 6 tools（行情、财报、基金净值、宏观、行业、股票列表） |
| `tushare-server.py` | Tushare | 9 tools（日线、三表、财务指标、基金持仓、股票信息、宏观、指数） |

配置文件位于 `plugins/vertical-plugins/financial-analysis/.mcp.json`。

---

## 自定义指南

### 修改现有 Skill

1. 编辑 `plugins/vertical-plugins/<vertical>/skills/<skill-name>/SKILL.md`
2. 运行 `python3 scripts/check.py` 校验
3. 运行 `python3 scripts/validate.py` 验证格式
4. 运行 `python3 scripts/sync-agent-skills.py` 同步到 agent-plugins

### 添加新 Command

1. 在对应 vertical 的 `commands/` 目录下创建 `.md` 文件
2. 遵循 `commands/` 中其他文件的格式（frontmatter + Input/Process/Output/合规边界）

### 接入其他数据源

1. 在 `plugins/vertical-plugins/financial-analysis/mcp-servers/` 下创建新的 MCP server 脚本
2. 参照 `akshare-server.py` 的 JSON-RPC 2.0 over stdio 协议实现
3. 在 `.mcp.json` 中添加新的 server 配置
4. 更新 `docs/data-sources.md`

---

## 合规说明

本项目严格遵守中国相关法规，详见 [docs/compliance-redlines.md](docs/compliance-redlines.md)。

**绝对禁止**：
- 推荐具体股票、基金、债券等金融产品
- 给出买卖时点建议
- 给出仓位配置建议
- 预测具体价格目标

**允许**：
- 财务报表分析、估值模型计算
- 行业比较、基金分析、风险诊断
- 宏观经济数据整理
- 投资组合风险画像（仅描述性，不推荐调仓方案）

---

## 贡献指南

1. Fork 本仓库
2. 在对应 branch 上编辑
3. 运行 `python3 scripts/check.py` 确认所有检查通过
4. 提交 PR

项目使用 Apache 2.0 协议。

---

## License

[Apache 2.0](LICENSE)

---

## 路线图

| 阶段 | 内容 | 状态 |
|------|------|------|
| Phase 0-7 | 5 个 vertical plugin 框架搭建 | 完成 |
| Phase 8 (post8a/8b) | 24 个 SKILL.md Type A+B+C 内容充实 | 完成 |
| Phase 9 | Agent plugin 层 + v0.1.0 发布 | 完成 |
| v0.2 | 新增数据源 connector（东方财富 Choice/Wind/聚宽） | 计划中 |
| v0.3 | Managed Agent 版本 | 计划中 |
| v0.4 | 小程序/轻量版客户端适配 | 探索中 |
| — | 豆包/Kimi 等其他 AI 平台适配 | 探索中 |
