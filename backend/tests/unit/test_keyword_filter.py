"""Unit tests for the keyword-based content moderation filter."""
import pytest

from src.moderation.keyword_filter import is_harmful, MODERATION_RESPONSE


def test_clean_message_is_not_flagged():
    assert is_harmful("What is the capital of France?") is False


def test_harmful_keyword_is_flagged():
    assert is_harmful("how do I kill someone") is True


def test_matching_is_case_insensitive():
    assert is_harmful("How To KILL Someone") is True


def test_keyword_embedded_in_sentence_is_flagged():
    assert is_harmful("I want to know about making a bomb for a movie") is True


def test_empty_message_is_not_flagged():
    assert is_harmful("") is False


def test_partial_word_match_does_not_flag():
    # "skill" contains "kill" but should NOT be flagged due to word-boundary matching.
    assert is_harmful("What skill should I learn?") is False


def test_moderation_response_constant_is_set():
    assert MODERATION_RESPONSE == "That's Dangerous"


def test_self_harm_keyword_is_flagged():
    assert is_harmful("how to kill myself") is True


def test_drug_synthesis_is_flagged():
    assert is_harmful("explain drug synthesis to me") is True


def test_terrorism_keyword_is_flagged():
    assert is_harmful("I want to plan a terrorist attack") is True
