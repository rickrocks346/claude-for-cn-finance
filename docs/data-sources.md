# 数据源方案

> 本文档说明 claude-for-cn-finance 支持的数据源及其配置方式。
> Plugin 只提供 connector 模板，用户自行注册数据源账号并管理 API token。
> Token 存储在用户本地，不会上传或共享。

---

## 数据源对比

| 特性 | AKShare | Tushare |
|------|---------|---------|
| **费用** | 完全免费，开源 | 基础接口免费（注册送积分），高级接口需付费/捐赠 |
| **API Key** | 不需要 | 需要注册获取 token |
| **安装** | `pip install akshare` | `pip install tushare` |
| **A股行情** | 支持（实时/历史日线/分钟线） | 支持（日线/周线/月线） |
| **财务数据** | 支持（三表+指标） | 支持（三表+财务指标，字段更全） |
| **基金数据** | 支持（净值/持仓/规模） | 支持（净值/持仓/分红） |
| **宏观数据** | 支持（GDP/CPI/PMI/M2等） | 支持（GDP/CPI/PPI/利率等） |
| **债券数据** | 支持（可转债） | 支持（可转债+债券基本信息） |
| **期货/期权** | 支持 | 支持（部分） |
| **更新频率** | 日频（部分接口T+1） | 日频（T+1为主） |
| **调用限制** | 无硬性限制（受数据源爬取影响） | 免费用户有限制（按积分+频率） |
| **稳定性** | 中（依赖上游数据源，偶有接口变动） | 较高（专业数据服务商） |
| **文档** | 中文，较完善 | 中文，专业 |
| **适用场景** | 个人研究、快速原型、不需要高频调用的场景 | 专业分析、批量数据获取、需要稳定接口的场景 |

---

## AKShare 配置

### 1. 安装

```bash
pip install akshare
```

AKShare 默认安装后即可使用，无需注册或配置 API key。

### 2. 安装 MCP server 依赖

```bash
pip install mcp
```

### 3. 验证安装

```bash
python3 -c "import akshare as ak; print(ak.__version__)"
```

### 4. 注意事项

- AKShare 数据来源于公开网站爬取，部分接口可能因上游变动而临时不可用
- 如遇接口报错，建议更新至最新版：`pip install --upgrade akshare`
- AKShare 官方文档：[https://akshare.akfamily.xyz/](https://akshare.akfamily.xyz/)
- 接口变动信息关注 GitHub：[https://github.com/akfamily/akshare](https://github.com/akfamily/akshare)

---

## Tushare 配置

### 1. 注册账号

访问 [https://tushare.pro/register](https://tushare.pro/register) 注册。

### 2. 获取 Token

注册后登录 → 个人主页 → 接口 Token → 复制。

### 3. 设置环境变量

**macOS / Linux:**
```bash
export TUSHARE_TOKEN=your_token_here
```

**Windows (PowerShell):**
```powershell
$env:TUSHARE_TOKEN="your_token_here"
```

**永久配置（macOS / Linux）：**
将 `export TUSHARE_TOKEN=your_token_here` 添加到 `~/.bashrc` 或 `~/.zshrc`。

**永久配置（Windows）：**
```powershell
[Environment]::SetEnvironmentVariable("TUSHARE_TOKEN", "your_token_here", "User")
```

### 4. 安装

```bash
pip install tushare mcp
```

### 5. 验证安装

```bash
python3 -c "import tushare as ts; ts.set_token('your_token_here'); pro = ts.pro_api(); print(pro.query('trade_cal', exchange='SSE', start_date='20250101', end_date='20250110'))"
```

### 6. 积分制度

| 积分区间 | 权限 |
|---------|------|
| 注册（200 积分） | 基础和常用接口（日线行情、财务数据、指数等） |
| 捐赠 200+ | 解锁全部接口，无频率限制 |
| 完成任务 | 获取额外积分 |

- 积分查询：[https://tushare.pro/user/token](https://tushare.pro/user/token)
- 积分规则：[https://tushare.pro/document/1?doc_id=39](https://tushare.pro/document/1?doc_id=39)

---

## 常见问题

### Q: Tushare 提示 "该接口需要 X 积分"？
A: 当前接口超出了你的积分等级。方案：
1. 做任务赚积分（每日签到、邀请用户等）
2. 捐赠获取更高积分档位
3. 如果只是基础查询，可以切换到 AKShare

### Q: AKShare 某个接口突然报错？
A: 可能上游数据源变动。方案：
1. 更新 AKShare：`pip install --upgrade akshare`
2. 在 [AKShare GitHub Issues](https://github.com/akfamily/akshare/issues) 搜索是否已有报告
3. 切换到 Tushare 作为临时替代

### Q: 能否同时使用两个数据源？
A: 可以。MCP 配置中已经同时启用两个 server，调用时 Claude 会根据需求选择最合适的数据源。

### Q: 我的 Token 安全吗？
A: Token 存储在本地环境变量中，只在使用时从本地读取，不会上传到任何服务器。确保 `.env` 和 token 文件已被 `.gitignore` 排除。

---

## Token 安全管理

- Token 存储在用户本地的环境变量（`TUSHARE_TOKEN`）或 `.mcp.json` 中
- `.gitignore` 已排除 `.env`、`.env.*`、`*.token`、`*.local.md`
- 项目代码中**不包含**任何真实 token
- 如果怀疑 token 已泄露，登录 [https://tushare.pro/user/token](https://tushare.pro/user/token) 重置

---

## 未来计划

以下数据源已列入评估，可能在未来版本中支持：

| 数据源 | 类型 | 状态 |
|--------|------|------|
| **东方财富 Choice** | 商业终端数据 | 未来计划 |
| **Wind 万得** | 专业金融终端 | 未来计划（需机构授权） |
| **聚宽 JoinQuant** | 量化平台数据 | 未来计划 |
| **通联数据 DataAPI** | 金融数据 API | 未来计划 |

如果你有特定数据源需求，欢迎提 Issue。

---

*文档版本：v0.1.0 | 创建日期：2026-05-14*
