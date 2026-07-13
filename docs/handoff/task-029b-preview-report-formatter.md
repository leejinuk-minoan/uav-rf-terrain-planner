# Task 029B Preview Report Formatter

Task 029B adds a pure deterministic `format_preview_report(...)` formatter and `PreviewReportError`. It reuses the appendix-table validation boundary, summarizes existing records without sorting or recalculation, optionally embeds the exact existing table, preserves MGRS/source metadata boundaries, and creates no files.

No CLI, file output, schema, table formatter, terrain, GIS, scoring, route, waypoint, UI, or control behavior is changed. Local focused and full tests plus compileall, Ruff, mypy, diff, scope, and artifact checks are recorded in the PR. CI passed on the reviewed PR head.

Overall local and CI status: **passed on the reviewed PR head**.
