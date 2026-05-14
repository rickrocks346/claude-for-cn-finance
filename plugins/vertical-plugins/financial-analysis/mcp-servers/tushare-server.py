#!/usr/bin/env python3
"""
Tushare MCP Server — 金融数据连接器

用户需先安装: pip install tushare mcp
用户需设置环境变量: export TUSHARE_TOKEN=your_token_here
注册地址: https://tushare.pro/register

Tushare 积分制度:
- 注册即送 200 积分（基础接口）
- 捐赠或完成任务获取更多积分（高级接口）
- 免费用户有接口调用频率限制

MCP protocol: JSON-RPC 2.0 over stdio.
"""

import json
import os
import sys
import traceback
from typing import Any


# ---------------------------------------------------------------------------
# Tushare wrapper — lazy init with token from env
# ---------------------------------------------------------------------------

_ts = None


def _get_ts():
    global _ts
    if _ts is None:
        token = os.environ.get("TUSHARE_TOKEN", "")
        if not token:
            raise RuntimeError(
                "TUSHARE_TOKEN 环境变量未设置。\n"
                "请先注册 Tushare: https://tushare.pro/register\n"
                "然后设置: export TUSHARE_TOKEN=your_token_here"
            )
        try:
            import tushare as ts  # type: ignore
            ts.set_token(token)
            _ts = ts.pro_api()
        except ImportError:
            raise RuntimeError(
                "Tushare 未安装。请运行: pip install tushare"
            )
    return _ts


# ---------------------------------------------------------------------------
# Tool definitions
# ---------------------------------------------------------------------------

TOOLS = [
    {
        "name": "get_daily_quotes",
        "description": "获取A股日线行情数据（开高低收、成交量、成交额、涨跌幅、换手率等）。覆盖沪深京三市全部股票。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "ts_code": {
                    "type": "string",
                    "description": "股票代码（Tushare格式），如 '600519.SH'、'000001.SZ'。多个用逗号分隔",
                },
                "trade_date": {
                    "type": "string",
                    "description": "交易日期 YYYYMMDD，如 '20241231'。留空返回最新交易日",
                },
                "start_date": {
                    "type": "string",
                    "description": "开始日期 YYYYMMDD",
                },
                "end_date": {
                    "type": "string",
                    "description": "结束日期 YYYYMMDD",
                },
                "limit": {
                    "type": "integer",
                    "description": "返回条数上限，默认 100",
                },
            },
            "required": [],
        },
    },
    {
        "name": "get_income_statement",
        "description": "获取上市公司利润表（营业收入、营业成本、各项费用、利润总额、净利润、EPS等）。覆盖全部A股（含北交所）。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "ts_code": {
                    "type": "string",
                    "description": "股票代码（Tushare格式），如 '600519.SH'",
                },
                "start_date": {
                    "type": "string",
                    "description": "报告期开始 YYYYMMDD，如 '20230101'",
                },
                "end_date": {
                    "type": "string",
                    "description": "报告期结束 YYYYMMDD，如 '20241231'",
                },
                "report_type": {
                    "type": "string",
                    "enum": ["1", "2", "3", "4"],
                    "description": "报告类型: 1=一季报, 2=中报, 3=三季报, 4=年报。留空返回全部",
                },
            },
            "required": ["ts_code"],
        },
    },
    {
        "name": "get_balance_sheet",
        "description": "获取上市公司资产负债表（总资产、总负债、净资产、流动资产、非流动资产、流动负债、非流动负债等）。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "ts_code": {
                    "type": "string",
                    "description": "股票代码（Tushare格式），如 '600519.SH'",
                },
                "start_date": {
                    "type": "string",
                    "description": "报告期开始 YYYYMMDD",
                },
                "end_date": {
                    "type": "string",
                    "description": "报告期结束 YYYYMMDD",
                },
                "report_type": {
                    "type": "string",
                    "enum": ["1", "2", "3", "4"],
                    "description": "报告类型",
                },
            },
            "required": ["ts_code"],
        },
    },
    {
        "name": "get_cashflow",
        "description": "获取上市公司现金流量表（经营活动、投资活动、筹资活动现金流、自由现金流等）。用于三表联动分析。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "ts_code": {
                    "type": "string",
                    "description": "股票代码（Tushare格式），如 '600519.SH'",
                },
                "start_date": {
                    "type": "string",
                    "description": "报告期开始 YYYYMMDD",
                },
                "end_date": {
                    "type": "string",
                    "description": "报告期结束 YYYYMMDD",
                },
                "report_type": {
                    "type": "string",
                    "enum": ["1", "2", "3", "4"],
                    "description": "报告类型",
                },
            },
            "required": ["ts_code"],
        },
    },
    {
        "name": "get_financial_indicators",
        "description": "获取上市公司核心财务指标（ROE、ROA、毛利率、净利率、资产负债率、流动比率、EPS、每股净资产等）。一站式获取常用财务比率。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "ts_code": {
                    "type": "string",
                    "description": "股票代码（Tushare格式）",
                },
                "start_date": {
                    "type": "string",
                    "description": "报告期开始 YYYYMMDD",
                },
                "end_date": {
                    "type": "string",
                    "description": "报告期结束 YYYYMMDD",
                },
            },
            "required": ["ts_code"],
        },
    },
    {
        "name": "get_fund_portfolio",
        "description": "获取公募基金持仓明细（前十大重仓股、持仓比例）。用于基金持仓穿透分析。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "fund_code": {
                    "type": "string",
                    "description": "基金代码（Tushare格式），如 '000001.OF'",
                },
                "report_date": {
                    "type": "string",
                    "description": "报告期 YYYYMMDD，如 '20241231'",
                },
            },
            "required": ["fund_code"],
        },
    },
    {
        "name": "get_stock_basic",
        "description": "获取A股股票基本信息（代码、名称、行业、上市日期、退市日期、交易所、全称）。用于代码查找和公司基本信息。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "ts_code": {
                    "type": "string",
                    "description": "股票代码（可选，Tushare格式）。留空返回全市场股票列表",
                },
                "exchange": {
                    "type": "string",
                    "enum": ["SSE", "SZSE", "BSE"],
                    "description": "交易所: SSE=上交所, SZSE=深交所, BSE=北交所",
                },
                "list_status": {
                    "type": "string",
                    "enum": ["L", "D", "P"],
                    "description": "上市状态: L=上市, D=退市, P=暂停上市。默认 L",
                },
            },
            "required": [],
        },
    },
    {
        "name": "get_macro_data",
        "description": "获取宏观经济数据（GDP、CPI、PPI、M2、社融、利率、外汇储备等）。数据来源：国家统计局、人民银行。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "indicator": {
                    "type": "string",
                    "enum": ["gdp", "cpi", "ppi", "m2", "social_finance", "shibor", "lpr", "forex_reserve"],
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
        "name": "get_index_daily",
        "description": "获取A股主要指数日线行情（上证综指、深证成指、沪深300、创业板指、科创50、中证500等）。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "ts_code": {
                    "type": "string",
                    "description": "指数代码（Tushare格式），如 '000001.SH'（上证综指）、'399006.SZ'（创业板指）",
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
            "required": [],
        },
    },
]

# ---------------------------------------------------------------------------
# Tool handlers
# ---------------------------------------------------------------------------

HANDLERS = {}


def handler(name: str):
    def dec(fn):
        HANDLERS[name] = fn
        return fn
    return dec


@handler("get_daily_quotes")
def handle_daily(args: dict) -> dict:
    ts = _get_ts()
    kwargs = {}
    if args.get("ts_code"):
        kwargs["ts_code"] = args["ts_code"]
    if args.get("trade_date"):
        kwargs["trade_date"] = args["trade_date"]
    if args.get("start_date"):
        kwargs["start_date"] = args["start_date"]
    if args.get("end_date"):
        kwargs["end_date"] = args["end_date"]
    limit = args.get("limit", 100)
    df = ts.daily(**kwargs, limit=limit)
    return {
        "count": len(df),
        "data": df.to_dict(orient="records"),
    }


@handler("get_income_statement")
def handle_income(args: dict) -> dict:
    ts = _get_ts()
    kwargs = {"ts_code": args["ts_code"]}
    if args.get("start_date"):
        kwargs["start_date"] = args["start_date"]
    if args.get("end_date"):
        kwargs["end_date"] = args["end_date"]
    if args.get("report_type"):
        kwargs["period"] = args["report_type"]
    df = ts.income(**kwargs)
    return {
        "ts_code": args["ts_code"],
        "count": len(df),
        "data": df.to_dict(orient="records"),
    }


@handler("get_balance_sheet")
def handle_balance(args: dict) -> dict:
    ts = _get_ts()
    kwargs = {"ts_code": args["ts_code"]}
    if args.get("start_date"):
        kwargs["start_date"] = args["start_date"]
    if args.get("end_date"):
        kwargs["end_date"] = args["end_date"]
    if args.get("report_type"):
        kwargs["period"] = args["report_type"]
    df = ts.balancesheet(**kwargs)
    return {
        "ts_code": args["ts_code"],
        "count": len(df),
        "data": df.to_dict(orient="records"),
    }


@handler("get_cashflow")
def handle_cashflow(args: dict) -> dict:
    ts = _get_ts()
    kwargs = {"ts_code": args["ts_code"]}
    if args.get("start_date"):
        kwargs["start_date"] = args["start_date"]
    if args.get("end_date"):
        kwargs["end_date"] = args["end_date"]
    if args.get("report_type"):
        kwargs["period"] = args["report_type"]
    df = ts.cashflow(**kwargs)
    return {
        "ts_code": args["ts_code"],
        "count": len(df),
        "data": df.to_dict(orient="records"),
    }


@handler("get_financial_indicators")
def handle_fina_indicator(args: dict) -> dict:
    ts = _get_ts()
    kwargs = {"ts_code": args["ts_code"]}
    if args.get("start_date"):
        kwargs["start_date"] = args["start_date"]
    if args.get("end_date"):
        kwargs["end_date"] = args["end_date"]
    df = ts.fina_indicator(**kwargs)
    return {
        "ts_code": args["ts_code"],
        "count": len(df),
        "data": df.to_dict(orient="records"),
    }


@handler("get_fund_portfolio")
def handle_fund_portfolio(args: dict) -> dict:
    ts = _get_ts()
    kwargs = {"ts_code": args["fund_code"]}
    if args.get("report_date"):
        kwargs["ann_date"] = args["report_date"]
    df = ts.fund_portfolio(**kwargs)
    return {
        "fund_code": args["fund_code"],
        "count": len(df),
        "data": df.to_dict(orient="records"),
    }


@handler("get_stock_basic")
def handle_stock_basic(args: dict) -> dict:
    ts = _get_ts()
    kwargs = {"list_status": args.get("list_status", "L")}
    if args.get("ts_code"):
        kwargs["ts_code"] = args["ts_code"]
    if args.get("exchange"):
        kwargs["exchange"] = args["exchange"]
    df = ts.stock_basic(**kwargs)
    return {
        "count": len(df),
        "data": df.head(500).to_dict(orient="records"),
        "note": "结果截断至前500条，请使用 exchange 参数缩小范围",
    }


@handler("get_macro_data")
def handle_macro(args: dict) -> dict:
    ts = _get_ts()
    indicator = args["indicator"]
    kwargs = {}
    if args.get("start_date"):
        kwargs["start_date"] = args["start_date"]
    if args.get("end_date"):
        kwargs["end_date"] = args["end_date"]

    mapping = {
        "gdp": ts.cn_gdp,
        "cpi": ts.cn_cpi,
        "ppi": ts.cn_ppi,
        "m2": ts.cn_m,
        "social_finance": ts.sf_month,
        "shibor": ts.shibor,
        "lpr": ts.cn_lpr,
        "forex_reserve": ts.cn_fx_reserves,
    }

    fn = mapping.get(indicator)
    if fn is None:
        raise ValueError(f"Unknown indicator: {indicator}")

    df = fn(**kwargs)
    return {
        "indicator": indicator,
        "count": len(df),
        "data": df.to_dict(orient="records"),
    }


@handler("get_index_daily")
def handle_index_daily(args: dict) -> dict:
    ts = _get_ts()
    kwargs = {}
    if args.get("ts_code"):
        kwargs["ts_code"] = args["ts_code"]
    if args.get("start_date"):
        kwargs["start_date"] = args["start_date"]
    if args.get("end_date"):
        kwargs["end_date"] = args["end_date"]
    df = ts.index_daily(**kwargs)
    return {
        "count": len(df),
        "data": df.to_dict(orient="records"),
    }


# ---------------------------------------------------------------------------
# JSON-RPC 2.0 over stdio
# ---------------------------------------------------------------------------

def send_response(id_val: Any, result: Any):
    msg = json.dumps({"jsonrpc": "2.0", "id": id_val, "result": result}, ensure_ascii=False, default=str)
    sys.stdout.write(msg + "\n")
    sys.stdout.flush()


def send_error(id_val: Any, code: int, message: str):
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
                "name": "tushare-mcp-server",
                "version": "0.1.0",
            },
        })

    elif method == "notifications/initialized":
        pass

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
    print("Tushare MCP Server starting...", file=sys.stderr)
    token = os.environ.get("TUSHARE_TOKEN", "")
    if not token:
        print("WARNING: TUSHARE_TOKEN not set. Server will start but tools will fail on call.", file=sys.stderr)

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
