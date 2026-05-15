#!/usr/bin/env python3
"""
AKShare MCP Server — 开源金融数据连接器

用户需先安装: pip install akshare mcp
AKShare 免费开源，无需注册或 API key。
数据覆盖: A股、基金、宏观、期货、期权、债券、外汇等。

MCP protocol: JSON-RPC 2.0 over stdio.
All requests come via stdin, responses go to stdout.
"""

import json
import sys
import traceback
from typing import Any

# UTF-8 is required for MCP JSON-RPC protocol over stdio.
# On Windows, sys.stdout.encoding defaults to 'gbk' which corrupts
# Chinese characters in JSON-RPC messages.
sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")


# ---------------------------------------------------------------------------
# AKShare wrapper — lazy import to allow tools/list before pip install check
# ---------------------------------------------------------------------------

_ak = None


def _get_ak():
    global _ak
    if _ak is None:
        try:
            import akshare as ak  # type: ignore
            _ak = ak
        except ImportError:
            raise RuntimeError(
                "AKShare 未安装。请运行: pip install akshare"
            )
    return _ak


# ---------------------------------------------------------------------------
# Tool definitions
# ---------------------------------------------------------------------------

TOOLS = [
    {
        "name": "get_stock_quote",
        "description": "获取A股个股实时行情或历史日线行情。返回开盘价、收盘价、最高价、最低价、成交量、涨跌幅等。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "symbol": {
                    "type": "string",
                    "description": "股票代码，如 '600519'（贵州茅台）或 '000001'（平安银行）",
                },
                "period": {
                    "type": "string",
                    "enum": ["daily", "weekly", "monthly"],
                    "description": "K线周期，默认 daily",
                },
                "start_date": {
                    "type": "string",
                    "description": "开始日期 YYYYMMDD，如 '20240101'",
                },
                "end_date": {
                    "type": "string",
                    "description": "结束日期 YYYYMMDD，如 '20241231'",
                },
                "adjust": {
                    "type": "string",
                    "enum": ["qfq", "hfq", ""],
                    "description": "复权类型: qfq=前复权, hfq=后复权, 空=不复权",
                },
            },
            "required": ["symbol"],
        },
    },
    {
        "name": "get_financial_statements",
        "description": "获取A股上市公司财务数据（资产负债表、利润表、现金流量表关键指标）。适用于财报分析和杜邦分析。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "symbol": {
                    "type": "string",
                    "description": "股票代码",
                },
                "report_type": {
                    "type": "string",
                    "enum": ["balance_sheet", "income_statement", "cashflow", "key_indicators"],
                    "description": "报表类型。key_indicators 返回核心财务指标汇总",
                },
                "report_date": {
                    "type": "string",
                    "description": "报告期，如 '20241231' 表示2024年报",
                },
            },
            "required": ["symbol"],
        },
    },
    {
        "name": "get_fund_nav",
        "description": "获取公募基金净值数据（单位净值、累计净值、日增长率）。支持开放式基金和ETF。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "fund_code": {
                    "type": "string",
                    "description": "基金代码，如 '000001'（华夏成长混合）",
                },
                "indicator": {
                    "type": "string",
                    "description": "指标类型: 单位净值走势(默认), 累计净值走势, 累计收益率走势",
                },
                "period": {
                    "type": "string",
                    "description": "时间范围: 交易日(默认), 1月, 3月, 6月, 1年, 3年, 5年, 成立以来, 今年来",
                },
            },
            "required": ["fund_code"],
        },
    },
    {
        "name": "get_macro_indicator",
        "description": "获取中国宏观经济指标，包括GDP、CPI、PPI、PMI、M2、社融、固定资产投资、社零等。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "indicator": {
                    "type": "string",
                    "enum": ["gdp", "cpi", "ppi", "pmi", "m2", "social_finance", "fixed_asset_investment", "retail_sales", "trade"],
                    "description": "宏观指标类型",
                },
                "start_date": {
                    "type": "string",
                    "description": "开始日期 YYYYMMDD",
                },
                "end_date": {
                    "type": "string",
                    "description": "结束日期 YYYYMMDD",
                },
            },
            "required": ["indicator"],
        },
    },
    {
        "name": "get_industry_data",
        "description": "获取申万行业板块数据（行业指数、涨跌幅、资金流向）。适用于行业比较和板块轮动分析。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "industry_name": {
                    "type": "string",
                    "description": "行业名称（申万一级/二级），如 '食品饮料'、'半导体'。留空返回所有行业概览。",
                },
                "indicator_type": {
                    "type": "string",
                    "enum": ["index", "pe", "pb", "roe", "roe_ttm"],
                    "description": "指标类型。index=行业指数行情, pe/pb=估值数据",
                },
                "start_date": {
                    "type": "string",
                    "description": "开始日期 YYYYMMDD（仅用于 index 类型）",
                },
            },
            "required": [],
        },
    },
    {
        "name": "get_stock_list",
        "description": "获取A股全市场股票列表（代码、简称、行业、上市日期、总市值）。适用于股票筛选和代码查找。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "market": {
                    "type": "string",
                    "enum": ["sh", "sz", "bj", "all"],
                    "description": "市场: sh=上海, sz=深圳, bj=北京（北交所）, all=全部",
                },
            },
            "required": [],
        },
    },
]

# ---------------------------------------------------------------------------
# Tool handlers
# ---------------------------------------------------------------------------

HANDLERS = {}


def handler(name: str):
    """Decorator to register tool handlers."""
    def dec(fn):
        HANDLERS[name] = fn
        return fn
    return dec


@handler("get_stock_quote")
def handle_stock_quote(args: dict) -> dict:
    ak = _get_ak()
    symbol = args["symbol"]
    period = args.get("period", "daily")
    start = args.get("start_date", "20240101")
    end = args.get("end_date", "20251231")
    adjust = args.get("adjust", "qfq")

    df = ak.stock_zh_a_hist(
        symbol=symbol,
        period=period,
        start_date=start,
        end_date=end,
        adjust=adjust,
    )
    return {
        "symbol": symbol,
        "period": period,
        "adjust": adjust,
        "count": len(df),
        "data": df.tail(100).to_dict(orient="records"),
    }


@handler("get_financial_statements")
def handle_financial_statements(args: dict) -> dict:
    ak = _get_ak()
    symbol = args["symbol"]
    report_type = args.get("report_type", "key_indicators")

    if report_type == "balance_sheet":
        df = ak.stock_balance_sheet_by_report_em(symbol=symbol)
    elif report_type == "income_statement":
        df = ak.stock_profit_sheet_by_report_em(symbol=symbol)
    elif report_type == "cashflow":
        df = ak.stock_cash_flow_sheet_by_report_em(symbol=symbol)
    else:
        df = ak.stock_financial_analysis_indicator(symbol=symbol)

    return {
        "symbol": symbol,
        "report_type": report_type,
        "count": len(df),
        "data": df.head(20).to_dict(orient="records"),
    }


@handler("get_fund_nav")
def handle_fund_nav(args: dict) -> dict:
    ak = _get_ak()
    fund_code = args["fund_code"]
    indicator = args.get("indicator", "单位净值走势")
    period = args.get("period", "交易日")

    df = ak.fund_open_fund_info_em(
        symbol=fund_code,
        indicator=indicator,
        period=period,
    )
    return {
        "fund_code": fund_code,
        "indicator": indicator,
        "period": period,
        "count": len(df) if df is not None else 0,
        "data": df.to_dict(orient="records") if df is not None else [],
    }


@handler("get_macro_indicator")
def handle_macro_indicator(args: dict) -> dict:
    ak = _get_ak()
    indicator = args["indicator"]

    mapping = {
        "gdp": ak.macro_china_gdp,
        "cpi": ak.macro_china_cpi_monthly,
        "ppi": ak.macro_china_ppi_yearly,
        "pmi": ak.macro_china_pmi,
        "m2": ak.macro_china_money_supply,
        "social_finance": ak.macro_china_shrzgm,
        "fixed_asset_investment": ak.macro_china_fixed_asset_investment,
        "retail_sales": ak.macro_china_consumer_goods_retail,
        "trade": ak.macro_china_trade_balance,
    }

    fn = mapping.get(indicator)
    if fn is None:
        raise ValueError(f"Unknown indicator: {indicator}")

    df = fn()
    return {
        "indicator": indicator,
        "count": len(df),
        "data": df.head(60).to_dict(orient="records"),
    }


@handler("get_industry_data")
def handle_industry_data(args: dict) -> dict:
    ak = _get_ak()
    indicator_type = args.get("indicator_type", "index")

    if indicator_type == "pe":
        df = ak.index_value_hist_funddb(symbol="all", indicator="PE")
    elif indicator_type == "pb":
        df = ak.index_value_hist_funddb(symbol="all", indicator="PB")
    elif indicator_type == "roe":
        df = ak.index_value_hist_funddb(symbol="all", indicator="ROE")
    else:
        df = ak.stock_board_industry_index_ths()

    return {
        "indicator_type": indicator_type,
        "count": len(df) if df is not None else 0,
        "data": df.head(50).to_dict(orient="records") if df is not None else [],
    }


@handler("get_stock_list")
def handle_stock_list(args: dict) -> dict:
    ak = _get_ak()
    df = ak.stock_info_a_code_name()
    return {
        "total_count": len(df),
        "data": df.head(200).to_dict(orient="records"),
        "note": "结果截断至前200条，请使用 market 参数缩小范围",
    }


# ---------------------------------------------------------------------------
# JSON-RPC 2.0 over stdio
# ---------------------------------------------------------------------------

def send_response(id_val: Any, result: Any):
    """Send a JSON-RPC success response to stdout."""
    msg = json.dumps({"jsonrpc": "2.0", "id": id_val, "result": result}, ensure_ascii=False, default=str)
    sys.stdout.write(msg + "\n")
    sys.stdout.flush()


def send_error(id_val: Any, code: int, message: str):
    """Send a JSON-RPC error response to stdout."""
    msg = json.dumps({
        "jsonrpc": "2.0",
        "id": id_val,
        "error": {"code": code, "message": message},
    }, ensure_ascii=False)
    sys.stdout.write(msg + "\n")
    sys.stdout.flush()


def handle_request(req: dict):
    method = req.get("method", "")
    req_id = req.get("id")
    params = req.get("params", {})

    if method == "initialize":
        send_response(req_id, {
            "protocolVersion": "2024-11-05",
            "capabilities": {"tools": {}},
            "serverInfo": {
                "name": "akshare-mcp-server",
                "version": "0.1.0",
            },
        })

    elif method == "notifications/initialized":
        pass  # No response for notifications

    elif method == "tools/list":
        send_response(req_id, {"tools": TOOLS})

    elif method == "tools/call":
        tool_name = params.get("name", "")
        tool_args = params.get("arguments", {})

        handler_fn = HANDLERS.get(tool_name)
        if handler_fn is None:
            send_error(req_id, -32601, f"Unknown tool: {tool_name}")
            return

        try:
            result = handler_fn(tool_args)
            send_response(req_id, {
                "content": [
                    {"type": "text", "text": json.dumps(result, ensure_ascii=False, default=str, indent=2)}
                ]
            })
        except Exception as e:
            send_response(req_id, {
                "content": [
                    {"type": "text", "text": f"Error: {e}\n{traceback.format_exc()}"}
                ],
                "isError": True,
            })

    elif method == "ping":
        send_response(req_id, {})

    else:
        send_error(req_id, -32601, f"Method not found: {method}")


def main():
    """Main loop: read JSON-RPC requests from stdin, write responses to stdout."""
    # Log initialization to stderr (stdout is for JSON-RPC protocol)
    print("AKShare MCP Server starting...", file=sys.stderr)

    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
            handle_request(req)
        except json.JSONDecodeError as e:
            print(f"Invalid JSON: {e}", file=sys.stderr)
        except Exception as e:
            print(f"Unexpected error: {e}\n{traceback.format_exc()}", file=sys.stderr)


if __name__ == "__main__":
    main()
