"""Deterministic patient replies — skip OpenAI for predictable turns."""

from __future__ import annotations

import re
from typing import Optional

from app.agent_intent import (
    agent_expects_reply,
    is_dob_question,
    is_hold_or_connecting,
    is_intent_question,
    is_name_verification,
)
from app.scenarios import Scenario
from app.state import CallState, Turn

DEFAULT_SPOKEN_DOB = "March fourteenth, nineteen eighty-eight."
WRONG_SPOKEN_DOB = "March fourth, nineteen eighty-eight."


def patient_first_name(scenario: Scenario) -> str:
    match = re.search(r"You are (\w+)", scenario.patient_profile)
    return match.group(1) if match else "Maria"


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower().strip())


def is_confirmation_statement(text: str) -> bool:
    if is_name_verification(text) or is_dob_question(text) or is_intent_question(text):
        return False
    lower = text.lower()
    markers = (
        "doesn't match",
        "does not match",
        "for demo",
        "i'll accept",
        "i will accept",
        "i've got that",
        "i have got that",
        "got that noted",
        "noted",
        "understood",
        "thank you for confirming",
        "thanks for confirming",
        "that works",
        "sounds good",
        "perfect",
        "great, i",
        "okay, i have",
        "i have your",
    )
    return any(m in lower for m in markers)


def is_yes_no_question(text: str) -> bool:
    if "?" not in text:
        return False
    lower = text.lower()
    # Open questions that need substantive answers, not yes/no.
    if any(
        p in lower
        for p in (
            "what kind",
            "what type",
            "what can",
            "what would",
            "what is the",
            "what's the",
            "how can",
            "how may",
            "tell me",
            "describe",
            "when ",
            "where ",
            "why ",
            "which provider",
            "which doctor",
            "name of the provider",
            "preferred provider",
            "main reason",
        )
    ):
        return False
    patterns = (
        "is that correct",
        "is that right",
        "is that okay",
        "does that work",
        "would you like",
        "do you want",
        "can you confirm",
        "should i",
        "is this okay",
        "would that work",
        "shall i",
    )
    return any(p in lower for p in patterns)


def is_repeat_name_request(text: str, state: CallState) -> bool:
    if not state.answered_name:
        return False
    lower = text.lower()
    # After goal is introduced, only explicit re-verify prompts — not keyword false positives.
    if state.goal_introduced:
        return any(
            p in lower
            for p in (
                "repeat your name",
                "spell your name",
                "name again",
                "say your name again",
                "confirm your name",
                "verify your name",
            )
        )
    if is_name_verification(text) and state.identity_verified:
        return True
    return any(
        p in lower
        for p in (
            "repeat your name",
            "spell your name",
            "name again",
            "say your name again",
        )
    )


def is_repeat_dob_request(text: str, state: CallState) -> bool:
    if not state.answered_dob:
        return False
    lower = text.lower()
    if state.goal_introduced:
        return any(
            p in lower
            for p in (
                "repeat your date of birth",
                "date of birth again",
                "birthday again",
                "say your birthday again",
                "confirm your birth",
                "verify your birth",
            )
        )
    if is_dob_question(text) and state.identity_verified:
        return True
    return any(
        p in lower
        for p in (
            "repeat your date of birth",
            "date of birth again",
            "birthday again",
            "say your birthday again",
        )
    )


def is_anything_else_question(text: str) -> bool:
    lower = text.lower()
    return any(
        p in lower
        for p in (
            "anything else",
            "help you with anything else",
            "assist you with anything else",
            "need anything else",
        )
    )


def is_closing_statement(text: str) -> bool:
    lower = text.lower()
    return any(
        p in lower
        for p in (
            "goodbye",
            "good bye",
            "have a great day",
            "have a good day",
            "thanks for calling",
            "thank you for calling",
        )
    )


def is_simple_statement(text: str) -> bool:
    if agent_expects_reply(text):
        return False
    if is_hold_or_connecting(text) or is_confirmation_statement(text):
        return False
    lower = text.lower()
    working = (
        "let me check",
        "checking",
        "looking that up",
        "pulling up",
        "one moment",
        "give me a",
    )
    if any(w in lower for w in working):
        return True
    return len(text.split()) >= 3


def last_patient_reply(transcript: list[Turn]) -> Optional[str]:
    for turn in reversed(transcript):
        if turn.speaker == "patient_bot":
            return turn.text
    return None


def is_repeated_agent_prompt(state: CallState, agent_text: str) -> bool:
    if not state.last_agent_text:
        return False
    return _normalize(agent_text) == _normalize(state.last_agent_text)


def try_scripted_reply(
    scenario: Scenario, state: CallState, agent_text: str
) -> Optional[tuple[str, str]]:
    """Return (spoken_reply, route_reason) for predictable turns, or None for LLM."""
    first_name = patient_first_name(scenario)

    if is_confirmation_statement(agent_text):
        return "Okay.", "confirmation"

    if is_repeat_name_request(agent_text, state):
        return f"Yeah, this is {first_name}.", "repeat_name"

    if is_repeat_dob_request(agent_text, state):
        dob = WRONG_SPOKEN_DOB if scenario.id == "wrong_dob_correction" else DEFAULT_SPOKEN_DOB
        return dob, "repeat_dob"

    if is_yes_no_question(agent_text):
        lower = agent_text.lower()
        if any(n in lower for n in ("don't", "do not", "not ", "cancel", "no ")):
            return "No.", "yes_no_no"
        return "Yeah.", "yes_no_yes"

    if is_anything_else_question(agent_text):
        if state.goal_introduced:
            return "No, that's all. Thanks.", "anything_else"
        return "Not yet.", "anything_else_pre_goal"

    if is_closing_statement(agent_text):
        return "Thanks, goodbye.", "closing"

    if is_repeated_agent_prompt(state, agent_text):
        prior = last_patient_reply(state.turns)
        if prior:
            return prior, "repeated_question"

    if is_simple_statement(agent_text):
        return "Okay.", "simple_acknowledgment"

    return None
