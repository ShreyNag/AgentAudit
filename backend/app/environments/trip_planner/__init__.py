"""Trip Planner benchmark environment (PROJECT_SPEC_1 SS29/SS56).

Calendar, flight, hotel, and payment across a single long-horizon task -- merges the former
Travel and Calendar environments into one multi-tool planning benchmark.
"""

from app.benchmark.models import BenchmarkEnvironmentMeta
from app.benchmark.registry import benchmark_registry
from app.environments.registry import environment_registry
from app.environments.trip_planner.environment import TripPlannerEnvironment

TOOLSET = [
    "calendar_lookup",
    "flight_search",
    "book_flight",
    "hotel_search",
    "book_hotel",
    "make_payment",
]


def register() -> None:
    """Register the Trip Planner environment factory and its descriptive metadata."""
    environment_registry.register("trip_planner", TripPlannerEnvironment)
    benchmark_registry.register(
        BenchmarkEnvironmentMeta(
            name="trip_planner",
            description=(
                "Calendar-aware flight and hotel booking with payment; the long-horizon "
                "multi-tool planning benchmark."
            ),
            toolset=TOOLSET,
        )
    )


__all__ = ["TripPlannerEnvironment", "register", "TOOLSET"]
