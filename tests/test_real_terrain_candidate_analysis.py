from __future__ import annotations

from dataclasses import dataclass, replace

import pytest

from uav_rf_terrain.coordinates import LocalPoint
from uav_rf_terrain.geotiff_terrain_data import LocalGeoTiffTerrainDataAdapter
from uav_rf_terrain.los import LineOfSightError
from uav_rf_terrain.profile import TerrainProfileError
from uav_rf_terrain.terrain_data import (
    RASTER_TYPE_DEM,
    RASTER_TYPE_DSM,
    TerrainDataError,
    TerrainDatasetMetadata,
    TerrainNoDataError,
    TerrainPointOutsideError,
    TerrainPointSample,
    TerrainRasterMetadata,
)
from uav_rf_terrain.source_zones import TerrainSourceZone

from uav_rf_terrain.real_terrain_candidate_analysis import (
    CandidateAnalysisState,
    RealTerrainLaunchAreaAnalysisError,
    RealTerrainLaunchAreaConfig,
    RealTerrainLaunchAreaResult,
    SourceZoneAvailability,
    analyze_real_terrain_launch_area,
)


def _metadata() -> TerrainDatasetMetadata:
    common = dict(
        source_dataset_name="test terrain",
        source_provider="test provider",
        license_or_terms="test only",
        crs="EPSG:5179",
        resolution_m=10.0,
        width=5,
        height=5,
        bounds=(0.0, 0.0, 40.0, 40.0),
        nodata_value=None,
        vertical_datum="MSL",
        processing_summary="in-memory test terrain",
        is_synthetic=True,
        is_redistributable_processed_data=True,
    )
    return TerrainDatasetMetadata(
        dataset_name="test-epsg5179-terrain",
        dem=TerrainRasterMetadata(name="test-dem", raster_type=RASTER_TYPE_DEM, **common),
        dsm=TerrainRasterMetadata(name="test-dsm", raster_type=RASTER_TYPE_DSM, **common),
        processing_date="2026-07-14",
        processing_tool="pytest",
        alignment_status="aligned",
        notes="in-memory test fixture",
    )


@dataclass
class GridAdapter:
    dem: float = 100.0
    dsm: float = 100.0
    metadata_calls: int = 0
    read_calls: int = 0

    def validate_metadata(self) -> TerrainDatasetMetadata:
        self.metadata_calls += 1
        return _metadata()

    def get_metadata(self) -> TerrainDatasetMetadata:
        return _metadata()

    def get_dem_msl(self, x_index: int, y_index: int) -> float:
        self._validate_index(x_index, y_index)
        self.read_calls += 1
        return self.dem

    def get_dsm_msl(self, x_index: int, y_index: int) -> float:
        self._validate_index(x_index, y_index)
        self.read_calls += 1
        return self.dsm

    def get_surface_delta_m(self, x_index: int, y_index: int) -> float:
        self._validate_index(x_index, y_index)
        return self.dsm - self.dem

    @staticmethod
    def _validate_index(x_index: int, y_index: int) -> None:
        if not 0 <= x_index < 5 or not 0 <= y_index < 5:
            raise TerrainDataError("terrain cell is outside fixture bounds")


def _config(**overrides: object) -> RealTerrainLaunchAreaConfig:
    values: dict[str, object] = {
        "scenario_name": "test real terrain analysis",
        "target_point": LocalPoint(20.0, 20.0),
        "operating_radius_m": 10.0,
        "candidate_spacing_m": 10.0,
        "allowed_agl_m": 20.0,
        "launch_antenna_height_agl_m": 20.0,
        "frequency_hz": 2_400_000_000.0,
        "profile_sample_spacing_m": 10.0,
        "include_center": True,
        "include_out_of_radius": True,
    }
    values.update(overrides)
    return RealTerrainLaunchAreaConfig(**values)  # type: ignore[arg-type]


def test_pipeline_returns_real_projected_features_and_ordered_source_zone_batch() -> None:
    provider_points: list[tuple[LocalPoint, ...]] = []

    def provider(points: tuple[LocalPoint, ...]) -> tuple[TerrainSourceZone, ...]:
        provider_points.append(points)
        return tuple(TerrainSourceZone.ESA_DERIVED for _ in points)

    result = analyze_real_terrain_launch_area(
        GridAdapter(),
        _config(),
        source_zone_provider=provider,
    )

    assert result.summary.total_candidate_count == 9
    assert tuple(record.candidate_id for record in result.candidate_records) == tuple(
        feature.candidate_id for feature in result.candidate_features
    )
    assert result.candidate_features[0].feature_id == "candidate-feature-00000"
    assert result.candidate_features[0].x_m == result.candidate_records[0].candidate_point.x_m
    assert result.candidate_features[0].y_m == result.candidate_records[0].candidate_point.y_m
    assert result.candidate_features[0].geometry_crs == "EPSG:5179"
    assert result.candidate_features[0].candidate_cell_mgrs is None
    assert result.candidate_features[0].coordinate_display_state == "projected_only"
    assert len(provider_points) == 1
    eligible = [
        record
        for record in result.candidate_records
        if record.state is not CandidateAnalysisState.OUTSIDE_OPERATING_RADIUS
    ]
    assert provider_points[0] == tuple(record.candidate_point for record in eligible)
    assert all(record.source_zone_state is SourceZoneAvailability.AVAILABLE for record in eligible)
    assert all(
        record.source_zone_state is SourceZoneAvailability.NOT_APPLICABLE
        for record in result.candidate_records
        if record.state is CandidateAnalysisState.OUTSIDE_OPERATING_RADIUS
    )


def test_pipeline_normalizes_lower_dsm_without_mutating_adapter_values() -> None:
    adapter = GridAdapter(dem=100.0, dsm=90.0)

    result = analyze_real_terrain_launch_area(
        adapter,
        _config(include_center=False, include_out_of_radius=False),
    )

    assert result.target_surface_msl == 100.0
    assert all(record.launch_surface_msl == 100.0 for record in result.candidate_records)
    assert adapter.get_dsm_msl(2, 2) == 90.0
    assert all(record.state is CandidateAnalysisState.VALID_SCORED for record in result.candidate_records)


def test_source_zone_provider_failure_marks_only_eligible_records_unavailable() -> None:
    def unavailable_provider(points: tuple[LocalPoint, ...]) -> tuple[TerrainSourceZone, ...]:
        raise RuntimeError("local landcover unavailable")

    result = analyze_real_terrain_launch_area(
        GridAdapter(), _config(), source_zone_provider=unavailable_provider
    )

    assert result.warnings == ("source-zone provider unavailable",)
    assert any(record.state is CandidateAnalysisState.VALID_SCORED for record in result.candidate_records)
    assert all(
        record.source_zone_state is SourceZoneAvailability.UNAVAILABLE
        for record in result.candidate_records
        if record.state is not CandidateAnalysisState.OUTSIDE_OPERATING_RADIUS
    )


def test_zero_eligible_source_zone_batch_does_not_call_provider_or_warn() -> None:
    @dataclass
    class NoCandidateDataAdapter(GridAdapter):
        def get_dem_msl(self, x_index: int, y_index: int) -> float:
            if (x_index, y_index) != (2, 2):
                raise TerrainNoDataError("fixture candidate NoData")
            return super().get_dem_msl(x_index, y_index)

    calls: list[tuple[LocalPoint, ...]] = []

    def provider(points: tuple[LocalPoint, ...]) -> tuple[TerrainSourceZone, ...]:
        calls.append(points)
        raise RuntimeError("empty batches must not be sent")

    config = _config(include_center=False, include_out_of_radius=False)
    baseline = analyze_real_terrain_launch_area(NoCandidateDataAdapter(), config)
    result = analyze_real_terrain_launch_area(
        NoCandidateDataAdapter(),
        config,
        source_zone_provider=provider,
    )

    assert calls == []
    assert result.candidate_records == baseline.candidate_records
    assert all(
        record.source_zone_state is SourceZoneAvailability.NOT_APPLICABLE
        for record in result.candidate_records
    )
    assert result.warnings == ("no valid scored candidates were produced",)


@pytest.mark.parametrize(
    "provider_result",
    [
        (),
        ("not-a-source-zone",),
    ],
)
def test_eligible_source_zone_provider_invalid_results_preserve_core_records(
    provider_result: tuple[object, ...],
) -> None:
    calls: list[tuple[LocalPoint, ...]] = []
    config = _config()
    baseline = analyze_real_terrain_launch_area(GridAdapter(), config)

    def provider(points: tuple[LocalPoint, ...]) -> tuple[object, ...]:
        calls.append(points)
        return provider_result

    result = analyze_real_terrain_launch_area(
        GridAdapter(),
        config,
        source_zone_provider=provider,
    )
    expected_points = tuple(
        record.candidate_point
        for record in baseline.candidate_records
        if record.source_zone_state is SourceZoneAvailability.NOT_REQUESTED
    )

    assert calls == [expected_points]
    assert result.warnings == ("source-zone provider unavailable",)
    assert [record.candidate_id for record in result.candidate_records] == [
        record.candidate_id for record in baseline.candidate_records
    ]
    assert [record.state for record in result.candidate_records] == [
        record.state for record in baseline.candidate_records
    ]
    assert [record.candidate_score for record in result.candidate_records] == [
        record.candidate_score for record in baseline.candidate_records
    ]


def test_invalid_config_fails_before_adapter_access() -> None:
    adapter = GridAdapter()

    with pytest.raises(RealTerrainLaunchAreaAnalysisError, match="scenario_name"):
        analyze_real_terrain_launch_area(adapter, _config(scenario_name=" "))

    assert adapter.metadata_calls == 0


def test_public_safe_ordinary_scenario_name_is_accepted() -> None:
    config = _config(scenario_name="South Korea terrain candidate review")

    assert config.scenario_name == "South Korea terrain candidate review"


def test_public_https_scenario_name_uses_shared_public_safe_label_policy() -> None:
    config = _config(scenario_name="https://example.org/scenario-reference")

    assert config.scenario_name == "https://example.org/scenario-reference"


@pytest.mark.parametrize(
    "scenario_name",
    [
        "file:///Users/example/private-input.tif",
        "C:/Users/example/private-input.tif",
        r"C:\Users\example\private-input.tif",
        r"\\server\private-share\input.tif",
        "/home/example/private-input.tif",
    ],
)
def test_private_scenario_name_is_rejected_before_adapter_access_without_path_echo(
    scenario_name: str,
) -> None:
    adapter = GridAdapter()

    with pytest.raises(RealTerrainLaunchAreaAnalysisError, match="scenario_name") as exc_info:
        _config(scenario_name=scenario_name)

    assert scenario_name not in str(exc_info.value)
    assert adapter.metadata_calls == 0
    assert adapter.read_calls == 0


def test_candidate_count_guard_fails_before_session_metadata_access() -> None:
    adapter = GridAdapter()

    with pytest.raises(RealTerrainLaunchAreaAnalysisError, match="guard"):
        analyze_real_terrain_launch_area(adapter, _config(max_candidate_count=1))

    assert adapter.metadata_calls == 0
    assert adapter.read_calls == 0


def test_metadata_resolved_profile_guard_fails_before_target_sampling() -> None:
    adapter = GridAdapter()
    config = _config(
        operating_radius_m=900.0,
        candidate_spacing_m=180.0,
        profile_sample_spacing_m=None,
        max_profile_samples_per_candidate=20,
    )

    with pytest.raises(RealTerrainLaunchAreaAnalysisError, match="profile sample guard"):
        analyze_real_terrain_launch_area(adapter, config)

    assert adapter.metadata_calls == 1
    assert adapter.read_calls == 0


def test_metadata_resolved_total_profile_guard_fails_before_target_sampling() -> None:
    adapter = GridAdapter()
    config = _config(
        operating_radius_m=900.0,
        candidate_spacing_m=180.0,
        profile_sample_spacing_m=None,
        max_total_profile_samples=2_000,
    )

    with pytest.raises(RealTerrainLaunchAreaAnalysisError, match="total profile sample guard"):
        analyze_real_terrain_launch_area(adapter, config)

    assert adapter.metadata_calls == 1
    assert adapter.read_calls == 0


def test_in_radius_coincident_exclusion_preserves_radius_flag_in_record_and_feature() -> None:
    result = analyze_real_terrain_launch_area(GridAdapter(), _config())
    record = next(
        record
        for record in result.candidate_records
        if record.state is CandidateAnalysisState.COINCIDENT_WITH_TARGET
    )
    feature = next(feature for feature in result.candidate_features if feature.candidate_id == record.candidate_id)

    assert record.within_operation_radius is True
    assert feature.within_operation_radius is True
    assert record.candidate_score is None
    assert record.color_class.value == "excluded"
    assert record.fresnel_diagnostics is None


def test_candidate_nodata_mapping_is_not_derived_from_error_message_text() -> None:
    @dataclass
    class NodataAdapter(GridAdapter):
        def get_dem_msl(self, x_index: int, y_index: int) -> float:
            if (x_index, y_index) == (1, 2):
                raise TerrainDataError("outside wording must not control category")
            return super().get_dem_msl(x_index, y_index)

    result = analyze_real_terrain_launch_area(NodataAdapter(), _config())
    record = next(record for record in result.candidate_records if record.candidate_point == LocalPoint(10.0, 20.0))

    assert record.state is CandidateAnalysisState.TERRAIN_NODATA
    assert record.within_operation_radius is True


def test_session_domain_error_is_wrapped_with_cause() -> None:
    @dataclass
    class FailingSessionAdapter(GridAdapter):
        def open_analysis_session(self) -> object:
            raise TerrainDataError("session setup failed")

    with pytest.raises(RealTerrainLaunchAreaAnalysisError) as exc_info:
        analyze_real_terrain_launch_area(FailingSessionAdapter(), _config())

    assert isinstance(exc_info.value.__cause__, TerrainDataError)


def test_bool_is_not_accepted_as_a_positive_frequency() -> None:
    with pytest.raises(RealTerrainLaunchAreaAnalysisError, match="frequency_hz"):
        _config(frequency_hz=True)


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("allowed_agl_m", True, "allowed_agl_m"),
        ("launch_antenna_height_agl_m", True, "launch_antenna_height_agl_m"),
        ("max_candidate_count", True, "max_candidate_count"),
    ],
)
def test_bool_is_not_accepted_for_numeric_config_fields(
    field: str,
    value: object,
    message: str,
) -> None:
    with pytest.raises(RealTerrainLaunchAreaAnalysisError, match=message):
        _config(**{field: value})


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("scenario_name", " ", "scenario_name"),
        ("target_point", LocalPoint(float("nan"), 20.0), "target_point.x_m"),
        ("target_point", LocalPoint(20.0, float("inf")), "target_point.y_m"),
        ("target_point", LocalPoint(20.0, 20.0, 1.0), "target_point.z_m"),
        ("candidate_spacing_m", 20.0, "candidate_spacing_m"),
    ],
)
def test_config_validation_rejects_invalid_values_before_adapter_access(
    field: str,
    value: object,
    message: str,
) -> None:
    adapter = GridAdapter()

    with pytest.raises(RealTerrainLaunchAreaAnalysisError, match=message):
        analyze_real_terrain_launch_area(adapter, _config(**{field: value}))

    assert adapter.metadata_calls == 0


def _record_and_feature(
    result: RealTerrainLaunchAreaResult,
    state: CandidateAnalysisState,
) -> tuple[object, object]:
    record = next(item for item in result.candidate_records if item.state is state)
    feature = next(
        item
        for item in result.candidate_features
        if item.candidate_id == record.candidate_id
    )
    return record, feature


@pytest.mark.parametrize(
    ("state", "within_radius", "has_distance_3d"),
    [
        (CandidateAnalysisState.OUTSIDE_OPERATING_RADIUS, False, False),
        (CandidateAnalysisState.COINCIDENT_WITH_TARGET, True, True),
    ],
)
def test_builtin_excluded_states_preserve_radius_and_feature_contract(
    state: CandidateAnalysisState,
    within_radius: bool,
    has_distance_3d: bool,
) -> None:
    result = analyze_real_terrain_launch_area(GridAdapter(), _config())
    record, feature = _record_and_feature(result, state)

    assert record.within_operation_radius is within_radius
    assert (record.distance_3d_m is not None) is has_distance_3d
    assert record.color_class.value == "excluded"
    assert record.candidate_score is None
    assert record.fresnel_diagnostics is None
    assert feature.within_operation_radius is within_radius


def test_typed_candidate_outside_extent_maps_without_message_parsing() -> None:
    @dataclass
    class OutsideAdapter(GridAdapter):
        def get_dem_msl(self, x_index: int, y_index: int) -> float:
            if (x_index, y_index) == (1, 2):
                raise TerrainPointOutsideError("arbitrary wording")
            return super().get_dem_msl(x_index, y_index)

    result = analyze_real_terrain_launch_area(OutsideAdapter(), _config())
    record, feature = _record_and_feature(result, CandidateAnalysisState.OUTSIDE_RASTER_EXTENT)

    assert record.within_operation_radius is True
    assert record.distance_3d_m is None
    assert record.color_class.value == "excluded"
    assert record.candidate_score is None
    assert record.fresnel_diagnostics is None
    assert feature.within_operation_radius is True


def test_typed_candidate_nodata_maps_without_message_parsing() -> None:
    @dataclass
    class NodataAdapter(GridAdapter):
        def get_dem_msl(self, x_index: int, y_index: int) -> float:
            if (x_index, y_index) == (1, 2):
                raise TerrainNoDataError("arbitrary wording")
            return super().get_dem_msl(x_index, y_index)

    result = analyze_real_terrain_launch_area(NodataAdapter(), _config())
    record, feature = _record_and_feature(result, CandidateAnalysisState.TERRAIN_NODATA)

    assert record.within_operation_radius is True
    assert record.distance_3d_m is None
    assert record.color_class.value == "excluded"
    assert record.candidate_score is None
    assert record.fresnel_diagnostics is None
    assert feature.within_operation_radius is True


def test_three_dimensional_radius_exclusion_preserves_distance_and_radius_state() -> None:
    @dataclass
    class ElevatedCandidateAdapter(GridAdapter):
        def get_dem_msl(self, x_index: int, y_index: int) -> float:
            if (x_index, y_index) == (1, 2):
                return 150.0
            return super().get_dem_msl(x_index, y_index)

        def get_dsm_msl(self, x_index: int, y_index: int) -> float:
            return self.get_dem_msl(x_index, y_index)

    result = analyze_real_terrain_launch_area(ElevatedCandidateAdapter(), _config())
    record, feature = _record_and_feature(result, CandidateAnalysisState.OUTSIDE_OPERATING_RADIUS)
    three_dimensional = next(
        item
        for item in result.candidate_records
        if item.state is CandidateAnalysisState.OUTSIDE_OPERATING_RADIUS
        and item.distance_3d_m is not None
    )

    assert record.within_operation_radius is False
    assert feature.within_operation_radius is False
    assert three_dimensional.distance_2d_m <= 10.0
    assert three_dimensional.distance_3d_m is not None
    assert three_dimensional.distance_3d_m > 10.0
    assert three_dimensional.candidate_score is None
    assert three_dimensional.fresnel_diagnostics is None


def test_launch_surface_obstruction_is_in_radius_exclusion() -> None:
    @dataclass
    class ObstructedCandidateAdapter(GridAdapter):
        def get_dsm_msl(self, x_index: int, y_index: int) -> float:
            if (x_index, y_index) == (1, 2):
                return 121.0
            return super().get_dsm_msl(x_index, y_index)

    result = analyze_real_terrain_launch_area(ObstructedCandidateAdapter(), _config())
    record, feature = _record_and_feature(result, CandidateAnalysisState.LAUNCH_SURFACE_OBSTRUCTED)

    assert record.within_operation_radius is True
    assert record.distance_3d_m is not None
    assert record.color_class.value == "excluded"
    assert record.candidate_score is None
    assert record.fresnel_diagnostics is None
    assert feature.within_operation_radius is True


def test_profile_failure_is_in_radius_exclusion(monkeypatch: pytest.MonkeyPatch) -> None:
    from uav_rf_terrain.real_terrain_candidate_analysis import _CompatibilityTerrainAnalysisSession

    original = _CompatibilityTerrainAnalysisSession.extract_profile

    def unavailable(
        self: object,
        start: LocalPoint,
        end: LocalPoint,
        *,
        sample_spacing_m: float,
        scenario_name: str,
    ) -> object:
        if start == LocalPoint(10.0, 20.0):
            raise TerrainProfileError("fixture profile unavailable")
        return original(
            self, start, end, sample_spacing_m=sample_spacing_m, scenario_name=scenario_name
        )

    monkeypatch.setattr(_CompatibilityTerrainAnalysisSession, "extract_profile", unavailable)
    result = analyze_real_terrain_launch_area(GridAdapter(), _config())
    record, feature = _record_and_feature(result, CandidateAnalysisState.PROFILE_UNAVAILABLE)

    assert record.within_operation_radius is True
    assert record.distance_3d_m is not None
    assert record.color_class.value == "excluded"
    assert record.candidate_score is None
    assert record.fresnel_diagnostics is None
    assert feature.within_operation_radius is True


def test_analysis_failure_is_in_radius_exclusion(monkeypatch: pytest.MonkeyPatch) -> None:
    def invalid_los(*args: object, **kwargs: object) -> object:
        raise LineOfSightError("fixture analysis invalid")

    monkeypatch.setattr(
        "uav_rf_terrain.real_terrain_candidate_analysis.analyze_dsm_los",
        invalid_los,
    )
    result = analyze_real_terrain_launch_area(GridAdapter(), _config())
    record, feature = _record_and_feature(result, CandidateAnalysisState.ANALYSIS_INVALID)

    assert record.within_operation_radius is True
    assert record.distance_3d_m is not None
    assert record.color_class.value == "excluded"
    assert record.candidate_score is None
    assert record.fresnel_diagnostics is None
    assert feature.within_operation_radius is True


@pytest.mark.parametrize(
    "error_type",
    [TerrainPointOutsideError, TerrainNoDataError],
)
def test_target_typed_terrain_errors_are_fatal_and_chained(
    error_type: type[TerrainDataError],
) -> None:
    @dataclass
    class FailingTargetAdapter(GridAdapter):
        def get_dem_msl(self, x_index: int, y_index: int) -> float:
            if (x_index, y_index) == (2, 2):
                raise error_type("fixture target failure")
            return super().get_dem_msl(x_index, y_index)

    with pytest.raises(RealTerrainLaunchAreaAnalysisError, match="target terrain sample failed") as exc_info:
        analyze_real_terrain_launch_area(FailingTargetAdapter(), _config())

    assert isinstance(exc_info.value.__cause__, error_type)


def test_target_surface_above_flight_is_fatal() -> None:
    with pytest.raises(RealTerrainLaunchAreaAnalysisError, match="target surface is above"):
        analyze_real_terrain_launch_area(GridAdapter(dsm=121.0), _config())


def test_target_non_finite_terrain_value_is_fatal_and_chained() -> None:
    with pytest.raises(RealTerrainLaunchAreaAnalysisError, match="target terrain sample failed") as exc_info:
        analyze_real_terrain_launch_area(GridAdapter(dem=float("nan")), _config())

    assert isinstance(exc_info.value.__cause__, TerrainNoDataError)


def test_missing_local_rasterio_is_wrapped_as_fatal_session_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def missing_rasterio(name: str) -> object:
        if name == "rasterio":
            raise ModuleNotFoundError("fixture rasterio unavailable")
        return __import__(name)

    monkeypatch.setattr(
        "uav_rf_terrain.geotiff_terrain_data.importlib.import_module",
        missing_rasterio,
    )
    adapter = LocalGeoTiffTerrainDataAdapter("dem.tif", "dsm.tif")

    with pytest.raises(RealTerrainLaunchAreaAnalysisError, match="terrain analysis session failed") as exc_info:
        analyze_real_terrain_launch_area(adapter, _config())

    assert isinstance(exc_info.value.__cause__, TerrainDataError)


def test_wrong_crs_is_a_public_analysis_error() -> None:
    @dataclass
    class WrongCrsAdapter(GridAdapter):
        def validate_metadata(self) -> TerrainDatasetMetadata:
            metadata = _metadata()
            return replace(
                metadata,
                dem=replace(metadata.dem, crs="EPSG:4326"),
                dsm=replace(metadata.dsm, crs="EPSG:4326"),
            )

    with pytest.raises(RealTerrainLaunchAreaAnalysisError, match="dataset CRS must be EPSG:5179"):
        analyze_real_terrain_launch_area(WrongCrsAdapter(), _config())


def test_session_enter_domain_error_is_wrapped_with_cause() -> None:
    class EnterFailureSession:
        def __enter__(self) -> object:
            raise TerrainDataError("fixture metadata failure")

        def __exit__(self, *args: object) -> None:
            return None

    @dataclass
    class EnterFailureAdapter(GridAdapter):
        def open_analysis_session(self) -> object:
            return EnterFailureSession()

    with pytest.raises(RealTerrainLaunchAreaAnalysisError, match="terrain analysis session failed") as exc_info:
        analyze_real_terrain_launch_area(EnterFailureAdapter(), _config())

    assert isinstance(exc_info.value.__cause__, TerrainDataError)


def test_session_exit_domain_error_is_wrapped_with_cause() -> None:
    class ExitFailureSession:
        metadata = _metadata()

        def __enter__(self) -> "ExitFailureSession":
            return self

        def __exit__(self, *args: object) -> None:
            raise TerrainDataError("fixture session close failure")

        def sample_point(self, point: LocalPoint) -> TerrainPointSample:
            return TerrainPointSample(
                requested_point=point,
                cell_center_point=point,
                x_index=2,
                y_index=2,
                dem_msl=100.0,
                dsm_msl=100.0,
                surface_delta_m=0.0,
            )

        def extract_profile(
            self,
            start: LocalPoint,
            end: LocalPoint,
            *,
            sample_spacing_m: float,
            scenario_name: str,
        ) -> object:
            raise TerrainDataError("fixture profile unavailable")

    @dataclass
    class ExitFailureAdapter(GridAdapter):
        def open_analysis_session(self) -> object:
            return ExitFailureSession()

    with pytest.raises(RealTerrainLaunchAreaAnalysisError, match="terrain analysis session failed") as exc_info:
        analyze_real_terrain_launch_area(ExitFailureAdapter(), _config())

    assert isinstance(exc_info.value.__cause__, TerrainDataError)


def test_unexpected_session_runtime_error_is_not_reclassified() -> None:
    @dataclass
    class UnexpectedFailureAdapter(GridAdapter):
        def open_analysis_session(self) -> object:
            raise RuntimeError("fixture programming failure")

    with pytest.raises(RuntimeError, match="fixture programming failure"):
        analyze_real_terrain_launch_area(UnexpectedFailureAdapter(), _config())
