"""CLI entrypoint.

Usage:
python -m orchestrator.cli "Plan a 5-day trip..."
"""

from __future__ import annotations

import argparse
import sys
from typing import Optional

from orchestrator.pipeline import plan_trip_sync


def main(argv: Optional[list] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Multi Agent_Tokyo — LLM travel planner"
    )
    parser.add_argument(
        "request",
        nargs="?",
        help="Natural-language trip request",
    )
    parser.add_argument(
        "--run-id",
        default=None,
        help="Optional run id for artifacts",
    )
    parser.add_argument(
        "-f",
        "--file",
        help="Read request from file instead of argument",
    )

    args = parser.parse_args(argv)

    if args.file:
        with open(args.file, encoding="utf-8") as f:
            request = f.read()
    else:
        request = args.request

    if not request or not request.strip():
        parser.error("Provide a request string or --file")

    try:
        result = plan_trip_sync(
            request.strip(),
            run_id=args.run_id,
        )
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Pipeline failed: {e}", file=sys.stderr)
        return 1

    print(f"Run ID: {result.run_id}")
    print(f"Artifacts: {result.run_dir}")
    print(f"Validation: {result.validation_status}")
    print("---")
    print(result.final_markdown)

    return 0 if result.validation_status != "fail" else 2


if __name__ == "__main__":
    raise SystemExit(main())