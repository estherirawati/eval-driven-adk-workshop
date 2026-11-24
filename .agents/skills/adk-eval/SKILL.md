---
name: adk-eval
description: >-
  Run, diagnose, and enforce Eval-Driven Development and Google Cloud deployment gates
  for Google ADK agents. Use whenever creating or updating evalset.json files, configuring
  Vertex AI LLM-as-a-Judge rubrics, running adk eval / pytest AgentEvaluator gates, or
  deploying verified agents to Cloud Run or Vertex AI Agent Engine.
---

# Google ADK + Vertex AI Evaluation & Cloud Gate Skill (`adk-eval`)

Activate this skill whenever building, refactoring, evaluating, or deploying an ADK agent so every change follows the **Red -> Green -> Deploy** lifecycle on Google Cloud.

## 1. Standard Eval-Driven Loop

1. **Define or Extend Golden Cases (`RED`)**:
   - Add expected `user_content`, `intermediate_data.tool_uses` (exact ordered tool calls + args), and `final_response` to `evals/core_trajectory.evalset.json`.
2. **Execute the Evaluation Gate**:
   ```bash
   ./.agents/skills/adk-eval/scripts/run_eval_gate.sh
   ```
3. **Diagnose Failures by Dimension**:
   - **Low `tool_trajectory_avg_score` (`< 1.0`)**: Inspect `--print_detailed_results` actual vs. expected `tool_uses`. Tighten tool docstrings in `tools.py` and explicit step ordering in `agent.py` `instruction`.
   - **Low `final_response_match_v2` or `rubric_based_final_response_quality_v1` (`< 0.85`)**: Ensure the agent cites the exact `order_id`, refund amount/status, and `policy_code`.
   - **Low `hallucinations_v1` (`< 0.90`)**: Remove speculative apologies or invented policy workarounds; instruct the agent to cite *only* fields returned in tool dictionaries.
4. **Deploy to Google Cloud Only After `GREEN`**:
   - Local Eval-Gated Deploy to **Cloud Run** (with OpenTelemetry **Cloud Trace**):
     ```bash
     ./deploy/deploy_cloud_run.sh cloud_run
     ```
   - Managed **Vertex AI Agent Engine** Deploy:
     ```bash
     ./deploy/deploy_cloud_run.sh agent_engine
     ```
   - Automated **Google Cloud Build** CI/CD Gate: see `cloudbuild.yaml`.

## 2. Key ADK & Vertex AI Commands

```bash
# Authenticate locally with keyless Vertex AI ADC
gcloud auth login
gcloud auth application-default login
export GOOGLE_GENAI_USE_VERTEXAI=TRUE
export GOOGLE_CLOUD_PROJECT="YOUR_PROJECT_ID"
export GOOGLE_CLOUD_LOCATION="us-central1"

# Run deterministic + Vertex AI semantic evaluation on golden evalset
adk eval refund_ops_agent evals/core_trajectory.evalset.json \
  --config_file_path evals/test_config.json \
  --print_detailed_results

# Run qualitative Vertex AI LLM-as-a-Judge rubric evaluation (gemini-2.5-pro)
adk eval refund_ops_agent evals/core_trajectory.evalset.json \
  --config_file_path evals/rubric_eval_config.json \
  --print_detailed_results

# Deploy GREEN-verified agent to Cloud Run with Cloud Trace enabled
adk deploy cloud_run \
  --project="${GOOGLE_CLOUD_PROJECT}" \
  --region="${GOOGLE_CLOUD_LOCATION}" \
  --service_name="refund-ops-agent" \
  --with_ui \
  --trace_to_cloud \
  refund_ops_agent
```
