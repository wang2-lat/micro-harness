"""
FinFars - Financial Research Auto-Generation System

A vertical harness specialized for equity research.
Demonstrates technique 9: domain-specific tools replacing generic ones.

Generic Claude Code harness: 5 tools (read/write/edit/bash/grep)
FinFars harness: 8 domain tools (fetch_filing, fetch_prices, fetch_news, etc.)

This is what a $10/month "AI equity analyst" product looks like.
"""
from __future__ import annotations
import os
import sys
import json
import urllib.request
import urllib.parse
from pathlib import Path
from dataclasses import dataclass
from datetime import datetime, timedelta

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from harness import MicroHarness, HarnessConfig, TOOLS_SCHEMA, TOOL_DISPATCH


# ═══════════════════════════════════════════════════════════════
# Domain-Specific Tools (the vertical harness edge)
# ═══════════════════════════════════════════════════════════════

SEC_EDGAR_BASE = "https://data.sec.gov"
USER_AGENT = "FinFars Research Tool contact@example.com"


def _http_get_json(url: str, headers: dict | None = None) -> dict | None:
    """Fetch URL, return parsed JSON or None on error."""
    req = urllib.request.Request(url, headers={
        "User-Agent": USER_AGENT,
        "Accept": "application/json",
        **(headers or {}),
    })
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read().decode("utf-8"))
    except Exception as e:
        return {"_error": str(e)}


def _ticker_to_cik(ticker: str) -> str | None:
    """Convert ticker symbol to SEC CIK (10-digit zero-padded)."""
    data = _http_get_json("https://www.sec.gov/files/company_tickers.json")
    if not data or "_error" in data:
        return None
    ticker_upper = ticker.upper()
    for entry in data.values():
        if entry.get("ticker") == ticker_upper:
            return str(entry["cik_str"]).zfill(10)
    return None


# ─── Tool: fetch_filing ─────────────────────────────────────────

def tool_fetch_filing(ticker: str, filing_type: str = "10-K", limit: int = 1) -> str:
    """Fetch recent SEC filings for a company."""
    cik = _ticker_to_cik(ticker)
    if not cik:
        return f"ERROR: Could not find CIK for ticker {ticker}"

    url = f"{SEC_EDGAR_BASE}/submissions/CIK{cik}.json"
    data = _http_get_json(url)
    if not data or "_error" in data:
        err = data.get("_error", "unknown") if data else "no data"
        return f"ERROR: SEC EDGAR request failed: {err}"

    recent = data.get("filings", {}).get("recent", {})
    forms = recent.get("form", [])
    dates = recent.get("filingDate", [])
    accession = recent.get("accessionNumber", [])
    docs = recent.get("primaryDocument", [])

    matches = []
    for i, form in enumerate(forms):
        if form == filing_type and i < len(dates):
            accession_clean = accession[i].replace("-", "")
            filing_url = f"{SEC_EDGAR_BASE.replace('data.', 'www.')}/Archives/edgar/data/{int(cik)}/{accession_clean}/{docs[i]}"
            matches.append({
                "form": form, "date": dates[i], "accession": accession[i], "url": filing_url,
            })
            if len(matches) >= limit:
                break

    if not matches:
        return f"No {filing_type} filings found for {ticker}"

    return json.dumps({"ticker": ticker, "cik": cik, "company": data.get("name"), "filings": matches}, indent=2)


# ─── Tool: fetch_company_facts ──────────────────────────────────

def tool_fetch_company_facts(ticker: str, concepts: list[str] | None = None) -> str:
    """Fetch fundamentals (revenue, net income, etc.) from SEC."""
    cik = _ticker_to_cik(ticker)
    if not cik:
        return f"ERROR: Could not find CIK for ticker {ticker}"

    url = f"{SEC_EDGAR_BASE}/api/xbrl/companyfacts/CIK{cik}.json"
    data = _http_get_json(url)
    if not data or "_error" in data:
        err = data.get("_error", "unknown") if data else "no data"
        return f"ERROR: {err}"

    if concepts is None:
        concepts = ["Revenues", "NetIncomeLoss", "Assets", "Liabilities", "StockholdersEquity"]

    result = {"company": data.get("entityName"), "concepts": {}}
    us_gaap = data.get("facts", {}).get("us-gaap", {})

    for concept in concepts:
        if concept not in us_gaap:
            continue
        units = us_gaap[concept].get("units", {})
        # Get USD amounts, most recent
        for unit_key in ["USD", "shares"]:
            if unit_key in units:
                recent = sorted(units[unit_key], key=lambda x: x.get("end", ""), reverse=True)[:4]
                result["concepts"][concept] = [
                    {"period": e.get("end"), "value": e.get("val"), "form": e.get("form")}
                    for e in recent
                ]
                break

    return json.dumps(result, indent=2)


# ─── Tool: fetch_stock_price ────────────────────────────────────

def tool_fetch_stock_price(ticker: str, period: str = "1mo") -> str:
    """Fetch recent stock prices from Yahoo Finance (public API)."""
    # Yahoo public chart API
    period_days = {"1d": 1, "5d": 5, "1mo": 30, "3mo": 90, "1y": 365}.get(period, 30)
    period2 = int(datetime.now().timestamp())
    period1 = int((datetime.now() - timedelta(days=period_days)).timestamp())

    url = (f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}"
           f"?period1={period1}&period2={period2}&interval=1d")

    data = _http_get_json(url)
    if not data or "_error" in data:
        err = data.get("_error", "unknown") if data else "no data"
        return f"ERROR: {err}"

    try:
        result = data["chart"]["result"][0]
        meta = result["meta"]
        timestamps = result.get("timestamp", [])
        quote = result["indicators"]["quote"][0]
        closes = quote.get("close", [])
        volumes = quote.get("volume", [])

        prices = []
        for i, ts in enumerate(timestamps):
            if i < len(closes) and closes[i] is not None:
                prices.append({
                    "date": datetime.fromtimestamp(ts).strftime("%Y-%m-%d"),
                    "close": round(closes[i], 2),
                    "volume": volumes[i] if i < len(volumes) else None,
                })

        return json.dumps({
            "ticker": ticker,
            "currency": meta.get("currency"),
            "current_price": meta.get("regularMarketPrice"),
            "52w_high": meta.get("fiftyTwoWeekHigh"),
            "52w_low": meta.get("fiftyTwoWeekLow"),
            "period": period,
            "prices": prices[-20:],  # last 20 bars
        }, indent=2)
    except (KeyError, IndexError) as e:
        return f"ERROR parsing response: {e}"


# ─── Tool: search_news ──────────────────────────────────────────

def tool_search_news(query: str, days: int = 7) -> str:
    """Search recent news (uses Yahoo search as free source)."""
    # Yahoo Finance news search
    url = f"https://query2.finance.yahoo.com/v1/finance/search?q={urllib.parse.quote(query)}&newsCount=10"
    data = _http_get_json(url)
    if not data or "_error" in data:
        err = data.get("_error", "unknown") if data else "no data"
        return f"ERROR: {err}"

    news = data.get("news", [])
    cutoff = datetime.now() - timedelta(days=days)
    articles = []
    for n in news[:15]:
        pub_ts = n.get("providerPublishTime", 0)
        pub_date = datetime.fromtimestamp(pub_ts)
        if pub_date < cutoff:
            continue
        articles.append({
            "title": n.get("title"),
            "publisher": n.get("publisher"),
            "date": pub_date.strftime("%Y-%m-%d"),
            "link": n.get("link"),
        })

    return json.dumps({"query": query, "days": days, "articles": articles}, indent=2)


# ─── Tool: compute_metrics ──────────────────────────────────────

def tool_compute_metrics(data_json: str) -> str:
    """Compute common financial ratios from concept data."""
    try:
        d = json.loads(data_json)
        concepts = d.get("concepts", {})

        def latest(name):
            vals = concepts.get(name, [])
            return vals[0]["value"] if vals else None

        revenue = latest("Revenues")
        net_income = latest("NetIncomeLoss")
        assets = latest("Assets")
        liabilities = latest("Liabilities")
        equity = latest("StockholdersEquity")

        metrics = {}
        if revenue and net_income:
            metrics["net_margin_pct"] = round(net_income / revenue * 100, 2)
        if assets and liabilities:
            metrics["leverage_ratio"] = round(assets / (assets - liabilities), 2) if (assets - liabilities) else None
            metrics["debt_to_assets_pct"] = round(liabilities / assets * 100, 2)
        if net_income and equity:
            metrics["roe_pct"] = round(net_income / equity * 100, 2)
        if net_income and assets:
            metrics["roa_pct"] = round(net_income / assets * 100, 2)

        metrics["raw"] = {
            "revenue": revenue, "net_income": net_income,
            "assets": assets, "liabilities": liabilities, "equity": equity,
        }
        return json.dumps(metrics, indent=2)
    except Exception as e:
        return f"ERROR: {e}"


# ─── Register domain tools ──────────────────────────────────────

FINFARS_TOOLS = TOOLS_SCHEMA + [
    {
        "name": "fetch_filing",
        "description": "Fetch recent SEC filings (10-K, 10-Q, 8-K) for a public company by ticker.",
        "input_schema": {
            "type": "object",
            "properties": {
                "ticker": {"type": "string"},
                "filing_type": {"type": "string", "default": "10-K"},
                "limit": {"type": "integer", "default": 1},
            },
            "required": ["ticker"],
        },
    },
    {
        "name": "fetch_company_facts",
        "description": "Get company fundamentals (revenue, net income, assets) from SEC.",
        "input_schema": {
            "type": "object",
            "properties": {
                "ticker": {"type": "string"},
                "concepts": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["ticker"],
        },
    },
    {
        "name": "fetch_stock_price",
        "description": "Get recent stock prices and 52-week range from Yahoo Finance.",
        "input_schema": {
            "type": "object",
            "properties": {
                "ticker": {"type": "string"},
                "period": {"type": "string", "default": "1mo", "enum": ["1d", "5d", "1mo", "3mo", "1y"]},
            },
            "required": ["ticker"],
        },
    },
    {
        "name": "search_news",
        "description": "Search recent financial news articles by query.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "days": {"type": "integer", "default": 7},
            },
            "required": ["query"],
        },
    },
    {
        "name": "compute_metrics",
        "description": "Calculate financial ratios (ROE, ROA, margins, leverage) from company facts JSON.",
        "input_schema": {
            "type": "object",
            "properties": {
                "data_json": {"type": "string", "description": "JSON output from fetch_company_facts"},
            },
            "required": ["data_json"],
        },
    },
]

FINFARS_DISPATCH = {
    **TOOL_DISPATCH,
    "fetch_filing": tool_fetch_filing,
    "fetch_company_facts": tool_fetch_company_facts,
    "fetch_stock_price": tool_fetch_stock_price,
    "search_news": tool_search_news,
    "compute_metrics": tool_compute_metrics,
}


# ═══════════════════════════════════════════════════════════════
# Research Report Generator
# ═══════════════════════════════════════════════════════════════

EQUITY_RESEARCH_PROMPT = """You are FinFars, a senior equity research analyst AI.

Your job: produce institutional-quality equity research reports on public companies.

Use these specialized tools:
- fetch_filing: get SEC filings (10-K annual, 10-Q quarterly, 8-K material events)
- fetch_company_facts: get fundamental financials from SEC
- fetch_stock_price: get recent price history and 52-week range
- search_news: get recent news articles about the company
- compute_metrics: calculate financial ratios from fundamentals
- write: save the final report to disk
- read: read existing reports or data files

Report structure (required sections):
1. **Executive Summary** (3-5 sentences, key thesis)
2. **Company Overview** (what they do, key products)
3. **Financial Analysis** (revenue trends, profitability, balance sheet)
4. **Recent Developments** (news from last 30 days)
5. **Stock Performance** (price trends, 52-week range)
6. **Investment Thesis** (bull case, bear case)
7. **Key Risks** (3-5 material risks)
8. **Recommendation** (Buy/Hold/Sell with rationale)

Style:
- Concise and data-driven
- Cite specific numbers with sources
- No fluff or disclaimers
- Use markdown formatting
"""


def generate_report(ticker: str, output_path: str | None = None) -> str:
    """Generate an equity research report for the given ticker."""
    output_path = output_path or f"/tmp/finfars-{ticker.upper()}.md"

    # Create a specialized harness for equity research
    config = HarnessConfig(
        max_turns=25,
        use_cache=True,
        use_bootstrap=False,  # don't need env for financial research
        use_file_index=False,
        verbose=True,
    )

    harness = MicroHarness(config)

    # Monkey-patch the harness to use FinFars tools
    import harness as harness_module
    harness_module.TOOLS_SCHEMA = FINFARS_TOOLS
    harness_module.TOOL_DISPATCH = FINFARS_DISPATCH

    task = (f"Generate a comprehensive equity research report on {ticker.upper()}. "
            f"Use all available tools to gather financial data, recent news, and market context. "
            f"Save the final report to {output_path} using the write tool. "
            f"Follow the required report structure.")

    # Override system prompt with equity research persona
    from harness import build_system_prompt
    original_build = build_system_prompt

    def custom_build(*args, **kwargs):
        kwargs.pop("base_instructions", None)
        return original_build(EQUITY_RESEARCH_PROMPT, *args[1:], **kwargs)

    harness_module.build_system_prompt = custom_build

    result = harness.run(task)

    # Restore
    harness_module.build_system_prompt = original_build

    return output_path if result.success else f"FAILED: {result.error}"


# ═══════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python finfars.py <TICKER> [output_path]")
        print("Example: python finfars.py AAPL")
        sys.exit(1)

    ticker = sys.argv[1].upper()
    output = sys.argv[2] if len(sys.argv) > 2 else None

    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("Set ANTHROPIC_API_KEY first.")
        sys.exit(1)

    print(f"Generating equity research report for {ticker}...")
    path = generate_report(ticker, output)
    print(f"\nReport saved to: {path}")
