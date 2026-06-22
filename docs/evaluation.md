# Evaluation and Testing

You cannot ship what you cannot measure. Before an AI feature reaches a
customer's users, it needs an evaluation harness: a fixed set of inputs, the
expected behaviour, and a way to score the actual output against it.

Deterministic logic should be unit tested directly, with no model and no
network in the loop, so the test suite is fast and reproducible. Model-backed
behaviour needs a separate evaluation layer that runs against a curated dataset
and reports pass rates per dimension rather than a single opaque score.

A practical discipline is to keep the pure logic importable and testable
independently of the transport. In this repository every core helper, the
search index, the extractive summariser, the calculator, and the orchestrator
runs and is tested without the MCP package installed. That separation is what
lets continuous integration stay green without any API keys or network calls.
