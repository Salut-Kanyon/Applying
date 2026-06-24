import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
from typing import Optional

from openai import OpenAI
from app import config
from app.agent_intent import (
    agent_expects_reply,
    is_disclosure_only,
    is_dob_question,
    is_hold_or_connecting,
    is_intent_question,
    is_name_verification,
)
from app.profiling import count_message_tokens, get_profiler
from app.scenarios import Scenario
from app.scripted import (
    DEFAULT_SPOKEN_DOB,
    WRONG_SPOKEN_DOB,
    is_confirmation_statement,
    patient_first_name,
    try_scripted_reply,
)
from app.state import CallState, Turn

client = OpenAI(api_key=config.OPENAI_API_KEY) if config.OPENAI_API_KEY else None
_llm_executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="openai")

SPEAKER_LABELS = {
    "patient_bot": "Patient",
    "pgai_agent": "Agent",
}

SPOKEN_LABEL_PREFIXES = (
    "patient_bot:",
    "pgai_agent:",
    "patient:",
    "agent:",
)

# Full prompt for transcript analysis only.
SYSTEM_PROMPT = """
You are controlling a voice bot that acts as a realistic patient calling a healthcare AI agent.
Your job is to have a natural phone conversation that tests the other agent.

Rules:
- Stay in character as the patient.
- Keep each response short, natural, and speakable: usually 1 sentence, max 2.
- Sound like a real person on the phone — calm, direct, not overly polite or scripted.
- Do not mention you are a bot, test, evaluator, transcript, or challenge.
- Actively steer toward the scenario goal.
- If the other agent asks for info, provide plausible info using fake details only.
- If the scenario is complete, politely end the call.
- Avoid long monologues, filler phrases, and exclamation marks.
- Prefer brief acknowledgments: "Okay.", "Sure.", "Got it." — not "Great, thank you!" or "Thank you so much."
- Never say "Sorry, I didn't catch that" or similar meta-phrases about hearing/audio.
- If the agent asks you to wait or is connecting/transferring, say nothing.

Output format:
- Return ONLY the words the patient would speak aloud.
- Never include speaker labels, prefixes, quotes, markdown, or role names.
""".strip()

LIVE_SYSTEM_PROMPT = """
You are a realistic patient on a healthcare phone call.
Stay in character. One short spoken sentence, max two.
Sound natural and calm — not overly polite.
Steer toward the scenario goal when appropriate.
Use only the fake profile details provided.
Return ONLY spoken words — no labels, quotes, or markdown.
""".strip()

BRIDGE_PHRASES = (
    "Sorry, one second.",
    "Let me think for a second.",
    "Yeah, so…",
)


def sanitize_spoken_text(text: str) -> str:
    """Strip label prefixes so Twilio TTS never speaks internal transcript markers."""
    cleaned = text.strip().replace("\n", " ")
    while cleaned:
        lower = cleaned.lower()
        matched = False
        for prefix in SPOKEN_LABEL_PREFIXES:
            if lower.startswith(prefix):
                cleaned = cleaned[len(prefix) :].strip()
                matched = True
                break
        if not matched:
            break
    if len(cleaned) >= 2 and cleaned[0] == cleaned[-1] and cleaned[0] in "\"'":
        cleaned = cleaned[1:-1].strip()
    return cleaned


VERBOSE_ACK_PHRASES = (
    "great, thank you",
    "great thank you",
    "thank you so much",
    "thanks so much",
    "perfect, thank you",
    "perfect thank you",
    "that's great, thank you",
    "that's great thank you",
    "wonderful, thank you",
    "i appreciate it",
    "thanks, i appreciate",
)


def polish_spoken_reply(text: str) -> str:
    """Shorten overly polite LLM filler; empty string means stay silent."""
    cleaned = sanitize_spoken_text(text)
    if not cleaned:
        return ""
    lower = cleaned.lower().strip().rstrip(".")
    for phrase in VERBOSE_ACK_PHRASES:
        if lower == phrase or lower.startswith(phrase):
            return "Okay."
    if lower in ("hello", "hello?"):
        return ""
    return cleaned


def finalize_reply(reply: Optional[str]) -> Optional[str]:
    if reply is None:
        return None
    polished = polish_spoken_reply(reply)
    return polished if polished else None


def format_conversation(transcript: list[Turn], max_turns: int = 6) -> str:
    lines = []
    for turn in transcript[-max_turns:]:
        label = SPEAKER_LABELS.get(turn.speaker, turn.speaker)
        lines.append(f"{label}: {turn.text}")
    return "\n".join(lines)


def _record_route(route_type: str, path: str, reason: str, state: Optional[CallState] = None) -> None:
    profiler = get_profiler()
    if not profiler:
        return
    profiler.set_path(path)
    profiler.set_meta("route_type", route_type)
    profiler.set_meta("route_reason", reason)
    if state is not None:
        profiler.set_meta("identity_verified", state.identity_verified)
        profiler.set_meta("goal_introduced", state.goal_introduced)
        print(
            f"[ROUTE-DEBUG] path={path} reason={reason} "
            f"identity_verified={state.identity_verified} goal_introduced={state.goal_introduced} "
            f"agent_preview={profiler.agent_text[:60]!r}"
        )


def _live_chat_completion(label: str, **kwargs) -> Optional[str]:
    """
    Live phone LLM call with timeout. Returns None if OpenAI exceeds the deadline.
    """
    if not client:
        return None

    profiler = get_profiler()
    messages = kwargs.get("messages", [])
    token_est = count_message_tokens(messages)
    timeout = config.OPENAI_LIVE_TIMEOUT_SEC

    if profiler:
        profiler.set_meta("prompt_tokens_est", token_est["total_input_tokens_est"])
        profiler.set_meta("openai_model", kwargs.get("model"))

    api_start = time.perf_counter()
    future = _llm_executor.submit(client.chat.completions.create, **kwargs)
    try:
        res = future.result(timeout=timeout)
    except FuturesTimeoutError:
        api_ms = (time.perf_counter() - api_start) * 1000
        if profiler:
            profiler.spans["openai_api_call"] = api_ms
            profiler.set_meta("openai_timed_out", True)
        print(
            f"OpenAI [{label}] TIMEOUT after {timeout:.1f}s model={kwargs.get('model')} "
            f"tokens_est={token_est}"
        )
        return None

    api_ms = (time.perf_counter() - api_start) * 1000
    usage = getattr(res, "usage", None)
    usage_dict = {}
    if usage:
        usage_dict = {
            "prompt_tokens": usage.prompt_tokens,
            "completion_tokens": usage.completion_tokens,
            "total_tokens": usage.total_tokens,
        }

    if profiler:
        profiler.spans["openai_api_call"] = api_ms
        if usage_dict:
            profiler.set_meta("openai_usage", usage_dict)

    print(
        f"OpenAI [{label}] latency: {api_ms / 1000:.2f}s model={kwargs.get('model')} "
        f"tokens={usage_dict or token_est}"
    )
    return res.choices[0].message.content or ""


def _timed_chat_completion(label: str, **kwargs) -> str:
    """Offline/analysis calls — no timeout, full system prompt allowed."""
    profiler = get_profiler()
    messages = kwargs.get("messages", [])
    token_est = count_message_tokens(messages)

    if profiler:
        profiler.set_meta("prompt_tokens_est", token_est["total_input_tokens_est"])
        profiler.set_meta("openai_model", kwargs.get("model"))

    api_start = time.perf_counter()
    res = client.chat.completions.create(**kwargs)
    api_ms = (time.perf_counter() - api_start) * 1000

    usage = getattr(res, "usage", None)
    usage_dict = {}
    if usage:
        usage_dict = {
            "prompt_tokens": usage.prompt_tokens,
            "completion_tokens": usage.completion_tokens,
            "total_tokens": usage.total_tokens,
        }

    if profiler:
        profiler.spans["openai_api_call"] = api_ms
        if usage_dict:
            profiler.set_meta("openai_usage", usage_dict)

    print(
        f"OpenAI [{label}] latency: {api_ms / 1000:.2f}s model={kwargs.get('model')} "
        f"tokens={usage_dict or token_est}"
    )
    return res.choices[0].message.content or ""


def _key_facts(scenario: Scenario) -> str:
    first = patient_first_name(scenario)
    return (
        f"Name: {first} (full name in profile). DOB: 03/14/1988. "
        f"Phone: 626-737-4463. Insurance: Blue Cross Blue Shield."
    )


def _call_state_summary(state: CallState) -> str:
    return (
        f"identity_verified={state.identity_verified}, "
        f"goal_introduced={state.goal_introduced}, turn={state.turn_count}"
    )


def bridge_phrase(state: CallState) -> str:
    phrase = BRIDGE_PHRASES[state.bridge_phrase_index % len(BRIDGE_PHRASES)]
    state.bridge_phrase_index += 1
    return phrase


def should_stay_silent(agent_text: str, state: CallState) -> bool:
    if is_disclosure_only(agent_text):
        return True
    if is_hold_or_connecting(agent_text):
        return True
    if is_confirmation_statement(agent_text):
        return False
    if not state.goal_introduced and not agent_expects_reply(agent_text):
        return True
    return False


def _maybe_complete_identity(state: CallState) -> None:
    if state.answered_name and state.answered_dob:
        state.identity_verified = True


def _apply_scripted(
    scenario: Scenario, state: CallState, agent_text: str
) -> Optional[str]:
    hit = try_scripted_reply(scenario, state, agent_text)
    if not hit:
        return None
    reply, reason = hit
    _record_route("scripted", f"scripted_{reason}", reason, state)
    return reply


def next_onboarding_reply(
    scenario: Scenario, state: CallState, agent_text: str, *, skip_scripted: bool = False
) -> Optional[str]:
    first_name = patient_first_name(scenario)

    if not state.answered_name and is_name_verification(agent_text):
        state.answered_name = True
        _maybe_complete_identity(state)
        _record_route("scripted", "scripted_name", "name_verification")
        return f"Yeah, this is {first_name}."

    if not state.answered_dob and is_dob_question(agent_text):
        state.answered_dob = True
        _maybe_complete_identity(state)
        _record_route("scripted", "scripted_dob", "dob_verification")
        if scenario.id == "wrong_dob_correction":
            return WRONG_SPOKEN_DOB
        return DEFAULT_SPOKEN_DOB

    if not skip_scripted:
        scripted = _apply_scripted(scenario, state, agent_text)
        if scripted:
            return scripted

    return _onboarding_llm_reply(scenario, state, agent_text)


def next_pre_goal_reply(
    scenario: Scenario, state: CallState, agent_text: str, *, skip_scripted: bool = False
) -> str:
    if is_intent_question(agent_text):
        state.goal_introduced = True
        _record_route("scripted", "scripted_opening", "intent_question", state)
        return sanitize_spoken_text(scenario.opening_line)

    if not skip_scripted:
        scripted = _apply_scripted(scenario, state, agent_text)
        if scripted:
            return scripted

    return _pre_goal_llm_reply(scenario, state, agent_text)


def _onboarding_llm_reply(scenario: Scenario, state: CallState, agent_text: str) -> str:
    if not client:
        _record_route("scripted", "scripted_fallback", "no_openai_key")
        return "Sure."

    prompt = f"""
Patient: {scenario.patient_profile}
Agent said: "{agent_text}"
State: pre-identity verification.
Answer only what was asked. Do not mention scheduling or your reason for calling yet.
""".strip()

    _record_route("pre_goal_llm", "openai_onboarding_fallback", "unrecognized_pre_identity")
    raw = _live_chat_completion(
        "onboarding_fallback",
        model=config.OPENAI_MODEL,
        messages=[
            {"role": "system", "content": LIVE_SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        temperature=0.4,
        max_tokens=config.OPENAI_LIVE_MAX_TOKENS,
    )
    if raw is None:
        state.force_llm_reply = True
        _record_route("scripted", "scripted_bridge", "openai_timeout_onboarding")
        return bridge_phrase(state)
    return sanitize_spoken_text(raw) or "Sure."


def _pre_goal_llm_reply(scenario: Scenario, state: CallState, agent_text: str) -> str:
    if not client:
        _record_route("scripted", "scripted_fallback", "no_openai_key")
        return "Sure."

    convo = format_conversation(state.turns, max_turns=config.LIVE_CONTEXT_TURNS)
    prompt = f"""
Patient: {scenario.patient_profile}
Goal (do not state yet unless asked): {scenario.goal}
Key facts: {_key_facts(scenario)}
State: {_call_state_summary(state)}

Agent said: "{agent_text}"

Recent conversation:
{convo}

Reply in one short sentence. Identity is verified — do not repeat name/DOB unless asked again.
""".strip()

    profiler = get_profiler()
    if profiler:
        profiler.set_meta("conversation_turns", len(state.turns))
        profiler.set_meta("conversation_turns_in_prompt", min(len(state.turns), config.LIVE_CONTEXT_TURNS))

    _record_route("pre_goal_llm", "openai_pre_goal", "pre_goal_needs_reasoning")
    raw = _live_chat_completion(
        "pre_goal",
        model=config.OPENAI_MODEL,
        messages=[
            {"role": "system", "content": LIVE_SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        temperature=0.4,
        max_tokens=config.OPENAI_LIVE_MAX_TOKENS,
    )
    if raw is None:
        state.force_llm_reply = True
        _record_route("scripted", "scripted_bridge", "openai_timeout_pre_goal")
        return bridge_phrase(state)
    return sanitize_spoken_text(raw) or "Sure."


def _patient_llm_reply(scenario: Scenario, state: CallState, agent_text: str) -> str:
    if not client:
        _record_route("scripted", "scripted_fallback", "no_openai_key")
        return "Could you help me with that, please?"

    convo = format_conversation(state.turns, max_turns=config.LIVE_CONTEXT_TURNS)
    prompt = f"""
Patient: {scenario.patient_profile}
Goal: {scenario.goal}
Edge case to test: {scenario.edge_case}
Key facts: {_key_facts(scenario)}
State: {_call_state_summary(state)}

Agent said: "{agent_text}"

Recent conversation:
{convo}

Write the patient's next spoken reply. If the goal is complete, say a short goodbye.
""".strip()

    profiler = get_profiler()
    if profiler:
        profiler.set_meta("conversation_turns", len(state.turns))
        profiler.set_meta("conversation_turns_in_prompt", min(len(state.turns), config.LIVE_CONTEXT_TURNS))

    _record_route("patient_reply_llm", "openai_patient_reply", "post_goal_needs_reasoning")
    raw = _live_chat_completion(
        "patient_reply",
        model=config.OPENAI_MODEL,
        messages=[
            {"role": "system", "content": LIVE_SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        temperature=0.4,
        max_tokens=config.OPENAI_LIVE_MAX_TOKENS,
    )
    if raw is None:
        state.force_llm_reply = True
        _record_route("scripted", "scripted_bridge", "openai_timeout_patient_reply")
        return bridge_phrase(state)
    return sanitize_spoken_text(raw) or "Could you help me with that?"


def _dispatch_llm(
    scenario: Scenario, state: CallState, agent_text: str, *, skip_scripted: bool = False
) -> Optional[str]:
    if not state.identity_verified:
        return next_onboarding_reply(scenario, state, agent_text, skip_scripted=skip_scripted)
    if not state.goal_introduced:
        return next_pre_goal_reply(scenario, state, agent_text, skip_scripted=skip_scripted)
    return _patient_llm_reply(scenario, state, agent_text)


def patient_reply(scenario: Scenario, state: CallState, agent_text: str) -> Optional[str]:
    profiler = get_profiler()
    if profiler:
        with profiler.span("route_decision"):
            silent = should_stay_silent(agent_text, state)
    else:
        silent = should_stay_silent(agent_text, state)

    if silent:
        _record_route("silent", "scripted_silent", "disclosure_hold_or_no_reply_expected", state)
        state.last_agent_text = agent_text
        return None

    force_llm = state.force_llm_reply
    if force_llm:
        state.force_llm_reply = False
        reply = _dispatch_llm(scenario, state, agent_text, skip_scripted=True)
        state.last_agent_text = agent_text
        if profiler:
            with profiler.span("finalize_reply"):
                return finalize_reply(reply)
        return finalize_reply(reply)

    # First-time name / DOB before generic scripted routing
    if not state.identity_verified:
        if not state.answered_name and is_name_verification(agent_text):
            state.answered_name = True
            _maybe_complete_identity(state)
            _record_route("scripted", "scripted_name", "name_verification", state)
            state.last_agent_text = agent_text
            return finalize_reply(f"Yeah, this is {patient_first_name(scenario)}.")
        if not state.answered_dob and is_dob_question(agent_text):
            state.answered_dob = True
            _maybe_complete_identity(state)
            _record_route("scripted", "scripted_dob", "dob_verification", state)
            dob = WRONG_SPOKEN_DOB if scenario.id == "wrong_dob_correction" else DEFAULT_SPOKEN_DOB
            state.last_agent_text = agent_text
            return finalize_reply(dob)

    if not state.goal_introduced and is_intent_question(agent_text):
        state.goal_introduced = True
        _record_route("scripted", "scripted_opening", "intent_question", state)
        state.last_agent_text = agent_text
        return finalize_reply(sanitize_spoken_text(scenario.opening_line))

    scripted = _apply_scripted(scenario, state, agent_text)
    if scripted is not None:
        state.last_agent_text = agent_text
        if profiler:
            with profiler.span("finalize_reply"):
                return finalize_reply(scripted)
        return finalize_reply(scripted)

    reply = _dispatch_llm(scenario, state, agent_text)
    state.last_agent_text = agent_text
    if profiler:
        with profiler.span("finalize_reply"):
            return finalize_reply(reply)
    return finalize_reply(reply)


def next_patient_reply(scenario: Scenario, transcript: list[Turn]) -> str:
    """Backward-compatible wrapper used by export/analysis tooling."""
    state = CallState(call_sid="legacy", scenario_id=scenario.id, turns=transcript, goal_introduced=True)
    agent_text = ""
    for turn in reversed(transcript):
        if turn.speaker == "pgai_agent":
            agent_text = turn.text
            break
    return _patient_llm_reply(scenario, state, agent_text)


def analyze_transcript(scenario: Scenario, transcript_text: str) -> str:
    if not client:
        return "OpenAI API key missing; manual analysis required."

    prompt = f"""
You are reviewing a transcript from a healthcare voice AI agent test.
Scenario: {scenario.title}
Goal: {scenario.goal}
Edge case: {scenario.edge_case}

Transcript:
{transcript_text}

Create a concise bug/quality report. Include:
- Summary
- Bugs or quality issues found, with severity High/Medium/Low
- Why each issue matters
- Evidence from the transcript
- Suggested expected behavior
If no bugs are found, say what the agent handled well and what should be tested next.
""".strip()

    return _timed_chat_completion(
        "analyze_transcript",
        model=config.OPENAI_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
    ).strip()
