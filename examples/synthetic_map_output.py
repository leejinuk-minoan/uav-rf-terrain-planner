"""Print a reproducible offline synthetic map-ready data summary."""

from uav_rf_terrain.map_outputs import build_map_output_package, format_map_output_summary
from uav_rf_terrain.scenario_outputs import build_synthetic_end_to_end_scenario


def main() -> None:
    """Build the default synthetic scenario and print map-ready data summary."""

    scenario = build_synthetic_end_to_end_scenario()
    package = build_map_output_package(scenario)
    print(format_map_output_summary(package))


if __name__ == "__main__":
    main()
