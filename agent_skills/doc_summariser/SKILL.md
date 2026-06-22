---
name: doc-summariser
description: Condense a document into a short, length-bounded summary. Use when a user provides a block of text and asks for a brief, deterministic summary or a one-line gist.
---

# Doc Summariser

A small example agent skill that demonstrates the SKILL.md + helper-code pattern.

## Capability

Given a block of text, produce a length-bounded summary. The current
implementation is deterministic (word-count truncation) so it runs offline and
is easy to test. In a production skill this helper would call Claude.

## When to use

- The user pastes a long passage and asks for the "gist" or a "short version".
- An orchestrator needs a quick, cheap summary step before deeper processing.

## How to use

Call the helper directly:

```python
from agent_skills.doc_summariser.helper import summarise_document

summarise_document("...long text...", max_words=15)
```

## Inputs

- `text` (str): the document to summarise.
- `max_words` (int, default 25): upper bound on summary length.

## Output

- A string: the original text if already short enough, otherwise the first
  `max_words` words followed by an ellipsis.

## Status

Early scaffold. Deterministic placeholder logic only — no model call yet.
