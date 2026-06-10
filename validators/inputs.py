from __future__ import annotations


def validate_coordinates(lat: float, lon: float) -> None:
    if not (-90 <= lat <= 90):
        raise ValueError(f"Latitude {lat} out of range [-90, 90].")
    if not (-180 <= lon <= 180):
        raise ValueError(f"Longitude {lon} out of range [-180, 180].")


def validate_altitude(altitude_m: int | float) -> None:
    if altitude_m <= 0:
        raise ValueError(f"Altitude {altitude_m}m must be greater than 0.")
    if altitude_m > 5000:
        raise ValueError(f"Altitude {altitude_m}m exceeds maximum of 5000m.")


def validate_waypoints(waypoints: list) -> None:
    if len(waypoints) < 2:
        raise ValueError(
            f"Route requires at least 2 waypoints, got {len(waypoints)}."
        )
    for i, wp in enumerate(waypoints):
        if not hasattr(wp, "__len__") or len(wp) != 2:
            raise ValueError(
                f"Waypoint {i} must contain exactly [lat, lon], got: {wp!r}."
            )
        validate_coordinates(float(wp[0]), float(wp[1]))
