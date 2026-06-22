"""Helper code for the doc-summariser agent skill.

Deterministic, offline placeholder logic so the skill is runnable as a
scaffold. Swap ``summarise_document`` for a Claude call to make it real.
"""

from __future__ import annotations


def summarise_document(text: str, max_words: int = 25) -> str:
    """Return a length-bounded summary of ``text``.

    If the text is already within ``max_words``, it is returned unchanged
    (stripped). Otherwise it is truncated to ``max_words`` words with a
    trailing ellipsis.
    """
    if max_words < 0:
        raise ValueError("max_words must be non-negative")
    words = text.split()
    if len(words) <= max_words:
        return text.strip()
    return " ".join(words[:max_words]).rstrip(".,;:") + " ..."


if __name__ == "__main__":
    sample = (
        "Forward Deployed Engineers embed with customers to design, build, and "
        "ship production AI systems, turning frontier model capabilities into "
        "concrete business outcomes."
    )
    print(summarise_document(sample, max_words=10))
