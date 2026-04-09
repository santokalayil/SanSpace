#!/bin/bash
set -euo pipefail

SKILL_PATH="$(pwd)/.."
EVAL_SET="$(pwd)/iteration-1/evals.json"

echo "This script prepares eval workspace and shows commands to run the skill-creator test scaffolding."
echo "It does NOT run the model (requires the 'claude' CLI and a configured model)."

echo
echo "To run trigger eval (requires 'claude' CLI):"
echo "  cd /path/to/repos/skills/skills/skill-creator && python3 scripts/run_eval.py --eval-set ${EVAL_SET} --skill-path ${SKILL_PATH} --model <model-id> --verbose"

echo
echo "To run the full improvement loop (requires 'claude' CLI and a model id):"
echo "  cd /path/to/repos/skills/skills/skill-creator && python3 scripts/run_loop.py --eval-set ${EVAL_SET} --skill-path ${SKILL_PATH} --model <model-id> --verbose"

echo
echo "If you want me to attempt running these now, confirm and ensure the 'claude' CLI is installed and accessible in this environment."
