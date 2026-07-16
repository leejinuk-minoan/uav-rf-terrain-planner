"""Render an application-prepared real-terrain map package for local smoke checks.

The caller supplies a ``module:callable`` factory that returns a verified
``RealTerrainLaunchAreaMapPackage``. This helper neither analyzes terrain nor
invents coordinates, and it never opens a browser.
"""

from __future__ import annotations

import argparse
import importlib
import sys
from collections.abc import Callable

from uav_rf_terrain.local_html_map_renderer import (
    LocalHtmlMapRendererError,
    render_local_html_map,
    write_local_html_map,
)
from uav_rf_terrain.real_terrain_launch_area_map import RealTerrainLaunchAreaMapPackage


def _load_factory(factory_path: str) -> Callable[[], RealTerrainLaunchAreaMapPackage]:
    module_name, separator, callable_name = factory_path.partition(":")
    if not separator or not module_name or not callable_name:
        raise ValueError("factory must use module:callable syntax.")
    factory = getattr(importlib.import_module(module_name), callable_name)
    if not callable(factory):
        raise ValueError("factory must be callable.")
    return factory


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Local real-terrain map package smoke.")
    parser.add_argument("--factory", required=True, help="Application factory as module:callable.")
    parser.add_argument("--output-html", help="Optional explicit local HTML output path.")
    parser.add_argument("--force", action="store_true", help="Allow overwriting --output-html.")
    args = parser.parse_args(argv)
    try:
        package = _load_factory(args.factory)()
        if not isinstance(package, RealTerrainLaunchAreaMapPackage):
            raise ValueError("factory must return RealTerrainLaunchAreaMapPackage.")
        if args.output_html:
            output = write_local_html_map(package, args.output_html, force=args.force)
            print(f"html_written={output}")
        else:
            render_local_html_map(package)
            print("html_rendered_in_memory=true")
        print(f"rendered_candidate_count={package.summary.rendered_candidate_count}")
        print(f"selectable_candidate_count={package.summary.selectable_candidate_count}")
        print(f"selected_candidate_count={package.summary.selected_candidate_count}")
        return 0
    except (ImportError, AttributeError, TypeError, ValueError, LocalHtmlMapRendererError) as exc:
        print(f"map smoke error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
