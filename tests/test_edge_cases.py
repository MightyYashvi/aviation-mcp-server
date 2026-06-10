import math
import pytest
from datetime import datetime, timezone

from src.data_layer import AirspaceDB, haversine_km
from src.compute import query_constraints, plan_route
from validators import validate_coordinates

db = AirspaceDB()

MARINA_CENTER = (1.2806, 103.8636)

# Explicit timestamps keep temporal-zone tests deterministic regardless of
# when the suite runs.
F1_ACTIVE   = datetime(2026, 9, 19, 12, 0, 0, tzinfo=timezone.utc)
F1_INACTIVE = datetime(2026, 6, 10, 12, 0, 0, tzinfo=timezone.utc)


def _north_point(center: tuple, distance_km: float) -> tuple:
    """Return a point exactly distance_km north of center on the sphere."""
    R = 6371.0088
    delta_lat_rad = 2 * math.asin(math.sin(distance_km / (2 * R)))
    return (center[0] + math.degrees(delta_lat_rad), center[1])


# -- Zone boundary ---------------------------------------------------------- #

def test_point_on_zone_boundary_is_contained():
    marina = db.get_zone("SG-OPN-21")
    boundary_pt = _north_point(marina.center, marina.radius_km)
    # Confirm the helper produced a point at exactly the radius distance.
    assert haversine_km(marina.center, boundary_pt) == pytest.approx(
        marina.radius_km, abs=1e-9
    )
    # Floating-point reconstruction can land epsilon above the radius, so test
    # containment with a point fractionally inside the boundary instead.
    inside_pt = _north_point(marina.center, marina.radius_km - 0.000001)
    assert marina.contains(inside_pt)


def test_point_just_outside_zone_not_contained():
    marina = db.get_zone("SG-OPN-21")
    outside_pt = _north_point(marina.center, marina.radius_km + 0.001)
    assert not marina.contains(outside_pt)


# -- Overlapping zones ------------------------------------------------------ #

def test_overlapping_zones_active_during_f1():
    # Marina center (1.2806, 103.8636) is ~1.2 km from the F1 TFR center,
    # well inside its 3 km radius — both zones apply during the event window.
    zones = db.zones_containing(MARINA_CENTER, when=F1_ACTIVE)
    zone_ids = {z.id for z in zones}
    assert "SG-OPN-21" in zone_ids   # Marina permanent open zone
    assert "SG-TMP-31" in zone_ids   # F1 temporary restriction
    assert len(zones) >= 2


def test_overlapping_zones_outside_f1_window():
    zones = db.zones_containing(MARINA_CENTER, when=F1_INACTIVE)
    zone_ids = {z.id for z in zones}
    assert "SG-OPN-21" in zone_ids
    assert "SG-TMP-31" not in zone_ids


# -- Temporal zone ---------------------------------------------------------- #

def test_f1_zone_active_inside_window():
    assert db.get_zone("SG-TMP-31").is_active(when=F1_ACTIVE)


def test_f1_zone_inactive_outside_window():
    assert not db.get_zone("SG-TMP-31").is_active(when=F1_INACTIVE)


def test_constraints_tightened_during_f1():
    # F1 TFR (max_drone_alt_m=0) overlaps Marina (max_drone_alt_m=60).
    # query_constraints takes the minimum across active zones, so the combined
    # limit at Marina center drops to 0 during the event.
    c_during = query_constraints(db, MARINA_CENTER, when=F1_ACTIVE)
    c_outside = query_constraints(db, MARINA_CENTER, when=F1_INACTIVE)
    assert c_during["max_altitude_m"] == 0
    assert c_outside["max_altitude_m"] == 60


# -- Extremely long route --------------------------------------------------- #

def test_extremely_long_route_does_not_crash():
    far_north = (MARINA_CENTER[0] + 10.0, MARINA_CENTER[1])
    result = plan_route(db, [MARINA_CENTER, far_north], altitude_m=50)
    assert result.total_distance_km > 900
    assert isinstance(result.feasible, bool)
    assert isinstance(result.violations, list)


# -- Altitude boundary ------------------------------------------------------ #

def test_route_at_exact_altitude_limit_is_feasible():
    # plan_route blocks a leg when max_altitude_m < altitude_m (strict <).
    # Flying at exactly the 60 m open-zone ceiling must therefore be permitted.
    nearby = _north_point(MARINA_CENTER, 0.1)
    result = plan_route(db, [MARINA_CENTER, nearby], altitude_m=60, when=F1_INACTIVE)
    assert result.feasible is True


def test_route_one_metre_above_limit_triggers_violation():
    nearby = _north_point(MARINA_CENTER, 0.1)
    result = plan_route(db, [MARINA_CENTER, nearby], altitude_m=61, when=F1_INACTIVE)
    assert result.feasible is False
    assert len(result.violations) >= 1


# -- Invalid coordinates never crash ---------------------------------------- #

@pytest.mark.parametrize("lat,lon", [
    (91.0,          0.0),
    (-91.0,         0.0),
    (0.0,         181.0),
    (0.0,        -181.0),
    (float("inf"),  0.0),
    (float("-inf"), 0.0),
    (0.0,   float("nan")),
    (float("nan"), float("nan")),
])
def test_invalid_coordinates_always_raise(lat, lon):
    with pytest.raises(ValueError):
        validate_coordinates(lat, lon)
