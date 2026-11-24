# Eval-Driven AI Engineering: Designing, Testing & Deploying Reliable Agents on Google Cloud with Antigravity & ADK

Complete Google Cloud hands-on workshop kit (8-step participant codelab, runnable ADK evaluation suite, Cloud Build CI gate, and Cloud Run / Vertex AI Agent Engine deployment scripts).

## Workshop Assets

| Asset | Location | Purpose |
| :--- | :--- | :--- |
| **Participant 8-Step Codelab** | `CODELAB.md` | Hands-on guide from Vertex AI ADC setup (`Red -> Green`) through `cloudbuild.yaml` & `adk deploy cloud_run --trace_to_cloud` |
| **Antigravity Customizations** | `AGENTS.md` + `.agents/skills/adk-eval/` | Enforces Eval-First invariants, keyless Vertex AI ADC, and eval-gated deploys |
| **Google Cloud CI/CD & Deploy** | `cloudbuild.yaml` + `deploy/deploy_cloud_run.sh` | 3-stage Cloud Build gate (`unittest` -> `pytest AgentEvaluator` -> `adk deploy cloud_run`) + Agent Engine option |
| **Runnable ADK Agent & Evals** | `refund_ops_agent/` + `evals/` + `tests/` | Includes `agent_v0_buggy.py` (**RED**) and hardened `agent.py` (**GREEN**), golden trajectories, Judge rubrics, User Simulation & `pytest` |

## Quick Start (Clone & Verify in 60 Seconds)

```bash
git clone https://github.com/estherirawati/eval-driven-adk-workshop.git
cd eval-driven-adk-workshop
chmod +x deploy/deploy_cloud_run.sh .agents/skills/adk-eval/scripts/run_eval_gate.sh stage_ctl.sh

# 1. Observe the RED phase failure on the naive 'vibe-coded' v0 agent:
python3 scripts/local_eval_harness.py --mode buggy

# 2. Run the GREEN evaluation gate (uses Vertex AI when GOOGLE_GENAI_USE_VERTEXAI=TRUE, or instant offline verifier):
./.agents/skills/adk-eval/scripts/run_eval_gate.sh
```
