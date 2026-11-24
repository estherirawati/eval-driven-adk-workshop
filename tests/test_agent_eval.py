"""CI/CD Pytest Regression Gate powered by Google ADK `AgentEvaluator`.

Run locally or in GitHub Actions / Cloud Build:
    export GOOGLE_API_KEY="your-gemini-api-key"
    pytest tests/test_agent_eval.py -v
"""

from __future__ import annotations

from pathlib import Path

import pytest

from refund_ops_agent.agent import reset_mock_data

WORKSHOP_ROOT = Path(__file__).resolve().parent.parent
EVALSET_PATH = WORKSHOP_ROOT / "evals" / "core_trajectory.evalset.json"


@pytest.mark.asyncio
async def test_refund_ops_core_trajectories() -> None:
    """Enforce 100% tool trajectory & groundedness compliance across 2 runs."""
    AgentEvaluator = pytest.importorskip(
        "google.adk.evaluation.agent_evaluator",
        reason="Install 'google-adk[eval]' to execute live AgentEvaluator LLM runs.",
    ).AgentEvaluator

    reset_mock_data()

    await AgentEvaluator.evaluate(
        agent_module="refund_ops_agent",
        eval_dataset_file_path_or_dir=str(EVALSET_PATH),
        num_runs=2,
    )
