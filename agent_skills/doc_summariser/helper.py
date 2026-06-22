"""Helper code for the doc-summariser agent skill.

This skill packages a real, deterministic extractive summariser. It delegates
to :func:`claude_fde_showcase.tools.summarise.summarise_extractive` so the skill
and the MCP ``summarise`` tool share one implementation -- a single source of
truth an FDE can later upgrade (e.g. to a Claude abstractive summary) in one
place.

Run it standalone with ``python agent_skills/doc_summariser/helper.py``.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Make the package importable when this file is run directly as a script,
# without requiring an editable install.
_SRC = Path(__file__).resolve().parents[2] / "src"
if _SRC.is_dir() and str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from claude_fde_showcase.tools.summarise import (  # noqa: E402
    summarise,
    summarise_extractive,
)


def summarise_document(text: str, max_sentences: int = 3) -> str:
    """Summarise ``text`` down to its ``max_sentences`` most salient sentences.

    Thin, stable wrapper over the shared extractive summariser so callers of the
    skill have a clear, documented entry point.
    """
    return summarise_extractive(text, max_sentences)


def gist(text: str, max_words: int = 20) -> str:
    """Return a one-line, word-bounded gist of ``text``.

    Useful when a caller wants a single short line rather than whole sentences.
    """
    return summarise(text, max_words)


if __name__ == "__main__":
    sample = (
        "Forward Deployed Engineers embed with customers to design, build, and ship "
        "production AI systems. They turn frontier model capabilities into concrete "
        "business outcomes. The work is end to end, from scoping to a hardened, "
        "reliable system. It also requires translating business goals into precise "
        "technical specifications."
    )
    print("Extractive summary:")
    print(summarise_document(sample, max_sentences=2))
    print()
    print("One-line gist:")
    print(gist(sample, max_words=12))
