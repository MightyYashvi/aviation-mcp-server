from __future__ import annotations

from src.compute import query_constraints, plan_route
from src.data_layer import AirspaceDB
from validators import validate_waypoints, validate_altitude


def run_preflight_check(
    db: AirspaceDB,
    waypoints: list[list[float]],
    altitude_m: int,
) -> dict:
    """Multi-step pre-flight workflow: validate → per-waypoint constraints
    → route feasibility → structured go/no-go summary.

    Orchestration only. All computation delegates to src.compute.
    """
    validate_waypoints(waypoints)
    validate_altitude(altitude_m)

    pts = [(float(wp[0]), float(wp[1])) for wp in waypoints]
    waypoint_constraints = [query_constraints(db, pt) for pt in pts]
    route = plan_route(db, pts, altitude_m)

    total_distance_km = round(route.total_distance_km, 2)

    if route.feasible:
        status = "approved"
        recommendation = (
            f"Route approved: {len(waypoints)} waypoints, "
            f"{total_distance_km}km at {altitude_m}m AGL. "
            f"No airspace violations detected."
        )
    else:
        status = "rejected"
        reasons = "; ".join(v["reason"] for v in route.violations)
        recommendation = (
            f"Route rejected: {len(route.violations)} violation(s). {reasons}"
        )

    return {
        "status": status,
        "checked_altitude_m": altitude_m,
        "total_distance_km": total_distance_km,
        "violations": route.violations,
        "waypoint_constraints": waypoint_constraints,
        "recommendation": recommendation,
    }
