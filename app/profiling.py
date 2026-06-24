"""Request-level timing instrumentation for the voice response pipeline."""

from __future__ import annotations

import json
import time
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass, field
from typing import Any, Iterator, Optional

_current_profiler: ContextVar[Optional["RequestProfiler"]] = ContextVar(
    "current_profiler", default=None
)

RECENT_REPORTS: list[dict[str, Any]] = []
MAX_RECENT_REPORTS = 50


@dataclass
class RequestProfiler:
    """Collects millisecond spans for one webhook request."""

    call_sid: str
    agent_text: str = ""
    response_path: str = "unknown"
    spans: dict[str, float] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    @contextmanager
    def span(self, name: str) -> Iterator[None]:
        start = time.perf_counter()
        try:
            yield
        finally:
            elapsed_ms = (time.perf_counter() - start) * 1000
            self.spans[name] = self.spans.get(name, 0.0) + elapsed_ms

    def set_path(self, path: str) -> None:
        self.response_path = path

    def set_meta(self, key: str, value: Any) -> None:
        self.metadata[key] = value

    def total_ms(self) -> float:
        return self.spans.get("total_request", 0.0)

    def to_dict(self) -> dict[str, Any]:
        return {
            "call_sid": self.call_sid,
            "agent_text_preview": self.agent_text[:80],
            "response_path": self.response_path,
            "spans_ms": {k: round(v, 2) for k, v in sorted(self.spans.items())},
            "metadata": self.metadata,
            "total_ms": round(self.total_ms(), 2),
        }

    def log(self) -> None:
        payload = self.to_dict()
        RECENT_REPORTS.append(payload)
        if len(RECENT_REPORTS) > MAX_RECENT_REPORTS:
            del RECENT_REPORTS[:-MAX_RECENT_REPORTS]
        print(f"[PROFILE] {json.dumps(payload, default=str)}")

    def log_route(self) -> None:
        """Human-readable route decision for live call debugging."""
        route_type = self.metadata.get("route_type", "unknown")
        reason = self.metadata.get("route_reason", self.response_path)
        openai_ms = self.spans.get("openai_api_call", 0.0)
        identity = self.metadata.get("identity_verified", "?")
        goal = self.metadata.get("goal_introduced", "?")
        print(
            f"[ROUTE] type={route_type} path={self.response_path} reason={reason} "
            f"identity_verified={identity} goal_introduced={goal} "
            f"total_ms={self.total_ms():.1f} openai_ms={openai_ms:.1f}"
        )


def get_profiler() -> Optional[RequestProfiler]:
    return _current_profiler.get()


def start_profiler(call_sid: str, agent_text: str = "") -> RequestProfiler:
    profiler = RequestProfiler(call_sid=call_sid, agent_text=agent_text)
    _current_profiler.set(profiler)
    return profiler


def clear_profiler() -> None:
    _current_profiler.set(None)


def estimate_tokens(text: str) -> int:
    """Rough token estimate when usage metadata is unavailable (~4 chars/token)."""
    return max(1, len(text) // 4)


def count_message_tokens(messages: list[dict[str, str]]) -> dict[str, int]:
    system = sum(estimate_tokens(m["content"]) for m in messages if m["role"] == "system")
    user = sum(estimate_tokens(m["content"]) for m in messages if m["role"] == "user")
    return {
        "system_tokens_est": system,
        "user_tokens_est": user,
        "total_input_tokens_est": system + user,
    }
