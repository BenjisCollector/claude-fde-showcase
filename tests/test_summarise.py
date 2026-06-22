"""Tests for the extractive summariser and the legacy word-bounded gist."""

import pytest

from claude_fde_showcase.tools.summarise import (
    split_sentences,
    summarise,
    summarise_extractive,
)

_PARAGRAPH = (
    "Cats are small carnivorous mammals. "
    "Cats are kept as pets all over the world. "
    "Photosynthesis is how plants make energy from sunlight. "
    "Cats hunt small prey such as mice and birds. "
    "The weather today is mild."
)


def test_split_sentences_counts_correctly():
    assert len(split_sentences(_PARAGRAPH)) == 5


def test_split_sentences_empty():
    assert split_sentences("   ") == []


def test_extractive_returns_requested_count():
    out = summarise_extractive(_PARAGRAPH, max_sentences=2)
    # Two sentences -> exactly one terminal punctuation per sentence (2 total).
    assert out.count(".") == 2


def test_extractive_prefers_salient_sentences():
    # "Cats" is the dominant term; cat sentences should be chosen over the
    # off-topic photosynthesis / weather sentences.
    out = summarise_extractive(_PARAGRAPH, max_sentences=2).lower()
    assert "cats" in out
    assert "photosynthesis" not in out
    assert "weather" not in out


def test_extractive_preserves_original_order():
    out = summarise_extractive(_PARAGRAPH, max_sentences=3)
    # The first cat sentence must appear before the hunting sentence.
    assert out.index("small carnivorous") < out.index("hunt small prey")


def test_extractive_passthrough_when_short():
    text = "Only one sentence here."
    assert summarise_extractive(text, max_sentences=3) == text


def test_extractive_zero_sentences_is_empty():
    assert summarise_extractive(_PARAGRAPH, max_sentences=0) == ""


def test_extractive_negative_raises():
    with pytest.raises(ValueError):
        summarise_extractive(_PARAGRAPH, max_sentences=-1)


def test_extractive_is_deterministic():
    a = summarise_extractive(_PARAGRAPH, max_sentences=2)
    b = summarise_extractive(_PARAGRAPH, max_sentences=2)
    assert a == b


def test_gist_truncates():
    assert summarise("one two three four five", max_words=2) == "one two ..."


def test_gist_passthrough_when_short():
    assert summarise("short text", max_words=10) == "short text"


def test_gist_negative_raises():
    with pytest.raises(ValueError):
        summarise("x y z", max_words=-1)
