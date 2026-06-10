import pytest
from validators import validate_coordinates, validate_altitude, validate_waypoints


# -- validate_coordinates --------------------------------------------------- #

@pytest.mark.parametrize("lat,lon", [
    (90.001, 0.0),
    (-90.001, 0.0),
    (180.0, 0.0),
])
def test_invalid_latitude(lat, lon):
    with pytest.raises(ValueError, match="Latitude"):
        validate_coordinates(lat, lon)


@pytest.mark.parametrize("lat,lon", [
    (0.0, 180.001),
    (0.0, -180.001),
    (0.0, 270.0),
])
def test_invalid_longitude(lat, lon):
    with pytest.raises(ValueError, match="Longitude"):
        validate_coordinates(lat, lon)


@pytest.mark.parametrize("lat,lon", [
    (0.0, 0.0),
    (90.0, 180.0),
    (-90.0, -180.0),
    (1.2806, 103.8636),
])
def test_valid_coordinates_do_not_raise(lat, lon):
    validate_coordinates(lat, lon)


# -- validate_altitude ------------------------------------------------------ #

@pytest.mark.parametrize("alt", [-1, -100, 0])
def test_non_positive_altitude(alt):
    with pytest.raises(ValueError, match="greater than 0"):
        validate_altitude(alt)


@pytest.mark.parametrize("alt", [5001, 10000])
def test_altitude_exceeds_maximum(alt):
    with pytest.raises(ValueError, match="exceeds maximum"):
        validate_altitude(alt)


@pytest.mark.parametrize("alt", [1, 50, 5000])
def test_valid_altitude_does_not_raise(alt):
    validate_altitude(alt)


# -- validate_waypoints ----------------------------------------------------- #

def test_empty_waypoints_rejected():
    with pytest.raises(ValueError, match="at least 2"):
        validate_waypoints([])


def test_single_waypoint_rejected():
    with pytest.raises(ValueError, match="at least 2"):
        validate_waypoints([[1.0, 2.0]])


@pytest.mark.parametrize("bad_wp", [
    [1.0, 2.0, 3.0],  # too many elements
    [1.0],             # too few elements
    42.0,              # not a sequence at all
])
def test_malformed_waypoint_shape(bad_wp):
    with pytest.raises(ValueError):
        validate_waypoints([[1.0, 2.0], bad_wp])


def test_valid_waypoints_do_not_raise():
    validate_waypoints([[1.2806, 103.8636], [1.2810, 103.8640]])


def test_waypoints_with_invalid_coordinates_rejected():
    with pytest.raises(ValueError, match="Latitude"):
        validate_waypoints([[999.0, 103.8636], [1.2810, 103.8640]])
