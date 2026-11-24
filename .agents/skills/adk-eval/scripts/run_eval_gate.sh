#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSHOP_ROOT="$(cd "${SCRIPT_DIR}/../../../.." && pwd)"
cd "${WORKSHOP_ROOT}"

AGENT_MODE="${1:-auto}"

echo "================================================================"
echo "  Eval-Driven AI Engineering Gate (Antigravity + ADK + GCP)"
echo "  Workspace : ${WORKSHOP_ROOT}"
echo "  Target    : ${AGENT_MODE}"
echo "================================================================"

echo ""
echo "[1/3] Running fast deterministic tool & schema unit checks..."
python3 -m unittest discover -s tests -p "test_tools_unit.py" -v

HAS_VERTEX_ADC="false"
if [[ "${GOOGLE_GENAI_USE_VERTEXAI:-}" == "TRUE" && -n "${GOOGLE_CLOUD_PROJECT:-}" ]]; then
  HAS_VERTEX_ADC="true"
fi

echo ""
if command -v adk >/dev/null 2>&1 && [[ "${HAS_VERTEX_ADC}" == "true" || -n "${GOOGLE_API_KEY:-}" ]]; then
  if [[ "${HAS_VERTEX_ADC}" == "true" ]]; then
    echo "[2/3] Running live ADK evaluation via Google Cloud Vertex AI (${GOOGLE_CLOUD_PROJECT} / ${GOOGLE_CLOUD_LOCATION:-us-central1})..."
  else
    echo "[2/3] Running live ADK evaluation via Gemini API..."
  fi
  adk eval refund_ops_agent evals/core_trajectory.evalset.json \
    --config_file_path evals/test_config.json \
    --print_detailed_results

  echo ""
  echo "[3/3] Running pytest CI gate (AgentEvaluator, num_runs=2)..."
  python3 -m pytest tests/test_agent_eval.py -v
else
  echo "[2/3] Live Vertex AI ADC / 'adk' CLI not active in current shell."
  echo "      Running deterministic offline ADK EvalSet & Trajectory Verifier..."
  python3 scripts/local_eval_harness.py --mode "${AGENT_MODE}"
  echo ""
  echo "TIP: Authenticate with Google Cloud Vertex AI ('gcloud auth application-default login',"
  echo "     export GOOGLE_GENAI_USE_VERTEXAI=TRUE GOOGLE_CLOUD_PROJECT=...) and install"
  echo "     'pip install \"google-adk[eval]\" pytest' to run live Vertex AI Judge & Cloud Run gates."
fi
