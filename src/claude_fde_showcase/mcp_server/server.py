"""MCP server exposing the FDE showcase tools.

This uses the official ``mcp`` Python SDK (FastMCP), but imports it **lazily**
inside :func:`build_server` so that all of the underlying tool logic can be
imported and unit-tested without the ``mcp`` package installed. That separation
is deliberate: the pure logic lives in :mod:`claude_fde_showcase.tools`, runs
offline, and is what CI exercises; the MCP layer is a thin transport wrapper
over it.

Run it over stdio with::

    python -m claude_fde_showcase.mcp_server.server
    # or, once installed:
    claude-fde-mcp

Tools exposed:

* ``search_docs``  -- TF-IDF keyword search over the local ``docs/`` corpus.
* ``summarise``    -- deterministic extractive summarisation.
* ``calculate``    -- safe arithmetic expression evaluation.
* ``list_docs``    -- list the document ids available to ``search_docs``.
"""

from __future__ import annotations

# Re-export the pure logic so existing callers (and tests) can import directly
# from this module without pulling in the mcp transport.
from claude_fde_showcase.tools.calculator import CalculatorError, calculate
from claude_fde_showcase.tools.search import DocStore, search_docs
from claude_fde_showcase.tools.summarise import summarise, summarise_extractive

__all__ = [
    "build_server",
    "main",
    "calculate",
    "CalculatorError",
    "search_docs",
    "summarise",
    "summarise_extractive",
    "DocStore",
    "list_docs",
]


def list_docs() -> list[str]:
    """Return the ids of every document available to ``search_docs``."""
    return [doc.id for doc in DocStore.from_dir().documents]


def build_server():
    """Construct and return the FastMCP server with all tools registered.

    The ``mcp`` import is deliberately local so importing this module (for the
    re-exported pure logic) never requires the SDK to be installed.
    """
    from mcp.server.fastmcp import FastMCP

    server = FastMCP("claude-fde-showcase")

    @server.tool()
    def search_docs_tool(query: str, limit: int = 3) -> list[dict[str, object]]:
        """Search the local docs corpus and return the best-matching documents.

        Args:
            query: natural-language or keyword query.
            limit: maximum number of hits to return (default 3).
        """
        return search_docs(query, limit)

    @server.tool()
    def summarise_tool(text: str, max_sentences: int = 3) -> str:
        """Produce a deterministic extractive summary of ``text``.

        Args:
            text: the document to summarise.
            max_sentences: upper bound on summary length in sentences.
        """
        return summarise_extractive(text, max_sentences)

    @server.tool()
    def calculate_tool(expression: str) -> float:
        """Safely evaluate an arithmetic expression and return the number.

        Supports + - * / // % **, parentheses, and common math functions
        (sqrt, log, sin, ...). Never executes arbitrary code.
        """
        return calculate(expression)

    @server.tool()
    def list_docs_tool() -> list[str]:
        """List the ids of all documents searchable via search_docs."""
        return list_docs()

    return server


def main() -> None:
    build_server().run()


if __name__ == "__main__":
    main()
