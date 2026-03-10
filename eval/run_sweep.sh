#!/usr/bin/env bash
# Run the Critic eval across all available Ollama models.
# Results are saved to eval/results/ with model name and timestamp.
#
# Usage:
#   ./eval/run_sweep.sh                    # all models
#   ./eval/run_sweep.sh qwen3:8b mistral:7b  # specific models

set -euo pipefail

MODELS=(
    "gemma3:12b-it-q8_0"
    "qwen3:8b"
    "llama3.1:8b-instruct-q8_0"
    "qwen2.5:7b"
    "mistral:7b"
)

if [ $# -gt 0 ]; then
    MODELS=("$@")
fi

BASE_URL="${AGENT_LLM_BASE_URL:-http://localhost:11434/v1}"

echo "============================================"
echo "Critic Eval Sweep"
echo "Models: ${MODELS[*]}"
echo "Base URL: ${BASE_URL}"
echo "============================================"
echo ""

for model in "${MODELS[@]}"; do
    echo ">>> Running eval for: ${model}"
    AGENT_LLM_PROVIDER=openai \
    AGENT_LLM_BASE_URL="${BASE_URL}" \
    AGENT_LLM_MODEL="${model}" \
    AGENT_LLM_API_KEY=not-needed \
    python -m eval.run_critic_eval || echo "  FAILED for ${model}"
    echo ""
done

echo ">>> Generating comparison report..."
python -m eval.compare_results

echo "Done."
