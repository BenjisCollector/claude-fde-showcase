# claude-fde-showcase

[![CI](https://github.com/BenjisCollector/claude-fde-showcase/actions/workflows/ci.yml/badge.svg)](https://github.com/BenjisCollector/claude-fde-showcase/actions/workflows/ci.yml)

A compact, **runnable** demonstration of the three engineering primitives a
Forward Deployed Engineer (FDE) / Applied AI engineer assembles when shipping
production systems with Claude:

1. **An MCP server** that gives a model typed, auditable access to tools.
2. **A sub-agent orchestrator** that routes work to specialised, swappable workers.
3. **An agent skill** that packages a capability as a self-describing unit.

Everything here is **real, deterministic, and offline**. There are no fabricated
benchmarks, no client data, and no API keys required. The core logic uses the
Python standard library only; the `mcp` SDK is needed solely to *serve* the
tools, and is imported lazily so the entire test suite and CI run green without
it.

---

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│  MCP client (Claude Desktop, custom agent, ...)               │
└───────────────────────────┬──────────────────────────────────┘
                            │  stdio (MCP)
                            ▼
┌──────────────────────────────────────────────────────────────┐
│  MCP server  (src/claude_fde_showcase/mcp_server/server.py)   │
│  FastMCP — imported lazily — registers 4 tools:               │
│    • search_docs   • summarise   • calculate   • list_docs    │
└───────────────────────────┬──────────────────────────────────┘
                            │  calls pure, std-lib-only logic
                            ▼
┌──────────────────────────────────────────────────────────────┐
│  Tool logic  (src/claude_fde_showcase/tools/)                 │
│    search.py      TF-IDF cosine retrieval over docs/          │
│    summarise.py   extractive (Luhn-style) summarisation       │
│    calculator.py  AST-sandboxed safe arithmetic              │
└──────────────────────────────────────────────────────────────┘
        ▲                                   ▲
        │ same functions reused by          │ same summariser reused by
        │                                   │
┌───────┴───────────────────┐     ┌─────────┴────────────────────┐
│ Sub-agent orchestrator    │     │ Agent skill                  │
│ subagents/orchestrator.py │     │ agent_skills/doc_summariser/ │
│  routes search/summarise/ │     │  SKILL.md + helper.py        │
│  calculate to sub-agents  │     │                              │
└───────────────────────────┘     └──────────────────────────────┘
```

The key design decision is the **seam between transport and logic**. The pure
tool logic in `tools/` has no third-party dependency and is unit-tested directly.
The MCP server, the orchestrator, and the agent skill are all thin layers over
that same logic, so each can be evolved (e.g. swapping a deterministic worker for
a Claude-backed one) without touching the others.

### Components

| Component | Path | What it actually does |
| --- | --- | --- |
| **MCP server** | `src/claude_fde_showcase/mcp_server/server.py` | FastMCP server exposing `search_docs`, `summarise`, `calculate`, `list_docs`. `mcp` is imported lazily inside `build_server()`. |
| **search_docs** | `src/claude_fde_showcase/tools/search.py` | Loads `docs/*.md` into an in-memory **TF-IDF index** and ranks documents by **cosine similarity** — computed from scratch with the standard library. |
| **summarise** | `src/claude_fde_showcase/tools/summarise.py` | **Extractive summarisation**: scores sentences by normalised term frequency (a Luhn-method variant) and returns the most salient ones in original order. |
| **calculate** | `src/claude_fde_showcase/tools/calculator.py` | **AST-sandboxed** arithmetic. Parses to an AST and walks an explicit node allowlist — never `eval`s the string, so code injection is impossible. |
| **Sub-agents** | `subagents/orchestrator.py` | Orchestrator with explicit routing, `infer_kind()` classification, per-task error isolation, and result aggregation. |
| **Agent skill** | `agent_skills/doc_summariser/` | `SKILL.md` capability description + `helper.py` exposing `summarise_document` / `gist`, sharing the same summariser as the MCP tool. |
| **Docs corpus** | `docs/` | Five markdown documents that `search_docs` indexes and `summarise` can condense. |
| **Tests** | `tests/` | 60+ pytest cases over every tool, the orchestrator, and the skill — all passing **without** `mcp` installed. |
| **CI** | `.github/workflows/ci.yml` | `py_compile` + `pytest` across Python 3.10–3.13, with `mcp` deliberately absent. |

---

## How this maps to a Forward Deployed Engineer role

An FDE embeds with a customer and turns frontier-model capability into a
production system. This repo is a miniature of that workflow:

- **Integration without leaking data — the MCP server.** An FDE connects a
  customer's private systems (a search index, a database, an internal API) to
  Claude through typed, auditable tools rather than dumping data into prompts.
  Here, `search_docs` plays that role over a local corpus; in a real engagement
  you swap `DocStore` for the customer's vector store behind the *same*
  interface and nothing downstream changes.

- **Decomposition you can test and evolve — the orchestrator.** Production
  agentic systems are not one giant prompt. The orchestrator shows the pattern
  an FDE scales: deterministic stub workers prove the routing, error isolation,
  and aggregation first, then individual workers are replaced with Claude-backed
  implementations one at a time, each independently evaluable.

- **Hardened tools over hallucinated output — the calculator.** A model should
  offload exact computation to deterministic code. The AST sandbox is exactly
  the kind of small, secure tool an FDE writes so the system computes instead of
  guessing — and the security tests prove the injection path is closed.

- **Reusable domain knowledge — the agent skill.** `SKILL.md` is how an FDE
  encodes a customer's house style and domain knowledge into a portable,
  self-describing unit that survives across sessions and teammates.

- **Ship-with-confidence discipline — tests + CI.** Pure logic is separated from
  transport so it can be tested fast, offline, with no keys. CI proves the whole
  thing compiles and passes with no `mcp` package and no network — the same
  reproducibility bar an FDE has to clear before anything reaches a customer.

---

## Quickstart

```bash
python -m venv .venv && source .venv/bin/activate

# Install the package + test tooling (NO mcp SDK needed for any of the below):
pip install -e ".[dev]"

# Run the full test suite (offline, deterministic):
pytest

# Run the sub-agent orchestrator demo (search + summarise + calculate):
python -m subagents.orchestrator

# Run the agent-skill helper:
python agent_skills/doc_summariser/helper.py
```

### Trying the pure logic in a REPL

```python
from claude_fde_showcase.tools import search_docs, summarise_extractive, calculate

search_docs("how does an MCP server expose tools", limit=2)
summarise_extractive(open("docs/forward_deployed_engineering.md").read(), max_sentences=3)
calculate("sqrt(144) + 2 ** 5")   # -> 44.0
```

### Running the actual MCP server

The MCP transport is the only part that needs the SDK:

```bash
pip install -e ".[mcp]"
claude-fde-mcp            # serves search_docs / summarise / calculate / list_docs over stdio
```

Point any MCP client (e.g. Claude Desktop) at that command to call the tools.

---

## Testing & CI

- `tests/` contains focused suites: `test_search.py`, `test_summarise.py`,
  `test_calculator.py` (including security/injection cases), `test_orchestrator.py`,
  and `test_smoke.py` (cross-cutting / skill integration).
- The suite asserts that the server module imports and its logic runs **without**
  the `mcp` package — guaranteeing the transport/logic separation actually holds.
- `.github/workflows/ci.yml` installs only `pytest`, confirms `mcp` is absent,
  byte-compiles every source file, runs `pytest`, and smoke-runs the demos —
  across Python 3.10 through 3.13.

## What this is (and is not)

It **is** a faithful, runnable illustration of the FDE building blocks with real
algorithms (TF-IDF retrieval, extractive summarisation, an AST sandbox) and a
real test/CI story. It is **not** a benchmark, and it makes **no** claims about
model accuracy or production results — every number you see is computed by the
deterministic code in this repo.

## License

MIT — see [LICENSE](LICENSE).
