import json
from src.data_layer import AirspaceDB
from workflows import run_preflight_check


def section(title: str) -> None:
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print('=' * 60)


def main() -> None:
    db = AirspaceDB()

    # ------------------------------------------------------------------ #
    # Example 1: Approved route
    # Short hop within Marina Recreational Open Area at 50 m AGL.
    # ------------------------------------------------------------------ #
    section("EXAMPLE 1 — Approved Route (Marina Open Area, 50 m AGL)")

    approved = run_preflight_check(
        db,
        waypoints=[[1.2806, 103.8636], [1.2810, 103.8640]],
        altitude_m=50,
    )
    print(json.dumps(approved, indent=2))

    # ------------------------------------------------------------------ #
    # Example 2: Rejected route
    # Route from Marina open area into Changi Control Zone — no-fly.
    # ------------------------------------------------------------------ #
    section("EXAMPLE 2 — Rejected Route (Marina → Changi Control Zone, 50 m AGL)")

    rejected = run_preflight_check(
        db,
        waypoints=[[1.2806, 103.8636], [1.3644, 103.9915]],
        altitude_m=50,
    )
    print(json.dumps(rejected, indent=2))


if __name__ == "__main__":
    main()
