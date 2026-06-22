"""Deterministic extractive summarisation.

Rather than a naive word-count truncation, this picks the most representative
*sentences* from the text using a small, well-understood scoring scheme: each
sentence is scored by the sum of the frequencies of its (non-stopword) terms,
normalised by sentence length to avoid favouring long sentences. The top
sentences are then returned in their original document order so the summary
reads naturally.

This is a real, classic extractive-summarisation algorithm (a frequency-based
variant of the Luhn method), implemented with the standard library only. It is
deterministic, offline, and unit-testable -- and an obvious seam for an FDE to
later replace with a Claude-generated abstractive summary behind the same API.
"""

from __future__ import annotations

import re
from collections import Counter

# A compact English stopword list. Kept small and inline so the module stays
# dependency-free and the behaviour is fully visible.
_STOPWORDS = frozenset(
    """
    a an and are as at be by for from has have in is it its of on or that the to
    was were will with this these those then than they them their there here he
    she his her you your we our us i but not no so if into over under about
    """.split()
)

_SENTENCE_RE = re.compile(r"(?<=[.!?])\s+")
_WORD_RE = re.compile(r"[a-z0-9']+")


def split_sentences(text: str) -> list[str]:
    """Split ``text`` into sentences on terminal punctuation + whitespace."""
    cleaned = " ".join(text.split())
    if not cleaned:
        return []
    return [s.strip() for s in _SENTENCE_RE.split(cleaned) if s.strip()]


def _word_frequencies(sentences: list[str]) -> Counter:
    freq: Counter = Counter()
    for sentence in sentences:
        for word in _WORD_RE.findall(sentence.lower()):
            if word not in _STOPWORDS:
                freq[word] += 1
    return freq


def summarise_extractive(text: str, max_sentences: int = 3) -> str:
    """Return the ``max_sentences`` most salient sentences, in original order.

    If the text has at most ``max_sentences`` sentences it is returned as-is
    (whitespace-normalised). Raises ``ValueError`` for a negative bound.
    """
    if max_sentences < 0:
        raise ValueError("max_sentences must be non-negative")
    if max_sentences == 0:
        return ""
    sentences = split_sentences(text)
    if len(sentences) <= max_sentences:
        return " ".join(sentences)

    freq = _word_frequencies(sentences)
    if not freq:
        return " ".join(sentences[:max_sentences])

    def score(sentence: str) -> float:
        words = [w for w in _WORD_RE.findall(sentence.lower()) if w not in _STOPWORDS]
        if not words:
            return 0.0
        return sum(freq[w] for w in words) / len(words)

    # Rank by score (desc), breaking ties by original position for determinism.
    ranked = sorted(
        range(len(sentences)),
        key=lambda i: (-score(sentences[i]), i),
    )
    chosen = sorted(ranked[:max_sentences])
    return " ".join(sentences[i] for i in chosen)


def summarise(text: str, max_words: int = 25) -> str:
    """Length-bounded summary by word count (legacy, kept for compatibility).

    Returns the text unchanged (stripped) if already within ``max_words``,
    otherwise truncates to ``max_words`` words with a trailing ellipsis.
    """
    if max_words < 0:
        raise ValueError("max_words must be non-negative")
    words = text.split()
    if len(words) <= max_words:
        return text.strip()
    return " ".join(words[:max_words]).rstrip(".,;:") + " ..."
