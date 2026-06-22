---
name: doc-summariser
description: Condense a document into a short, faithful summary using deterministic extractive logic. Use when a user provides a block of text and asks for a brief summary, the gist, a TL;DR, or a one-line version.
---

# Doc Summariser

An agent skill that demonstrates the SKILL.md + helper-code pattern with a real,
runnable capability.

## Capability

Given a block of text, produce a faithful summary. Two modes are available:

- **Extractive summary** (`summarise_document`): selects the most salient whole
  sentences from the text using a frequency-based scoring scheme (a variant of
  the classic Luhn method) and returns them in their original order, so the
  summary reads naturally.
- **One-line gist** (`gist`): a word-bounded single line for when the caller
  wants the shortest possible version.

Both modes are deterministic and run fully offline, which makes the skill cheap,
reproducible, and easy to test. They share their implementation with the MCP
`summarise` tool, so there is one source of truth to upgrade later (for example,
to a Claude-generated abstractive summary).

## When to use

- The user pastes a long passage and asks for the "gist", "TL;DR", or a "short
  version".
- An orchestrator needs a quick, cheap summary step before deeper processing.

## How to use

```python
from agent_skills.doc_summariser.helper import summarise_document, gist

# Most salient sentences, original order:
summarise_document(long_text, max_sentences=3)

# A single short line:
gist(long_text, max_words=20)
```

Or run the skill directly to see both modes on a sample:

```bash
python agent_skills/doc_summariser/helper.py
```

## Inputs

- `text` (str): the document to summarise.
- `max_sentences` (int, default 3): upper bound on extractive summary length.
- `max_words` (int, default 20): upper bound on the one-line gist.

## Output

- `summarise_document`: a string containing the top sentences, joined and in
  original document order. If the text is already within the sentence bound it
  is returned (whitespace-normalised) unchanged.
- `gist`: a single short line; the original text if already short enough,
  otherwise the first `max_words` words followed by an ellipsis.

## Edge cases

- A negative bound raises `ValueError`.
- A bound of zero returns an empty string.
- Text with no scorable content falls back to the leading sentences.
