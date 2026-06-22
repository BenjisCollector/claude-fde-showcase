"""Pure, dependency-free tool logic for the FDE showcase.

Every function in this package runs offline with no model call and no third-party
runtime dependency (the ``mcp`` package is only needed to *serve* these as MCP
tools, not to execute the logic). This is what lets the test suite and CI run
green without any API keys, network access, or the mcp SDK installed.
"""

from claude_fde_showcase.tools.calculator import CalculatorError, calculate
from claude_fde_showcase.tools.search import DocStore, search_docs
from claude_fde_showcase.tools.summarise import summarise, summarise_extractive

__all__ = [
    "calculate",
    "CalculatorError",
    "DocStore",
    "search_docs",
    "summarise",
    "summarise_extractive",
]
