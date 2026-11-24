#!/usr/bin/env bash
# Eval-Gated ADK Deployment Script for Google Cloud Run / Vertex AI Agent Engine
#
# Enforces local evaluation pass BEFORE deploying the agent to Google Cloud,
# and configures Cloud Trace telemetry (--trace_to_cloud).

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSHOP_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${WORKSHOP_ROOT}"

PROJECT_ID="${GOOGLE_CLOUD_PROJECT:-}"
REGION="${GOOGLE_CLOUD_LOCATION:-us-central1}"
SERVICE_NAME="${SERVICE_NAME:-refund-ops-agent}"
DEPLOY_TARGET="${1:-cloud_run}"  # 'cloud_run' or 'agent_engine'

if [[ -z "${PROJECT_ID}" ]]; then
  echo "ERROR: GOOGLE_CLOUD_PROJECT is not set."
  echo "Authenticate with keyless ADC and set your project first:"
  echo "  gcloud auth login"
  echo "  gcloud auth application-default login"
  echo "  export GOOGLE_GENAI_USE_VERTEXAI=TRUE"
  echo "  export GOOGLE_CLOUD_PROJECT=\"your-gcp-project-id\""
  echo "  export GOOGLE_CLOUD_LOCATION=\"us-central1\""
  exit 1
fi

echo "==> [Gate 1/2] Verifying ADK Evaluation Suite passes before cloud deploy..."
./.agents/skills/adk-eval/scripts/run_eval_gate.sh hardened

echo ""
echo "==> [Gate 2/2] Deploying GREEN-verified RefundOps Agent to Google Cloud (${DEPLOY_TARGET})..."
if [[ "${DEPLOY_TARGET}" == "agent_engine" ]]; then
  STAGING_BUCKET="${STAGING_BUCKET:-gs://${PROJECT_ID}-adk-staging}"
  adk deploy agent_engine \
    --project="${PROJECT_ID}" \
    --region="${REGION}" \
    --staging_bucket="${STAGING_BUCKET}" \
    --display_name="RefundOps Verified Agent" \
    refund_ops_agent
else
  adk deploy cloud_run \
    --project="${PROJECT_ID}" \
    --region="${REGION}" \
    --service_name="${SERVICE_NAME}" \
    --with_ui \
    --trace_to_cloud \
    refund_ops_agent
fi
