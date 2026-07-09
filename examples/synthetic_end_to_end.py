"""Print a reproducible offline synthetic end-to-end summary."""

from uav_rf_terrain.scenario_outputs import (
    build_synthetic_end_to_end_scenario,
    format_synthetic_end_to_end_summary,
)


def main() -> None:
    """Build the default synthetic scenario and print its summary."""

    scenario = build_synthetic_end_to_end_scenario()
    print(format_synthetic_end_to_end_summary(scenario))


if __name__ == "__main__":
    main()
