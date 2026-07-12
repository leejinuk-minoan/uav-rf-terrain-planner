"""Minimal stdout CLI for the synthetic candidate display preview."""

from __future__ import annotations

import argparse
from collections.abc import Sequence
import json
import sys

from .candidate_display_preview import CandidateDisplayPreviewError
from .synthetic_candidate_preview_smoke import (
    SyntheticCandidatePreviewSmokeError,
    build_synthetic_candidate_preview_smoke,
)


def _positive_int(value: str) -> int:
    try:
        resolved = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("must be a positive integer") from exc
    if resolved <= 0:
        raise argparse.ArgumentTypeError("must be a positive integer")
    return resolved


def build_parser() -> argparse.ArgumentParser:
    """Build the synthetic preview CLI parser."""

    parser = argparse.ArgumentParser(
        prog="python -m uav_rf_terrain.preview_cli",
        description="Print the existing synthetic candidate display preview.",
    )
    parser.add_argument(
        "--synthetic",
        action="store_true",
        required=True,
        help="run the existing in-memory synthetic preview path",
    )
    parser.add_argument(
        "--max-records",
        type=_positive_int,
        default=None,
        help="limit visible plain-text candidate rows to a positive integer",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        dest="json_output",
        help="print the existing JSON-ready preview dictionary",
    )
    return parser


def run_preview_cli(argv: Sequence[str] | None = None) -> int:
    """Run the CLI and return a deterministic process status code."""

    try:
        args = build_parser().parse_args(argv)
    except SystemExit as exc:
        return exc.code if isinstance(exc.code, int) else 2
    try:
        result = build_synthetic_candidate_preview_smoke(
            max_preview_records=args.max_records,
        )
    except (SyntheticCandidatePreviewSmokeError, CandidateDisplayPreviewError) as exc:
        print(f"preview error: {exc}", file=sys.stderr)
        return 1
    if args.json_output:
        print(json.dumps(result.preview_dict, ensure_ascii=False))
    else:
        print(result.preview_text)
    return 0


def main() -> None:
    """Exit with the CLI status code."""

    raise SystemExit(run_preview_cli())


if __name__ == "__main__":
    main()
