"""Deterministic unit tests for RefundOps tools and ADK EvalSet JSON schemas."""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

WORKSHOP_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(WORKSHOP_ROOT))

from refund_ops_agent import agent, tools  # noqa: E402


class RefundOpsToolContractTests(unittest.TestCase):
    def setUp(self) -> None:
        tools.reset_mock_db()

    def test_blocks_refund_when_identity_unverified(self) -> None:
        result = tools.issue_refund("ORD-9001", reason="defective_audio")
        self.assertEqual(result["status"], "error")
        self.assertEqual(result["policy_violation"], "UNVERIFIED_IDENTITY")

    def test_happy_path_verified_and_within_30_days(self) -> None:
        auth = tools.verify_customer_identity("CUST-101", "4821")
        self.assertTrue(auth["verified"])

        elig = tools.check_return_eligibility("ORD-9001")
        self.assertTrue(elig["eligible"])
        self.assertEqual(elig["policy_code"], "WITHIN_30_DAY_WINDOW")

        refund = tools.issue_refund("ORD-9001", reason="defective_audio")
        self.assertEqual(refund["status"], "success")
        self.assertEqual(refund["refund_id"], "RFND-9001")
        self.assertEqual(refund["refunded_amount_usd"], 199.00)

        # Double-refund must be rejected deterministically
        second_attempt = tools.issue_refund("ORD-9001", reason="defective_audio")
        self.assertEqual(second_attempt["status"], "error")
        self.assertEqual(second_attempt["policy_violation"], "ALREADY_REFUNDED")

    def test_blocks_expired_45_day_order(self) -> None:
        tools.verify_customer_identity("CUST-101", "4821")
        elig = tools.check_return_eligibility("ORD-9002")
        self.assertFalse(elig["eligible"])
        self.assertEqual(elig["policy_code"], "RETURN_WINDOW_EXPIRED")

        refund = tools.issue_refund("ORD-9002", reason="changed_mind")
        self.assertEqual(refund["status"], "error")
        self.assertEqual(refund["policy_violation"], "RETURN_WINDOW_EXPIRED")

    def test_blocks_final_sale_gift_card(self) -> None:
        tools.verify_customer_identity("CUST-202", "9910")
        elig = tools.check_return_eligibility("ORD-9003")
        self.assertFalse(elig["eligible"])
        self.assertEqual(elig["policy_code"], "FINAL_SALE_EXCLUDED")

    def test_root_agent_exposes_four_typed_tools(self) -> None:
        self.assertEqual(agent.root_agent.name, "refund_ops_agent")
        self.assertEqual(len(agent.root_agent.tools), 4)

    def test_evalset_and_configs_are_valid_adk_schemas(self) -> None:
        evalset_path = WORKSHOP_ROOT / "evals" / "core_trajectory.evalset.json"
        evalset = json.loads(evalset_path.read_text(encoding="utf-8"))
        self.assertIn("eval_set_id", evalset)
        self.assertGreaterEqual(len(evalset["eval_cases"]), 3)
        for case in evalset["eval_cases"]:
            self.assertIn("eval_id", case)
            self.assertTrue(len(case["conversation"]) >= 1)
            turn = case["conversation"][0]
            self.assertIn("user_content", turn)
            self.assertIn("intermediate_data", turn)
            self.assertIn("tool_uses", turn["intermediate_data"])
            self.assertIn("final_response", turn)


if __name__ == "__main__":
    unittest.main()
