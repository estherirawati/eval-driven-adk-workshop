#!/usr/bin/env bash
# Stage Controller for Live Demo Resilience (Prof. Esther's 1-Command Safety Net)
set -euo pipefail

WORKSHOP_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${WORKSHOP_ROOT}"

CMD="${1:-status}"

case "${CMD}" in
  status)
    echo "=== LIVE STAGE PRE-FLIGHT STATUS ==="
    echo "Directory : ${WORKSHOP_ROOT}"
    echo "Python    : $(python3 --version)"
    if grep -q "VIP-SORRY-25" refund_ops_agent/agent.py; then
      echo "agent.py  : CURRENTLY SET TO v0_buggy (RED phase)"
    else
      echo "agent.py  : CURRENTLY SET TO v1_hardened (GREEN phase)"
    fi
    CASE_COUNT="$(python3 -c 'import json; print(len(json.load(open("evals/core_trajectory.evalset.json"))["eval_cases"]))')"
    echo "EvalCases : ${CASE_COUNT} cases in evals/core_trajectory.evalset.json"
    ;;
  set-buggy)
    cp refund_ops_agent/agent_v0_buggy.py refund_ops_agent/agent.py
    echo "Switched refund_ops_agent/agent.py -> v0_buggy (Ready for Step 3 RED failure demo!)"
    ;;
  set-hardened)
    cp refund_ops_agent/agent_v1_hardened.py refund_ops_agent/agent.py
    echo "Restored refund_ops_agent/agent.py -> v1_hardened (Ready for Step 4 GREEN pass!)"
    ;;
  reset-all)
    cp refund_ops_agent/agent_v1_hardened.py refund_ops_agent/agent.py
    cp evals/.baseline_core_trajectory.evalset.json evals/core_trajectory.evalset.json
    echo "Reset agent.py (GREEN) and core_trajectory.evalset.json (3 baseline cases)."
    ;;
  *)
    echo "Usage: ./stage_ctl.sh {status|set-buggy|set-hardened|reset-all}"
    exit 1
    ;;
esac
