import pytest
from src.data_layer import AirspaceDB
from workflows import run_preflight_check

db = AirspaceDB()

OPEN_MARINA = [1.2806, 103.8636]
NEARBY_OPEN = [1.2810, 103.8640]
CHANGI      = [1.3644, 103.9915]

EXPECTED_KEYS = {
    "status",
    "checked_altitude_m",
    "total_distance_km",
    "violations",
    "waypoint_constraints",
    "recommendation",
}


# -- Approved path ---------------------------------------------------------- #

def test_approved_workflow_status():
    result = run_preflight_check(db, [OPEN_MARINA, NEARBY_OPEN], altitude_m=50)
    assert result["status"] == "approved"


def test_approved_workflow_has_no_violations():
    result = run_preflight_check(db, [OPEN_MARINA, NEARBY_OPEN], altitude_m=50)
    assert result["violations"] == []


# -- Rejected path ---------------------------------------------------------- #

def test_rejected_workflow_status():
    result = run_preflight_check(db, [OPEN_MARINA, CHANGI], altitude_m=50)
    assert result["status"] == "rejected"


def test_rejected_workflow_has_violations():
    result = run_preflight_check(db, [OPEN_MARINA, CHANGI], altitude_m=50)
    assert len(result["violations"]) >= 1


# -- Schema ----------------------------------------------------------------- #

def test_workflow_returns_expected_keys():
    result = run_preflight_check(db, [OPEN_MARINA, NEARBY_OPEN], altitude_m=50)
    assert set(result.keys()) == EXPECTED_KEYS


def test_recommendation_is_non_empty():
    result = run_preflight_check(db, [OPEN_MARINA, NEARBY_OPEN], altitude_m=50)
    assert len(result["recommendation"]) > 0


def test_checked_altitude_matches_input():
    result = run_preflight_check(db, [OPEN_MARINA, NEARBY_OPEN], altitude_m=50)
    assert result["checked_altitude_m"] == 50


def test_waypoint_constraints_count_matches_waypoint_count():
    waypoints = [OPEN_MARINA, [1.2808, 103.8638], NEARBY_OPEN]
    result = run_preflight_check(db, waypoints, altitude_m=40)
    assert len(result["waypoint_constraints"]) == 3


def test_total_distance_km_is_non_negative():
    result = run_preflight_check(db, [OPEN_MARINA, NEARBY_OPEN], altitude_m=50)
    assert result["total_distance_km"] >= 0


def test_total_distance_km_rounded_to_two_decimal_places():
    result = run_preflight_check(db, [OPEN_MARINA, NEARBY_OPEN], altitude_m=50)
    assert result["total_distance_km"] == round(result["total_distance_km"], 2)


# -- Invalid inputs --------------------------------------------------------- #

def test_single_waypoint_raises_value_error():
    with pytest.raises(ValueError):
        run_preflight_check(db, [OPEN_MARINA], altitude_m=50)


def test_empty_waypoints_raises_value_error():
    with pytest.raises(ValueError):
        run_preflight_check(db, [], altitude_m=50)


def test_zero_altitude_raises_value_error():
    with pytest.raises(ValueError):
        run_preflight_check(db, [OPEN_MARINA, NEARBY_OPEN], altitude_m=0)


def test_negative_altitude_raises_value_error():
    with pytest.raises(ValueError):
        run_preflight_check(db, [OPEN_MARINA, NEARBY_OPEN], altitude_m=-10)


def test_altitude_over_maximum_raises_value_error():
    with pytest.raises(ValueError):
        run_preflight_check(db, [OPEN_MARINA, NEARBY_OPEN], altitude_m=5001)
