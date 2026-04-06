"""
LawFars — Legal Research Auto-Generation System

Vertical harness for legal research using free US legal data APIs.
Generates structured legal research memos on any topic.

Data sources (all free, no auth):
- CourtListener: 7M+ US court opinions
- Federal Register: US regulations and rulemaking
- SEC EDGAR: securities filings full-text search
"""
from __future__ import annotations
import os
import sys
import json
import urllib.request
import urllib.parse
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from harness import TOOL_DISPATCH, TOOLS_SCHEMA

USER_AGENT = "LawFars Research Tool contact@example.com"


def _http_get_json(url: str) -> dict | None:
    req = urllib.request.Request(url, headers={
        "User-Agent": USER_AGENT, "Accept": "application/json",
    })
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return json.loads(r.read().decode("utf-8"))
    except Exception as e:
        return {"_error": str(e)}


# ─── Tool: search_cases ─────────────────────────────────────

def tool_search_cases(query: str, court: str = "", after_date: str = "", limit: int = 10) -> str:
    """Search US court opinions via CourtListener."""
    params = {"q": query, "type": "o", "format": "json", "page_size": min(limit, 20)}
    if court:
        params["court"] = court
    if after_date:
        params["filed_after"] = after_date

    url = "https://www.courtlistener.com/api/rest/v4/search/?" + urllib.parse.urlencode(params)
    data = _http_get_json(url)
    if not data or "_error" in data:
        return f"ERROR: {data.get('_error', 'unknown') if data else 'no response'}"

    results = data.get("results", [])
    cases = []
    for r in results[:limit]:
        cases.append({
            "case_name": r.get("caseName", ""),
            "court": r.get("court", ""),
            "date_filed": r.get("dateFiled", ""),
            "citation": r.get("citation", [None])[0] if r.get("citation") else "",
            "url": f"https://www.courtlistener.com{r.get('absolute_url', '')}",
            "snippet": (r.get("snippet", "") or "")[:300],
        })

    return json.dumps({"query": query, "total": data.get("count", 0), "cases": cases}, indent=2)


# ─── Tool: search_regulations ────────────────────────────────

def tool_search_regulations(query: str, agency: str = "", after_date: str = "", limit: int = 10) -> str:
    """Search Federal Register for regulations and rulemaking."""
    params = {
        "conditions[term]": query,
        "per_page": min(limit, 20),
        "order": "relevance",
    }
    if agency:
        params["conditions[agencies][]"] = agency
    if after_date:
        params["conditions[publication_date][gte]"] = after_date

    url = "https://www.federalregister.gov/api/v1/documents.json?" + urllib.parse.urlencode(params)
    data = _http_get_json(url)
    if not data or "_error" in data:
        return f"ERROR: {data.get('_error', 'unknown') if data else 'no response'}"

    results = data.get("results", [])
    regs = []
    for r in results[:limit]:
        regs.append({
            "title": r.get("title", ""),
            "type": r.get("type", ""),
            "agency": ", ".join(r.get("agencies", [{}])[0].get("name", "") for a in [r] if r.get("agencies")),
            "date": r.get("publication_date", ""),
            "abstract": (r.get("abstract", "") or "")[:300],
            "url": r.get("html_url", ""),
            "citation": r.get("citation", ""),
        })

    return json.dumps({"query": query, "total": data.get("count", 0), "regulations": regs}, indent=2)


# ─── Tool: search_sec_filings ────────────────────────────────

def tool_search_sec_filings(query: str, form_type: str = "", after_date: str = "", limit: int = 10) -> str:
    """Search SEC EDGAR full-text search for securities-related filings."""
    params = {
        "q": f'"{query}"',
        "dateRange": "custom",
        "startdt": after_date or "2024-01-01",
        "enddt": datetime.now().strftime("%Y-%m-%d"),
    }
    if form_type:
        params["forms"] = form_type

    url = "https://efts.sec.gov/LATEST/search-index?" + urllib.parse.urlencode(params)
    data = _http_get_json(url)
    if not data or "_error" in data:
        return f"ERROR: {data.get('_error', 'unknown') if data else 'no response'}"

    hits = data.get("hits", {}).get("hits", [])
    filings = []
    for h in hits[:limit]:
        src = h.get("_source", {})
        filings.append({
            "entity": src.get("entity_name", ""),
            "form": src.get("form_type", ""),
            "date": src.get("file_date", ""),
            "description": (src.get("file_description", "") or "")[:200],
        })

    total = data.get("hits", {}).get("total", {}).get("value", 0)
    return json.dumps({"query": query, "total": total, "filings": filings}, indent=2)


# ─── Tool: get_case_detail ───────────────────────────────────

def tool_get_case_detail(case_url: str) -> str:
    """Get full opinion text from a CourtListener case URL."""
    # Convert web URL to API URL
    api_url = case_url.replace("www.courtlistener.com", "www.courtlistener.com/api/rest/v4")
    if not api_url.endswith("/"):
        api_url += "/"
    api_url += "?format=json"

    data = _http_get_json(api_url)
    if not data or "_error" in data:
        return f"ERROR: {data.get('_error', 'unknown') if data else 'no response'}"

    # Extract key info
    plain_text = data.get("plain_text", "") or data.get("html", "") or ""
    # Strip HTML tags if present
    import re
    plain_text = re.sub(r'<[^>]+>', '', plain_text)

    return json.dumps({
        "case_name": data.get("case_name", ""),
        "date_filed": data.get("date_filed", ""),
        "court": data.get("court", ""),
        "judges": data.get("judges", ""),
        "opinion_text": plain_text[:5000],  # First 5000 chars
    }, indent=2)


# ─── Register all tools ─────────────────────────────────────

LAWFARS_TOOLS_SCHEMA = TOOLS_SCHEMA + [
    {
        "name": "search_cases",
        "description": "Search US court opinions by keyword. Returns case names, courts, dates, citations, and snippets.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query for case law"},
                "court": {"type": "string", "description": "Court filter (e.g. 'scotus' for Supreme Court)"},
                "after_date": {"type": "string", "description": "Only cases after this date (YYYY-MM-DD)"},
                "limit": {"type": "integer", "default": 10},
            },
            "required": ["query"],
        },
    },
    {
        "name": "search_regulations",
        "description": "Search Federal Register for regulations, rules, and proposed rules.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "agency": {"type": "string", "description": "Agency name filter"},
                "after_date": {"type": "string", "description": "Published after (YYYY-MM-DD)"},
                "limit": {"type": "integer", "default": 10},
            },
            "required": ["query"],
        },
    },
    {
        "name": "search_sec_filings",
        "description": "Full-text search SEC EDGAR filings for securities law research.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "form_type": {"type": "string", "description": "Filing type (10-K, 10-Q, 8-K, etc.)"},
                "after_date": {"type": "string", "description": "Filed after (YYYY-MM-DD)"},
                "limit": {"type": "integer", "default": 10},
            },
            "required": ["query"],
        },
    },
    {
        "name": "get_case_detail",
        "description": "Get full opinion text from a CourtListener case URL.",
        "input_schema": {
            "type": "object",
            "properties": {
                "case_url": {"type": "string", "description": "CourtListener case URL"},
            },
            "required": ["case_url"],
        },
    },
]

LAWFARS_DISPATCH = {
    **TOOL_DISPATCH,
    "search_cases": tool_search_cases,
    "search_regulations": tool_search_regulations,
    "search_sec_filings": tool_search_sec_filings,
    "get_case_detail": tool_get_case_detail,
}

LEGAL_RESEARCH_PROMPT = """You are LawFars, a senior legal research analyst AI.

Your job: produce well-structured legal research memos on any topic.

Use these specialized tools:
- search_cases: find relevant US court opinions (7M+ cases)
- search_regulations: find Federal Register rules and rulemaking
- search_sec_filings: search SEC filings for securities law topics
- get_case_detail: read the full text of a specific court opinion
- write: save the final memo to disk

Legal memo structure (required sections):
1. **Issue** (1-2 sentences: what legal question are we analyzing?)
2. **Background** (key facts, statutory framework, regulatory context)
3. **Case Law Analysis** (cite 3-5 relevant cases with holdings)
4. **Regulatory Landscape** (applicable regulations, recent rulemaking)
5. **Analysis** (synthesize case law + regulations, identify trends)
6. **Risk Assessment** (legal risks, compliance gaps, enforcement trends)
7. **Conclusion & Recommendations** (actionable guidance)

Style:
- Cite specific cases with dates and courts
- Quote relevant statutory provisions
- Use Bluebook-style citations
- Be analytical, not just descriptive
- Flag areas of legal uncertainty
"""


# ─── CLI ─────────────────────────────────────────────────────

if __name__ == "__main__":
    # Self-test mode: verify all data sources work
    print("=== LawFars Data Source Tests ===\n")

    print("1. Case search (AI regulation):")
    result = tool_search_cases("artificial intelligence regulation", limit=3)
    data = json.loads(result)
    print(f"   Found {data.get('total', 0)} cases")
    for c in data.get("cases", [])[:2]:
        print(f"   - {c['case_name'][:50]} ({c['date_filed']})")

    print("\n2. Regulation search (AI):")
    result = tool_search_regulations("artificial intelligence", limit=3)
    data = json.loads(result)
    print(f"   Found {data.get('total', 0)} regulations")
    for r in data.get("regulations", [])[:2]:
        print(f"   - {r['title'][:50]} ({r['date']})")

    print("\n3. SEC filing search (AI disclosure):")
    result = tool_search_sec_filings("artificial intelligence risk", form_type="10-K", limit=3)
    data = json.loads(result)
    print(f"   Found {data.get('total', 0)} filings")
    for f in data.get("filings", [])[:2]:
        print(f"   - {f['entity'][:30]} {f['form']} ({f['date']})")

    print("\n=== All data sources working ===")
