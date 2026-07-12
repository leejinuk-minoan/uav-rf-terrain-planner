"""CLI for stdout or explicit file output of the synthetic candidate preview."""

from __future__ import annotations

import argparse
from collections.abc import Mapping, Sequence
import json
from pathlib import Path
import sys

from .candidate_display_preview import CandidateDisplayPreviewError
from .preview_appendix_table import (
    PreviewAppendixTableError,
    format_preview_appendix_table,
)
from .synthetic_candidate_preview_smoke import (
    SyntheticCandidatePreviewSmokeError,
    build_synthetic_candidate_preview_smoke,
)


class PreviewJsonInputError(ValueError):
    """Raised when an explicitly selected preview JSON input cannot be loaded."""


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
        help="run the existing in-memory synthetic preview path",
    )
    parser.add_argument("--input-json", metavar="PATH")
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
    parser.add_argument(
        "--table",
        action="store_true",
        dest="table_output",
        help="print the existing preview as an appendix table",
    )
    parser.add_argument("--output-json", metavar="PATH")
    parser.add_argument("--output-text", metavar="PATH")
    parser.add_argument("--output-table", metavar="PATH")
    parser.add_argument(
        "--force",
        action="store_true",
        help="overwrite an existing explicitly selected output file",
    )
    return parser


def _validate_arguments(args: argparse.Namespace, parser: argparse.ArgumentParser) -> None:
    source_count = sum((args.synthetic, args.input_json is not None))
    if source_count != 1:
        parser.error("exactly one of --synthetic or --input-json is required")
    selectors = (
        args.json_output,
        args.table_output,
        args.output_json is not None,
        args.output_text is not None,
        args.output_table is not None,
    )
    output_count = sum(selectors)
    if output_count > 1:
        parser.error("output selectors cannot be used together")
    if args.input_json is not None and not (
        args.table_output or args.output_table is not None
    ):
        parser.error("--input-json requires --table or --output-table")


def _read_preview_json(path: Path) -> dict[str, object]:
    if not path.is_file():
        raise PreviewJsonInputError("input path must exist and be a file")
    try:
        decoded = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise PreviewJsonInputError("input file must contain valid UTF-8 JSON") from exc
    if not isinstance(decoded, Mapping):
        raise PreviewJsonInputError("input JSON top level must be an object")
    return dict(decoded)


def _validate_output_path(path: Path, *, force: bool) -> None:
    if not path.parent.is_dir():
        raise OSError("parent directory does not exist")
    if path.is_dir():
        raise OSError("output path is a directory")
    if path.exists() and not force:
        raise OSError("output file already exists; use --force to overwrite")


def _write_text_output(path: Path, text: str, *, force: bool) -> None:
    _validate_output_path(path, force=force)
    path.write_text(text.rstrip("\n") + "\n", encoding="utf-8")


def _write_json_output(
    path: Path, payload: Mapping[str, object], *, force: bool
) -> None:
    _write_text_output(
        path,
        json.dumps(payload, ensure_ascii=False, indent=2),
        force=force,
    )


def run_preview_cli(argv: Sequence[str] | None = None) -> int:
    """Run the CLI and return a deterministic process status code."""

    try:
        parser = build_parser()
        args = parser.parse_args(argv)
        _validate_arguments(args, parser)
    except SystemExit as exc:
        return exc.code if isinstance(exc.code, int) else 2
    preview_text: str | None = None
    preview_dict: Mapping[str, object]
    if args.input_json is not None:
        try:
            preview_dict = _read_preview_json(Path(args.input_json))
        except PreviewJsonInputError as exc:
            print(f"preview input error: {exc}", file=sys.stderr)
            return 1
    else:
        try:
            result = build_synthetic_candidate_preview_smoke(
                max_preview_records=args.max_records,
            )
        except (SyntheticCandidatePreviewSmokeError, CandidateDisplayPreviewError) as exc:
            print(f"preview error: {exc}", file=sys.stderr)
            return 1
        preview_dict = result.preview_dict
        preview_text = result.preview_text
    table_text: str | None = None
    if args.table_output or args.output_table is not None:
        try:
            table_text = format_preview_appendix_table(
                preview_dict,
                max_rows=args.max_records,
            )
        except PreviewAppendixTableError as exc:
            print(f"preview table error: {exc}", file=sys.stderr)
            return 1
    try:
        if args.output_json is not None:
            _write_json_output(Path(args.output_json), preview_dict, force=args.force)
            print(f"preview saved: {args.output_json}")
        elif args.output_text is not None:
            assert preview_text is not None
            _write_text_output(Path(args.output_text), preview_text, force=args.force)
            print(f"preview saved: {args.output_text}")
        elif args.output_table is not None:
            assert table_text is not None
            _write_text_output(Path(args.output_table), table_text, force=args.force)
            print(f"preview saved: {args.output_table}")
        elif args.json_output:
            print(json.dumps(result.preview_dict, ensure_ascii=False))
        elif args.table_output:
            assert table_text is not None
            print(table_text)
        else:
            assert preview_text is not None
            print(preview_text)
    except OSError as exc:
        print(f"output error: {exc}", file=sys.stderr)
        return 3
    return 0


def main() -> None:
    """Exit with the CLI status code."""

    raise SystemExit(run_preview_cli())


if __name__ == "__main__":
    main()
