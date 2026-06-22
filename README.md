# claude-fde-showcase

Demonstrates: Forward Deployed Engineer / Applied AI (MCP servers, sub-agents, agent skills, Claude integration)

**Status: early scaffold (work in progress).**

A minimal, honest skeleton showing the building blocks an FDE assembles when
shipping production apps with Claude. Every component runs offline with
deterministic placeholder logic — there are no benchmarks, no results, and no
client data here.

## What's in here

| Component | Path | What it is |
| --- | --- | --- |
| MCP server | `src/claude_fde_showcase/mcp_server/server.py` | Official `mcp` SDK (FastMCP) server exposing two tools: `search_docs_tool` and `summarise_tool`. |
| Sub-agents | `subagents/orchestrator.py` | An orchestrator that routes tasks to specialised sub-agent functions. |
| Agent skill | `agent_skills/doc_summariser/` | A `SKILL.md` capability description plus a small Python helper. |
| Tests | `tests/test_smoke.py` | Smoke tests over the deterministic core logic. |

## What works today

- The two MCP tools are registered and the server runs over stdio.
- The pure-logic helpers (`search_docs`, `summarise`, `summarise_document`)
  import and run without any network access.
- The orchestrator routes tasks to sub-agents and aggregates results.
- The smoke test suite passes.

## Quickstart

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

# Run the smoke tests
pytest

# Run the sub-agent demo
python -m subagents.orchestrator

# Run the agent-skill helper
python agent_skills/doc_summariser/helper.py

# Launch the MCP server over stdio
claude-fde-mcp
```

## Next steps

- Replace the deterministic stubs with real Claude calls (Anthropic SDK).
- Back `search_docs` with a real vector store instead of the in-memory corpus.
- Add an Anthropic-API-driven sub-agent that plans multi-step tasks.
- Wire the agent skill into the MCP server as a discoverable tool.
- Add CI (lint + tests) and packaging for distribution.

## License

MIT — see [LICENSE](LICENSE).
