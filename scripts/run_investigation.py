"""Run a full investigation through the agent spine.

Usage:
    python scripts/run_investigation.py \
        --question "Investigate respiratory failure (J96) mortality trends" \
        --data-dir experiments/respiratory_failure/outputs/data
"""

from __future__ import annotations

import argparse
import sys

from loguru import logger

from src.agent.config import AgentConfig
from src.agent.spine import Spine


def main():
    parser = argparse.ArgumentParser(description="Run a health investigation")
    parser.add_argument(
        "--question", "-q",
        required=True,
        help="Research question to investigate",
    )
    parser.add_argument(
        "--data-dir", "-d",
        default="",
        help="Directory with pre-processed parquet data files",
    )
    parser.add_argument(
        "--output-dir", "-o",
        default="runs",
        help="Output directory for runs (default: runs/)",
    )
    parser.add_argument(
        "--max-rounds",
        type=int,
        default=5,
        help="Max tool-calling rounds per agent (default: 5)",
    )
    args = parser.parse_args()

    logger.remove()
    logger.add(sys.stderr, level="INFO")

    config = AgentConfig()
    spine = Spine(
        config=config,
        output_dir=args.output_dir,
        max_tool_rounds=args.max_rounds,
    )

    result = spine.run(
        question=args.question,
        data_dir=args.data_dir,
    )

    if result.error:
        logger.error(f"Investigation failed: {result.error}")
        sys.exit(1)

    logger.info(f"Run complete: {result.run_dir}")
    for ar in result.agent_results:
        status = "OK" if not ar.error else f"ERR: {ar.error}"
        logger.info(f"  {ar.agent_name}: {status} ({ar.duration_ms}ms)")


if __name__ == "__main__":
    main()
