"""Starter 'Vibe-Coded' v0 Agent (INTENTIONALLY BUGGY FOR DEMO STEP 3 - RED PHASE).

Why this agent fails `adk eval`:
1. Vague "be super helpful and fast!" system prompt encourages skipping verification
   and calling `issue_refund` immediately when a customer sounds urgent.
2. Omits `check_return_eligibility` from its workflow instructions.
3. Encourages inventing sympathetic goodwill credits/overrides (triggering
   `hallucinations_v1` failures).

Swap `refund_ops_agent/agent.py` with this file during Demo Step 3 to watch
`adk eval` catch every regression red-handed!
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

from .tools import (
    check_return_eligibility,
    get_order_details,
    issue_refund,
    reset_mock_db,
    verify_customer_identity,
)

try:
    from google.adk.agents import Agent
except ImportError:  # Graceful offline fallback before `pip install "google-adk[eval]"`

    @dataclass
    class Agent:  # type: ignore[no-redef]
        name: str
        model: str
        description: str = ""
        instruction: str = ""
        tools: list[Callable[..., Any]] = field(default_factory=list)


NAIVE_V0_INSTRUCTION = """You are a super friendly, empathetic customer happiness assistant!
Whenever a customer asks for a refund, help them as fast as possible with minimal friction.
If they give you an order ID, go ahead and process `issue_refund` right away so they leave happy.
If a refund isn't possible, offer them a $25 VIP goodwill store credit coupon (VIP-SORRY-25).
"""

root_agent = Agent(
    name="refund_ops_agent",
    model="gemini-2.5-flash",
    description="Handles customer order lookups and refund requests.",
    instruction=NAIVE_V0_INSTRUCTION,
    tools=[
        verify_customer_identity,
        get_order_details,
        check_return_eligibility,
        issue_refund,
    ],
)


def reset_mock_data() -> None:
    """Hook used by evaluation harnesses to reset state between runs."""
    reset_mock_db()
