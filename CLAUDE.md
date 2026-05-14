# Claude Code 项目配置

## 项目概述

claude-for-cn-finance 是 [Anthropic financial-services](https://github.com/anthropics/financial-services) 的中国本土化版本，面向中国金融从业者提供 Claude plugin 工具集。

### 项目规模
- **24 个 SKILL.md**（覆盖 5 个 vertical plugin）
- **20 个 command**（`/cn-finance:*` 命名空间）
- **2 个 MCP server**（AKShare + Tushare，JSON-RPC 2.0 over stdio）
- **5 个脚本**（check.py、validate.py、sync-agent-skills.py、deploy-managed-agent.py、test-cookbooks.py）
- **3 套 CMA cookbook**（market-researcher、fund-screener、risk-advisor）

### 五个 Vertical Plugin

| Vertical | Skills | Commands | 定位 |
|----------|--------|----------|------|
| **financial-analysis** | 6 | 5 | 核心层：建模工具 + 数据连接器 |
| **a-share-research** | 5 | 5 | A股研究：财报/估值/板块/政策/公司速览 |
| **fund-analysis** | 5 | 4 | 基金分析：筛选/持仓/归因/漂移/经理 |
| **fixed-income** | 4 | 3 | 固收理财：债券/收益率曲线/可转债/银行理财 |
| **risk-profiling** | 4 | 3 | 风险画像：风险计算/匹配度诊断/集中度/压力测试 |

## 核心原则

- 所有 skill 内容使用中文编写
- 不提供投资建议，只做分析工具
- 合规红线参见 [docs/compliance-redlines.md](docs/compliance-redlines.md)
- 数据源方案参见 [docs/data-sources.md](docs/data-sources.md)

## 目录结构

```
claude-for-cn-finance/
├── .claude-plugin/
│   └── plugin.json                      ← 顶层 marketplace manifest
├── plugins/
│   ├── vertical-plugins/                ← skill 源文件（在此编辑）
│   │   ├── financial-analysis/          ← 核心层：skills/ + commands/ + mcp-servers/ + .mcp.json
│   │   ├── a-share-research/            ← A股研究：skills/ + commands/
│   │   ├── fund-analysis/               ← 基金分析：skills/ + commands/
│   │   ├── fixed-income/                ← 固收理财：skills/ + commands/
│   │   └── risk-profiling/              ← 风险画像：skills/ + commands/
│   └── agent-plugins/                   ← 同步副本（由 sync-agent-skills.py 生成）
├── managed-agent-cookbooks/             ← CMA cookbooks（agent.yaml + subagents + steering examples）
│   ├── market-researcher/
│   ├── fund-screener/
│   └── risk-advisor/
├── scripts/
│   ├── check.py                         ← lint 所有 manifest + 校验交叉引用
│   ├── validate.py                      ← 验证 SKILL.md frontmatter 格式
│   ├── sync-agent-skills.py             ← 从 vertical-plugins 同步到 agent-plugins
│   ├── deploy-managed-agent.py          ← CMA 部署脚本（引用解析 + skill 上传 + POST /v1/agents）
│   └── test-cookbooks.py                ← 所有 cookbook dry-run 验证
├── .github/workflows/                   ← CI（secret-scan + cookbook 验证 + plugin lint）
├── docs/
│   ├── compliance-redlines.md           ← 合规红线文档
│   └── data-sources.md                  ← 数据源方案文档
├── .claude-plugin/plugin.json           ← Marketplace 注册
├── CLAUDE.md
├── README.md
├── LICENSE                              ← Apache 2.0
└── .gitignore
```

## 开发工作流

1. 在 `plugins/vertical-plugins/<vertical>/skills/` 中编写/编辑 skill
2. 运行 `python3 scripts/check.py` 校验所有 manifest（当前: 94 checks）
3. 运行 `python3 scripts/validate.py` 验证 SKILL.md 格式（当前: 80 files）
4. 运行 `python3 scripts/sync-agent-skills.py` 同步到 agent-plugins
5. 运行 `python3 scripts/test-cookbooks.py` 验证 CMA cookbook 完整性
5. 每个 SKILL.md 末尾必须包含合规边界 checklist
6. 每个涉及数据输出的 command 末尾必须附带 disclaimer

## Skill 规范

### Frontmatter 格式
```yaml
---
name: skill-name          # 不超过 64 字符
description: "描述..."     # 不超过 200 字符
---
```

### 末尾必须包含
```markdown
## 合规边界
- [ ] 不包含具体标的推荐
- [ ] 不包含买卖时点建议
- [ ] 不包含仓位配置建议
- [ ] 所有分析结果附带免责声明
- [ ] 不要求用户提供证券账户信息
```

## 数据源

- **AKShare**: 免费开源金融数据接口（无需注册）
  - MCP server: `mcp-servers/akshare-server.py`
  - 用户安装: `pip install akshare`
- **Tushare**: 需注册 token，数据更全面
  - MCP server: `mcp-servers/tushare-server.py`
  - 用户安装: `pip install tushare`
  - 环境变量: `TUSHARE_TOKEN`

## 注意事项

- 所有 MCP 连接器统一放在 `plugins/vertical-plugins/financial-analysis/`
- 禁止在 skill 中给出买卖建议或价格预测
- Plugin 不经手用户数据，数据从源直达用户本地
- 用户自行注册和管理数据源 API token
- skill body 控制在 500 行以内，详细内容放 `references/` 子文件夹
