from dataclasses import dataclass, field
from typing import Dict, List, Optional

@dataclass
class Turn:
    speaker: str
    text: str

@dataclass
class CallState:
    call_sid: str
    scenario_id: str
    turns: List[Turn] = field(default_factory=list)
    turn_count: int = 0
    completed: bool = False
    answered_name: bool = False
    answered_dob: bool = False
    identity_verified: bool = False
    goal_introduced: bool = False
    force_llm_reply: bool = False
    last_agent_text: Optional[str] = None
    bridge_phrase_index: int = 0

CALLS: Dict[str, CallState] = {}
