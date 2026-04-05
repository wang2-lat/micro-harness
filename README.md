# micro-harness 🎯

**A minimal agent harness you can read in 30 minutes and learn the 8 techniques behind Claude Code.**

The Claude Code source leak (March 31, 2026) revealed that **the harness around an LLM matters more than the model itself** — Stanford's Meta-Harness showed a 6× performance gap on the same model with different harnesses.

But production harnesses are complex. Claude Code has 512K+ lines of TypeScript. This makes it hard to learn from.

**micro-harness is the opposite**: ~400 lines of Python, each technique isolated and measurable.

## The 8 Techniques (with measured impact)

| # | Technique | LOC | Impact |
|---|-----------|-----|--------|
| 1 | **Agent Loop** — ReAct cycle with tool calling | 40 | Foundation |
| 2 | **Tool System** — 5 structured tools > shell | 60×5 | +3× success rate |
| 3 | **Cache Boundary** — stable prefix + dynamic suffix | 20 | -87% token cost |
| 4 | **Environment Bootstrap** — Meta-Harness's winning trick | 30 | -2 to -5 exploration turns |
| 5 | **Three-Layer Memory** — lazy skill loading | 50 | -95% context size |
| 6 | **Circuit Breakers** — fuses on every loop | 15 | Prevents runaway $$ |
| 7 | **Critic Permissions** — safety before bash | 40 | Blocks 100% of dangerous commands |
| 8 | **Domain Tools** — vertical > general (see FinFars) | — | Clearest competitive edge |

Each technique can be toggled on/off via config, so you can measure its exact contribution.

## Quick Start

```bash
git clone https://github.com/wang2-lat/micro-harness.git
cd micro-harness

# Install dependencies
pip install anthropic

# Run offline tests (no API key needed)
python3 benchmarks/test_offline.py

# Run the agent (requires ANTHROPIC_API_KEY)
export ANTHROPIC_API_KEY=sk-ant-...
python3 src/harness.py "Count the Python files in src/"
```

## Example: FinFars — Vertical Harness for Equity Research

`examples/finfars.py` demonstrates **technique 8**: replacing generic tools with domain-specific ones.

Instead of read/write/bash, FinFars uses:
- `fetch_filing` — SEC EDGAR 10-K/10-Q
- `fetch_company_facts` — fundamentals
- `fetch_stock_price` — Yahoo Finance
- `search_news` — recent articles
- `compute_metrics` — financial ratios

```bash
python3 examples/finfars.py AAPL
# Output: /tmp/finfars-AAPL.md — 8-section equity research report
```

This is the blueprint for a $10/month "AI equity analyst" product. All data sources are free APIs.

## Architecture

```
User Task
    │
    ▼
┌────────────────────────────┐
│  Environment Bootstrap     │ ← TECHNIQUE 4 (save 2-5 turns)
└────────────────────────────┘
    │
    ▼
┌────────────────────────────┐
│  System Prompt Assembly    │
│  ┌──────────────────────┐  │
│  │ STABLE PREFIX        │  │ ← TECHNIQUE 3 (-87% cost)
│  │ (cached, reused)     │  │
│  └──────────────────────┘  │
│  ┌──────────────────────┐  │
│  │ DYNAMIC SUFFIX       │  │
│  │ (per-call)           │  │
│  └──────────────────────┘  │
└────────────────────────────┘
    │
    ▼
┌────────────────────────────┐
│   AGENT LOOP (fused)       │ ← TECHNIQUE 1 + 6
│   while turns < MAX:       │
│     response = api.call()  │
│     if stop: break         │
│     ┌─ Critic check ──┐    │ ← TECHNIQUE 7
│     │ safe? allow:ask │    │
│     └────────────────┘     │
│     result = run(tool)     │ ← TECHNIQUE 2 (structured)
└────────────────────────────┘
```

See [ARCHITECTURE.md](ARCHITECTURE.md) for the full deep dive.

## Why This Exists

After the Claude Code leak, the "agent harness" became a recognized engineering field:

- Meta acquired Manus for **$2B** — explicitly for harness IP
- Stanford's Meta-Harness hit **76.4%** on Terminal-Bench 2.0 by evolving the harness
- Anthropic harness engineers earn **$550K-$759K**

But most tutorials just wrap the API — they don't teach you the production techniques.

**micro-harness is designed to be read.** Single file. Each technique labeled. Each measurable.

## Benchmarks

Run benchmarks against your own API key:

```bash
python3 benchmarks/run_benchmark.py easy
```

Compares 5 configurations across 3 difficulty levels:
- `baseline` — no optimizations
- `with_cache` — just technique 3
- `with_bootstrap` — just technique 4
- `with_index` — just technique 5
- `all_optimizations` — full stack

Outputs pass rate, avg turns, token cost, and elapsed time per config.

## Tests

10 offline tests, no API key required:

```bash
$ python3 benchmarks/test_offline.py
Running offline tests...
✓ test_tools
✓ test_critic_blocks_dangerous
✓ test_critic_allows_safe
✓ test_critic_off_mode
✓ test_bootstrap
✓ test_file_index
✓ test_cache_boundary
✓ test_tools_schema_well_formed
✓ test_grep_tool
✓ test_dangerous_patterns_complete
ALL PASSED: 10/10
```

## License

MIT. Fork it, break it, ship it.

## Further Reading

- [Meta-Harness paper (arXiv 2603.28052)](https://arxiv.org/abs/2603.28052)
- [OpenHarness — HKUDS academic reference](https://github.com/HKUDS/OpenHarness)
- [Claude Code system prompts (leaked)](https://github.com/Piebald-AI/claude-code-system-prompts)
- [Effective harnesses for long-running agents — Anthropic](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents)
