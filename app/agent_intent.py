"""Keyword detection for PGAI agent utterances."""

from __future__ import annotations


def is_name_verification(text: str) -> bool:
    lower = text.lower()
    if any(
        phrase in lower
        for phrase in (
            "speaking with",
            "speak with",
            "am i speaking",
            "may i speak",
            "verify your name",
            "confirm your name",
            "is that you",
        )
    ):
        return True
    # Bare "is this" matches scheduling questions ("is this for a routine checkup?").
    if any(
        skip in lower
        for skip in (
            "is this for",
            "is this a ",
            "is this an ",
            "is this the ",
            "is this your ",
        )
    ):
        return False
    if "is this" in lower:
        return True
    return False


def is_dob_question(text: str) -> bool:
    lower = text.lower()
    if "doesn't match" in lower or "does not match" in lower:
        return False
    return any(
        phrase in lower
        for phrase in (
            "date of birth",
            "birthday",
            "when were you born",
            "verify your birth",
            "confirm your birth",
        )
    ) or ("born" in lower and "?" in text)


def is_intent_question(text: str) -> bool:
    lower = text.lower()
    return any(
        phrase in lower
        for phrase in (
            "how can i help",
            "how may i help",
            "how can i assist",
            "how may i assist",
            "what can i do for you",
            "what can i help you with",
            "how can i help you today",
            "how may i help you today",
            "what brings you",
            "reason for your call",
            "what can i help with",
            "how may i help you",
        )
    )


def is_disclosure_only(text: str) -> bool:
    if is_name_verification(text) or is_dob_question(text) or is_intent_question(text):
        return False
    lower = text.lower()
    markers = (
        "recorded",
        "quality and training",
        "para español",
        "oprima dos",
        "monitor",
    )
    return any(marker in lower for marker in markers)


def is_hold_or_connecting(text: str) -> bool:
    if is_name_verification(text) or is_dob_question(text) or is_intent_question(text):
        return False
    lower = text.lower()
    markers = (
        "please wait",
        "connecting you",
        "connecting",
        "one moment",
        "one second",
        "just a second",
        "just a moment",
        "hold on",
        "transferring",
        "while i connect",
        "putting you through",
        "bear with me",
        "give me a moment",
    )
    return any(marker in lower for marker in markers)


def agent_expects_reply(text: str) -> bool:
    if is_name_verification(text) or is_dob_question(text) or is_intent_question(text):
        return True
    return "?" in text
