"""
Benchmark the voice response pipeline: scripted vs OpenAI paths.

Usage:
    python -m app.profile_pipeline
    python -m app.profile_pipeline --iterations 5
"""

from __future__ import annotations

import argparse
import statistics
import time
from dataclasses import dataclass, field
from typing import Callable

from app.llm import (
    LIVE_SYSTEM_PROMPT,
    SYSTEM_PROMPT,
    format_conversation,
    patient_reply,
)
from app.profiling import clear_profiler, count_message_tokens, start_profiler
from app.scenarios import get_scenario
from app.state import CallState, Turn


@dataclass
class BenchCase:
    name: str
    path_label: str
    build_state: Callable[[], CallState]
    agent_text: str
    expect_openai: bool = False


@dataclass
class BenchResult:
    case: str
    path: str
    total_ms: float
    spans: dict[str, float] = field(default_factory=dict)
    metadata: dict = field(default_factory=dict)


def _base_state() -> CallState:
    return CallState(call_sid="bench", scenario_id="schedule_basic")


def _verified_pre_goal_state() -> CallState:
    state = _base_state()
    state.answered_name = True
    state.answered_dob = True
    state.identity_verified = True
    state.goal_introduced = False
    state.turns = [
        Turn("pgai_agent", "This call may be recorded for quality and training purposes."),
        Turn("pgai_agent", "Am I speaking with Maria?"),
        Turn("patient_bot", "Yeah, this is Maria."),
        Turn("pgai_agent", "Please tell me your date of birth."),
        Turn("patient_bot", "March fourteenth, nineteen eighty-eight."),
    ]
    return state


def _post_goal_state(turn_count: int = 6) -> CallState:
    state = _verified_pre_goal_state()
    state.goal_introduced = True
    state.turns.extend(
        [
            Turn("pgai_agent", "What can I help you with today?"),
            Turn("patient_bot", "Hi, I'd like to schedule an appointment for next week."),
            Turn("pgai_agent", "What kind of visit do you need?"),
            Turn("patient_bot", "A routine check-up with my primary care doctor."),
            Turn("pgai_agent", "Let me check for openings next week."),
            Turn("patient_bot", "Okay."),
        ]
    )
    state.turn_count = turn_count
    return state


def _name_answered_state() -> CallState:
    state = _base_state()
    state.answered_name = True
    return state


BENCH_CASES = [
    BenchCase(
        name="silent_disclosure",
        path_label="scripted_silent",
        build_state=_base_state,
        agent_text="This call may be recorded for quality and training purposes.",
    ),
    BenchCase(
        name="scripted_name",
        path_label="scripted_name",
        build_state=_base_state,
        agent_text="Am I speaking with Maria?",
    ),
    BenchCase(
        name="scripted_dob",
        path_label="scripted_dob",
        build_state=_name_answered_state,
        agent_text="Please tell me your date of birth.",
    ),
    BenchCase(
        name="scripted_opening_line",
        path_label="scripted_opening",
        build_state=_verified_pre_goal_state,
        agent_text="What can I help you with today?",
    ),
    BenchCase(
        name="openai_pre_goal",
        path_label="openai_pre_goal",
        build_state=_verified_pre_goal_state,
        agent_text="The birthday doesn't match our records, but I'll accept it for demo.",
        expect_openai=True,
    ),
    BenchCase(
        name="openai_patient_reply_early",
        path_label="openai_patient_reply",
        build_state=lambda: _post_goal_state(2),
        agent_text="What kind of visit do you need?",
        expect_openai=True,
    ),
    BenchCase(
        name="openai_patient_reply_mid",
        path_label="openai_patient_reply",
        build_state=lambda: _post_goal_state(6),
        agent_text="Let me check for openings next week.",
        expect_openai=True,
    ),
]


def run_case(case: BenchCase) -> BenchResult:
    scenario = get_scenario("schedule_basic")
    state = case.build_state()

    profiler = start_profiler("bench", case.agent_text)
    try:
        t0 = time.perf_counter()
        patient_reply(scenario, state, case.agent_text)
        total_ms = (time.perf_counter() - t0) * 1000
        profiler.spans["total_request"] = total_ms
        if profiler.response_path == "unknown":
            profiler.set_path(case.path_label)
        return BenchResult(
            case=case.name,
            path=profiler.response_path,
            total_ms=total_ms,
            spans=dict(profiler.spans),
            metadata=dict(profiler.metadata),
        )
    finally:
        clear_profiler()


def token_analysis() -> dict:
    scenario = get_scenario("schedule_basic")
    samples = {}

    onboarding_prompt = f"""
You are {scenario.patient_profile}
The healthcare agent just said: "Can you spell your last name?"

Reply as the patient on the phone. Rules:
- Answer ONLY what was asked using fake profile details if needed.
- Do NOT mention appointments, refills, scheduling, or your reason for calling yet.
- One short sentence. Return ONLY spoken words.
""".strip()
    samples["onboarding_fallback"] = count_message_tokens(
        [{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": onboarding_prompt}]
    )

    pre_goal_transcript = _verified_pre_goal_state().turns
    pre_goal_convo = format_conversation(pre_goal_transcript)
    pre_goal_prompt = f"""
You are {scenario.patient_profile}
Identity verification is already complete. Do NOT re-introduce your name or date of birth
unless the agent explicitly asks you to repeat or confirm them as a new question.

The healthcare agent just said: "The birthday doesn't match our records."

Recent conversation:
{pre_goal_convo}

Reply naturally in one short sentence. Do NOT state your reason for calling yet unless asked.
Return ONLY spoken words.
""".strip()
    samples["pre_goal"] = count_message_tokens(
        [{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": pre_goal_prompt}]
    )
    samples["pre_goal"]["conversation_turns"] = len(pre_goal_transcript)

    post_goal_transcript = _post_goal_state(6).turns
    post_goal_convo = format_conversation(post_goal_transcript)
    patient_prompt = f"""
Patient: {scenario.patient_profile}
Goal: {scenario.goal}
Edge case: {scenario.edge_case}
Key facts: Name Maria, DOB 03/14/1988.

Recent conversation:
{post_goal_convo}

Write the patient's next spoken reply.
""".strip()
    samples["patient_reply"] = count_message_tokens(
        [{"role": "system", "content": LIVE_SYSTEM_PROMPT}, {"role": "user", "content": patient_prompt}]
    )
    samples["patient_reply"]["conversation_turns"] = len(post_goal_transcript)
    samples["patient_reply"]["conversation_turns_in_prompt"] = min(len(post_goal_transcript), 12)

    return samples


def summarize(results: list[BenchResult]) -> dict:
    scripted = [r for r in results if r.path.startswith("scripted")]
    openai = [r for r in results if r.path.startswith("openai")]

    def avg_ms(items: list[BenchResult], key: str = "total_ms") -> float:
        if not items:
            return 0.0
        if key == "total_ms":
            vals = [r.total_ms for r in items]
        else:
            vals = [r.spans.get(key, 0) for r in items]
        return statistics.mean(vals)

    def p95_ms(items: list[BenchResult]) -> float:
        if not items:
            return 0.0
        vals = sorted(r.total_ms for r in items)
        idx = int(len(vals) * 0.95) - 1
        return vals[max(0, idx)]

    summary = {
        "scripted_avg_ms": avg_ms(scripted),
        "openai_avg_ms": avg_ms(openai),
        "openai_p95_ms": p95_ms(openai),
        "openai_api_avg_ms": avg_ms(openai, "openai_api_call"),
        "prompt_construction_avg_ms": avg_ms(openai, "prompt_construction"),
        "response_parsing_avg_ms": avg_ms(openai, "response_parsing"),
    }

    print("\n=== LATENCY SUMMARY (ms) ===")
    print(f"Scripted path avg total: {summary['scripted_avg_ms']:.2f} ms  (n={len(scripted)})")
    print(f"OpenAI path avg total:   {summary['openai_avg_ms']:.2f} ms  (n={len(openai)})")
    print(f"OpenAI path p95 total:   {summary['openai_p95_ms']:.2f} ms")
    if openai:
        print(f"  └─ openai_api_call avg: {summary['openai_api_avg_ms']:.2f} ms")
        print(f"  └─ prompt_construction avg: {summary['prompt_construction_avg_ms']:.2f} ms")
        print(f"  └─ response_parsing avg: {summary['response_parsing_avg_ms']:.2f} ms")

    print("\n=== PER-CASE BREAKDOWN ===")
    for r in results:
        span_str = ", ".join(f"{k}={v:.1f}" for k, v in sorted(r.spans.items()))
        usage = r.metadata.get("openai_usage", {})
        token_info = ""
        if usage:
            token_info = f"tokens={usage.get('prompt_tokens')}+{usage.get('completion_tokens')}"
        print(f"  {r.case:30s} path={r.path:22s} total={r.total_ms:7.1f}ms  [{span_str}]  {token_info}")

    print("\n=== ESTIMATED INPUT TOKENS PER OPENAI PATH ===")
    tokens = token_analysis()
    for path, data in tokens.items():
        print(
            f"  {path}: ~{data['total_input_tokens_est']} tokens "
            f"(system={data['system_tokens_est']}, user={data['user_tokens_est']})"
        )
    return summary


def main():
    parser = argparse.ArgumentParser(description="Profile voice response pipeline latency")
    parser.add_argument("--iterations", type=int, default=3, help="Runs per OpenAI case")
    args = parser.parse_args()

    results: list[BenchResult] = []

    for case in BENCH_CASES:
        runs = args.iterations if case.expect_openai else 1
        for _ in range(runs):
            results.append(run_case(case))
            time.sleep(0.2)

    summarize(results)


if __name__ == "__main__":
    main()
