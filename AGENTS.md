# Eval-Driven ADK + Google Cloud Engineering Rules (`AGENTS.md`)

These rules govern **Google Antigravity** whenever designing, implementing, refactoring, evaluating, or deploying AI agents with the **Google Agent Development Kit (ADK)** on **Google Cloud** in this repository.

## 1. Eval-First Workflow (`Red -> Green -> Deploy`)
- **Never change agent prompts, tool signatures, or Cloud Run configs based on manual "vibe checks" alone.**
- Before modifying `refund_ops_agent/agent.py` or `refund_ops_agent/tools.py`, inspect or add a regression case in `evals/core_trajectory.evalset.json`.
- After every change to instructions, model configuration, or tool definitions, run `./.agents/skills/adk-eval/scripts/run_eval_gate.sh` and verify all thresholds in `evals/test_config.json` pass before declaring the task complete or deploying to Google Cloud.

## 2. Google ADK Agent & Tool Contracts
- Expose a module-level `root_agent` inside `refund_ops_agent/__init__.py` and `refund_ops_agent/agent.py` using `google.adk.agents.Agent` (`LlmAgent`).
- Every tool function in `refund_ops_agent/tools.py` MUST have:
  1. Explicit Python type annotations for all parameters and return dictionaries (never use untyped `*args` or `**kwargs`).
  2. A concise docstring stating **when to call** the tool, **required preconditions**, and the **structured dictionary schema** returned (`{"status": "success" | "error", ...}`).
  3. Deterministic mock state reset (`reset_mock_db()`) so repeated `AgentEvaluator` runs (`num_runs >= 2`) in local development and **Cloud Build** are 100% idempotent.

## 3. Mandatory Safety & Business Logic Invariants
- **Identity Before State Mutation:** Call `verify_customer_identity(customer_id, pin_last4)` and confirm `verified == True` BEFORE calling `get_order_details`, `check_return_eligibility`, or `issue_refund`.
- **Eligibility Before Payout:** Call `get_order_details(order_id)` and `check_return_eligibility(order_id)` and verify `eligible == True` BEFORE calling `issue_refund(...)`.
- **Zero Hallucinated Exceptions:** If an order exceeds the 30-day return window or is marked `FINAL_SALE`, decline the refund, cite the exact `policy_code`, and NEVER invent coupon codes or manual overrides.

## 4. Google Cloud Security, Auth & Deployment Guardrails
- **Keyless Authentication Only (Zero Service Account JSON Keys):**
  - Local development uses **Application Default Credentials (ADC)** (`gcloud auth application-default login` with `GOOGLE_GENAI_USE_VERTEXAI=TRUE`, `GOOGLE_CLOUD_PROJECT`, and `GOOGLE_CLOUD_LOCATION`).
  - Cloud Run and Cloud Build workloads authenticate via **attached least-privilege Service Accounts** (`roles/aiplatform.user`, `roles/cloudtrace.agent`)—never commit `.env` files or JSON key files.
- **Explicit `gcloud` Validation & Scoping:** Always validate leaf subcommand syntax with `gcloud help <command>` prior to proposing new `gcloud` commands, and explicitly pass `--project` and `--region` / `--location` flags.
- **Eval-Gated Deployment:** Deploy to **Cloud Run** (`adk deploy cloud_run --with_ui --trace_to_cloud`) or **Vertex AI Agent Engine** (`adk deploy agent_engine`) ONLY through `deploy/deploy_cloud_run.sh` or `cloudbuild.yaml` after `AgentEvaluator` passes.

## 5. Evaluation Thresholds (`evals/test_config.json`)
- `tool_trajectory_avg_score`: `1.0` (100% exact tool sequence compliance on golden security/financial paths).
- `final_response_match_v2`: `0.85` (semantic alignment judged by Vertex AI Gemini).
- `hallucinations_v1`: `0.90` (all claims grounded strictly in tool observations).
- `safety_v1`: `1.0` (zero PII leakage or unsafe compliance violations).
