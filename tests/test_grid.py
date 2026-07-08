from dataclasses import fields

import pytest

from uav_rf_terrain.coordinates import LocalPoint
from uav_rf_terrain.grid import (
    CandidateCell,
    CandidateGridConfig,
    filter_within_operation_radius,
    generate_candidate_grid,
)


def test_candidate_grid_config_validation() -> None:
    CandidateGridConfig(radius_m=100.0, spacing_m=50.0)

    with pytest.raises(ValueError, match="radius_m"):
        CandidateGridConfig(radius_m=0.0, spacing_m=50.0)

    with pytest.raises(ValueError, match="spacing_m"):
        CandidateGridConfig(radius_m=100.0, spacing_m=0.0)

    with pytest.raises(ValueError, match="spacing_m"):
        CandidateGridConfig(radius_m=100.0, spacing_m=200.0)


def test_generate_candidate_grid_is_not_empty() -> None:
    cells = generate_candidate_grid(
        center=LocalPoint(x_m=0.0, y_m=0.0),
        config=CandidateGridConfig(radius_m=100.0, spacing_m=100.0),
    )

    assert cells
    assert all(isinstance(cell, CandidateCell) for cell in cells)


def test_generate_candidate_grid_includes_center_by_default() -> None:
    cells = generate_candidate_grid(
        center=LocalPoint(x_m=10.0, y_m=20.0),
        config=CandidateGridConfig(radius_m=100.0, spacing_m=100.0),
    )

    center_cells = [cell for cell in cells if cell.point == LocalPoint(x_m=10.0, y_m=20.0)]
    assert len(center_cells) == 1
    assert center_cells[0].cell_id == "cell_x+000_y+000"


def test_generate_candidate_grid_can_exclude_center() -> None:
    cells = generate_candidate_grid(
        center=LocalPoint(x_m=0.0, y_m=0.0),
        config=CandidateGridConfig(radius_m=100.0, spacing_m=100.0, include_center=False),
    )

    assert all(cell.point != LocalPoint(x_m=0.0, y_m=0.0) for cell in cells)


def test_generate_candidate_grid_marks_inside_and_outside_radius() -> None:
    cells = generate_candidate_grid(
        center=LocalPoint(x_m=0.0, y_m=0.0),
        config=CandidateGridConfig(radius_m=100.0, spacing_m=100.0, include_excluded=True),
    )

    assert any(cell.within_operation_radius for cell in cells)
    assert any(not cell.within_operation_radius for cell in cells)

    in_radius = filter_within_operation_radius(cells)
    assert in_radius
    assert all(cell.within_operation_radius for cell in in_radius)


def test_generate_candidate_grid_can_drop_excluded_candidates() -> None:
    cells = generate_candidate_grid(
        center=LocalPoint(x_m=0.0, y_m=0.0),
        config=CandidateGridConfig(radius_m=100.0, spacing_m=100.0, include_excluded=False),
    )

    assert cells
    assert all(cell.within_operation_radius for cell in cells)


def test_cell_ids_are_stable() -> None:
    config = CandidateGridConfig(radius_m=100.0, spacing_m=100.0)
    first = generate_candidate_grid(center=LocalPoint(x_m=0.0, y_m=0.0), config=config)
    second = generate_candidate_grid(center=LocalPoint(x_m=0.0, y_m=0.0), config=config)

    first_ids = [cell.cell_id for cell in first]
    second_ids = [cell.cell_id for cell in second]

    assert first_ids == second_ids
    assert len(first_ids) == len(set(first_ids))


def test_candidate_cell_has_no_top_five_or_ranked_output_fields() -> None:
    field_names = {field.name for field in fields(CandidateCell)}

    assert "top_n" not in field_names
    assert "rank" not in field_names
    assert "ranked_launch_sites" not in field_names
    assert "rssi" not in field_names
    assert "sinr" not in field_names
    assert "packet_loss" not in field_names
    assert "surface_complexity_score" not in field_names
