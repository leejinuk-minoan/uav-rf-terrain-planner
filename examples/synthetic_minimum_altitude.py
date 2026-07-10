"""Print a reproducible synthetic minimum altitude summary."""

from uav_rf_terrain.coordinates import LocalPoint
from uav_rf_terrain.minimum_altitude import (
    compute_minimum_required_altitude,
    summarize_minimum_altitude_result,
)
from uav_rf_terrain.profile import extract_terrain_profile
from uav_rf_terrain.synthetic import SCENARIO_SINGLE_RIDGE, create_synthetic_terrain


def main() -> None:
    """Build a synthetic ridge profile and print minimum altitude proxy fields."""

    terrain = create_synthetic_terrain(SCENARIO_SINGLE_RIDGE)
    profile = extract_terrain_profile(
        terrain=terrain,
        start=LocalPoint(x_m=0.0, y_m=2500.0),
        end=LocalPoint(x_m=5000.0, y_m=2500.0),
    )
    result = compute_minimum_required_altitude(
        profile,
        launch_antenna_msl_m=profile.samples[0].dem_msl,
        frequency_hz=2_400_000_000.0,
    )

    print(f"minimum_required_msl_m={result.minimum_required_msl_m:.2f}")
    print(
        "minimum_required_agl_over_highest_dem_m="
        f"{result.minimum_required_agl_over_highest_dem_m:.2f}"
    )
    print(
        "minimum_required_agl_over_target_dem_m="
        f"{result.minimum_required_agl_over_target_dem_m:.2f}"
    )
    print(f"limiting_sample_index={result.limiting_sample_index}")
    print(summarize_minimum_altitude_result(result))


if __name__ == "__main__":
    main()
