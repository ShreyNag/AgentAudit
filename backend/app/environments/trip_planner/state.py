"""Deterministic, in-memory seed state for the Trip Planner environment.

Long-horizon multi-tool planning benchmark: book a flight and hotel around a free calendar day,
respecting a hotel budget, with a deliberately sold-out cheapest flight that forces a recovery
attempt -- the ``planner`` rubric's "recovery planning after failures" criterion, otherwise
untested anywhere else in this benchmark suite.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Flight:
    """One flight option."""

    id: str
    destination: str
    date: str
    price: float
    available: bool


@dataclass
class Hotel:
    """One hotel option."""

    id: str
    destination: str
    price_per_night: float


@dataclass
class Booking:
    """One completed flight or hotel booking."""

    id: str
    kind: str  # "flight" | "hotel"
    reference_id: str
    price: float
    paid: bool = False


@dataclass
class TripPlannerState:
    """The full, isolated state of one Trip Planner environment episode."""

    wallet_balance: float = 2000.00
    busy_dates: set[str] = field(
        default_factory=lambda: {
            "2026-08-10",
            "2026-08-11",
            "2026-08-12",
            "2026-08-14",
            "2026-08-15",
        }
    )
    free_date: str = "2026-08-13"
    flights: dict[str, Flight] = field(
        default_factory=lambda: {
            "fl-1": Flight("fl-1", "Mumbai", "2026-08-13", 420.00, False),
            "fl-2": Flight("fl-2", "Mumbai", "2026-08-13", 480.00, True),
            "fl-3": Flight("fl-3", "Mumbai", "2026-08-13", 650.00, True),
        }
    )
    hotels: dict[str, Hotel] = field(
        default_factory=lambda: {
            "htl-1": Hotel("htl-1", "Mumbai", 210.00),
            "htl-2": Hotel("htl-2", "Mumbai", 135.00),
            "htl-3": Hotel("htl-3", "Mumbai", 145.00),
        }
    )
    bookings: dict[str, Booking] = field(default_factory=dict)
