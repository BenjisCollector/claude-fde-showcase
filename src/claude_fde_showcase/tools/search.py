"""Keyword search over a local documents directory.

This is a real, dependency-free retrieval implementation. Documents are loaded
from a directory of ``.md`` / ``.txt`` files, tokenised, and ranked against a
query using TF-IDF cosine similarity computed from scratch with the standard
library only. No vector database, no network, no model call -- which makes the
results deterministic and unit-testable.

A Forward Deployed Engineer would swap ``DocStore`` for a managed vector store
(or the customer's existing search index) behind the same ``search_docs``
interface; the MCP tool and every caller stay unchanged.
"""

from __future__ import annotations

import math
import re
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

# The default corpus lives at <repo>/docs. Resolve it relative to this file so
# the tool works regardless of the current working directory.
_DEFAULT_DOCS_DIR = Path(__file__).resolve().parents[3] / "docs"

_TOKEN_RE = re.compile(r"[a-z0-9]+")


def _tokenize(text: str) -> list[str]:
    """Lowercase the text and split it into alphanumeric tokens."""
    return _TOKEN_RE.findall(text.lower())


@dataclass
class Document:
    """A single indexed document."""

    id: str
    text: str
    term_freq: Counter = field(default_factory=Counter)

    @classmethod
    def from_text(cls, doc_id: str, text: str) -> "Document":
        return cls(id=doc_id, text=text, term_freq=Counter(_tokenize(text)))


@dataclass
class DocStore:
    """An in-memory TF-IDF index over a set of documents.

    Build it from a directory (:meth:`from_dir`) or from an explicit mapping
    (:meth:`from_mapping`), then call :meth:`search`.
    """

    documents: list[Document] = field(default_factory=list)
    _idf: dict[str, float] = field(default_factory=dict, init=False)

    def __post_init__(self) -> None:
        self._recompute_idf()

    # -- construction ---------------------------------------------------------
    @classmethod
    def from_mapping(cls, mapping: dict[str, str]) -> "DocStore":
        return cls(documents=[Document.from_text(k, v) for k, v in mapping.items()])

    @classmethod
    def from_dir(cls, directory: str | Path | None = None) -> "DocStore":
        """Load every ``.md`` / ``.txt`` file in ``directory`` into the store.

        Missing directories yield an empty store rather than raising, so the
        tool degrades gracefully if the corpus has not been provisioned yet.
        """
        path = Path(directory) if directory is not None else _DEFAULT_DOCS_DIR
        docs: list[Document] = []
        if path.is_dir():
            for file in sorted(path.iterdir()):
                if file.suffix.lower() in {".md", ".txt"} and file.is_file():
                    docs.append(Document.from_text(file.stem, file.read_text(encoding="utf-8")))
        return cls(documents=docs)

    # -- indexing -------------------------------------------------------------
    def _recompute_idf(self) -> None:
        n = len(self.documents)
        self._idf = {}
        if n == 0:
            return
        doc_count: Counter = Counter()
        for doc in self.documents:
            for term in doc.term_freq:
                doc_count[term] += 1
        # Smoothed inverse document frequency.
        for term, df in doc_count.items():
            self._idf[term] = math.log((1 + n) / (1 + df)) + 1.0

    def _vector(self, term_freq: Counter) -> dict[str, float]:
        return {term: tf * self._idf.get(term, 0.0) for term, tf in term_freq.items()}

    @staticmethod
    def _cosine(a: dict[str, float], b: dict[str, float]) -> float:
        if not a or not b:
            return 0.0
        common = set(a) & set(b)
        dot = sum(a[t] * b[t] for t in common)
        if dot == 0.0:
            return 0.0
        na = math.sqrt(sum(v * v for v in a.values()))
        nb = math.sqrt(sum(v * v for v in b.values()))
        if na == 0.0 or nb == 0.0:
            return 0.0
        return dot / (na * nb)

    # -- query ----------------------------------------------------------------
    def search(self, query: str, limit: int = 3) -> list[dict[str, object]]:
        """Return the ``limit`` best-matching documents for ``query``.

        Each hit is a dict with ``id``, ``score`` (rounded), and a ``snippet``
        of the document body. Results are sorted by descending score, then by
        id for a stable, deterministic order. Documents with zero similarity
        are excluded.
        """
        if limit <= 0:
            return []
        terms = _tokenize(query)
        if not terms or not self.documents:
            return []
        query_vec = self._vector(Counter(terms))
        scored: list[tuple[float, Document]] = []
        for doc in self.documents:
            score = self._cosine(query_vec, self._vector(doc.term_freq))
            if score > 0.0:
                scored.append((score, doc))
        scored.sort(key=lambda pair: (-pair[0], pair[1].id))
        return [
            {"id": doc.id, "score": round(score, 4), "snippet": _snippet(doc.text, terms)}
            for score, doc in scored[:limit]
        ]


def _snippet(text: str, terms: list[str], width: int = 200) -> str:
    """Return a short snippet centred on the first matching term, if any."""
    lowered = text.lower()
    pos = -1
    for term in terms:
        found = lowered.find(term)
        if found != -1 and (pos == -1 or found < pos):
            pos = found
    flat = " ".join(text.split())
    if pos == -1:
        return flat[:width].strip()
    # Re-find the position in the whitespace-collapsed string for a clean cut.
    start = max(0, pos - width // 2)
    snippet = flat[start : start + width].strip()
    prefix = "..." if start > 0 else ""
    suffix = "..." if start + width < len(flat) else ""
    return f"{prefix}{snippet}{suffix}"


# A module-level default store loaded from the repo's docs directory. Loaded
# lazily so importing this module never touches the filesystem unexpectedly.
_default_store: DocStore | None = None


def _get_default_store() -> DocStore:
    global _default_store
    if _default_store is None:
        _default_store = DocStore.from_dir()
    return _default_store


def search_docs(query: str, limit: int = 3) -> list[dict[str, object]]:
    """Search the repository's local docs corpus for ``query``.

    Thin convenience wrapper over the default :class:`DocStore`. Returns a list
    of ``{"id", "score", "snippet"}`` hits, best match first.
    """
    return _get_default_store().search(query, limit)
