# claude-for-cn-finance

面向中国金融从业者的 Claude plugin 工具集 — A股研究、基金分析、固收理财、风险画像。

## 项目定位

本项目是 [Anthropic financial-services](https://github.com/anthropics/financial-services) 的中国本土化版本，采用同一套 skill 源文件双部署到 Claude Code plugin 和 Claude Cowork plugin。

## 功能模块

| 模块 | 说明 |
|------|------|
| **financial-analysis** | 核心金融建模 + AKShare/Tushare 数据连接器 |
| **a-share-research** | A股研究：财报分析、行业比较、估值模型 |
| **fund-analysis** | 公募/私募基金分析：持仓穿透、业绩归因、风格漂移 |
| **fixed-income** | 债券/银行理财/固收产品分析 |
| **risk-profiling** | 投资者风险画像诊断与组合偏离度分析 |

## 数据源

- [AKShare](https://github.com/akfamily/akshare) — 免费开源金融数据接口
- [Tushare](https://tushare.pro/) — 需注册 token，数据更全面

## 免责声明

本工具仅供分析研究使用，**不构成任何投资建议**。使用者应独立判断并承担投资风险。

## License

Apache 2.0
