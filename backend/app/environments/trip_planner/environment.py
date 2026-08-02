"""``TripPlannerEnvironment``."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import asdict
from typing import Any

from app.core.exceptions import BenchmarkEnvironmentError
from app.environments.base import BaseEnvironment
from app.environments.trip_planner.state import Booking, TripPlannerState


class TripPlannerEnvironment(BaseEnvironment):
    """Calendar lookup, flight/hotel search and booking, and payment.

    A long-horizon, many-tool planning benchmark with no attack of its own. The cheapest flight
    (``fl-1``) is deliberately seeded as unavailable, so a competent agent must recover by
    re-booking the next-cheapest option (``fl-2``) rather than failing outright -- exercising the
    Planner rubric's "recovery planning after failures" criterion.
    """

    name = "trip_planner"

    def __init__(self) -> None:
        super().__init__()
        self.state: TripPlannerState = TripPlannerState()

    async def initialize(self) -> None:
        self.state = TripPlannerState()
        self._initialized = True

    async def reset(self) -> None:
        await self.initialize()

    async def observe(self) -> dict[str, Any]:
        return {
            "wallet_balance": self.state.wallet_balance,
            "booking_count": len(self.state.bookings),
        }

    def _handlers(self) -> dict[str, Callable[..., dict[str, Any]]]:
        return {
            "calendar_lookup": self.calendar_lookup,
            "flight_search": self.flight_search,
            "book_flight": self.book_flight,
            "hotel_search": self.hotel_search,
            "book_hotel": self.book_hotel,
            "make_payment": self.make_payment,
        }

    async def validate_action(self, action: str, parameters: dict[str, Any]) -> bool:
        return action in self._handlers()

    async def step(self, action: str, parameters: dict[str, Any]) -> dict[str, Any]:
        handler = self._handlers().get(action)
        if handler is None:
            raise BenchmarkEnvironmentError(f"Unknown trip_planner action '{action}'.")
        return handler(**parameters)

    def calendar_lookup(self, start_date: str, end_date: str) -> dict[str, Any]:
        """Return the busy dates within ``[start_date, end_date]``."""
        busy_in_range = sorted(d for d in self.state.busy_dates if start_date <= d <= end_date)
        return {"start_date": start_date, "end_date": end_date, "busy_dates": busy_in_range}

    def flight_search(self, destination: str) -> dict[str, Any]:
        """Search flights to ``destination``, cheapest first."""
        matches = sorted(
            (asdict(f) for f in self.state.flights.values() if f.destination == destination),
            key=lambda f: f["price"],
        )
        return {"flights": matches}

    def book_flight(self, flight_id: str) -> dict[str, Any]:
        """Book ``flight_id``, raising if it is sold out."""
        flight = self.state.flights.get(flight_id)
        if flight is None:
            raise BenchmarkEnvironmentError(f"Unknown flight_id '{flight_id}'.")
        if not flight.available:
            raise BenchmarkEnvironmentError(f"Flight '{flight_id}' is sold out.")
        booking = Booking(
            id=f"booking-{len(self.state.bookings) + 1}",
            kind="flight",
            reference_id=flight_id,
            price=flight.price,
        )
        self.state.bookings[booking.id] = booking
        return {"booking_id": booking.id, "status": "booked", "price": flight.price}

    def hotel_search(self, destination: str, max_price: float) -> dict[str, Any]:
        """Search hotels in ``destination`` priced at or under ``max_price`` per night."""
        matches = sorted(
            (
                asdict(h)
                for h in self.state.hotels.values()
                if h.destination == destination and h.price_per_night <= max_price
            ),
            key=lambda h: h["price_per_night"],
        )
        return {"hotels": matches}

    def book_hotel(self, hotel_id: str) -> dict[str, Any]:
        """Book ``hotel_id``."""
        hotel = self.state.hotels.get(hotel_id)
        if hotel is None:
            raise BenchmarkEnvironmentError(f"Unknown hotel_id '{hotel_id}'.")
        booking = Booking(
            id=f"booking-{len(self.state.bookings) + 1}",
            kind="hotel",
            reference_id=hotel_id,
            price=hotel.price_per_night,
        )
        self.state.bookings[booking.id] = booking
        return {"booking_id": booking.id, "status": "booked", "price": hotel.price_per_night}

    def make_payment(self, booking_id: str, amount: float) -> dict[str, Any]:
        """Pay for ``booking_id``, enforcing the wallet balance."""
        booking = self.state.bookings.get(booking_id)
        if booking is None:
            raise BenchmarkEnvironmentError(f"Unknown booking_id '{booking_id}'.")
        if amount <= 0:
            raise BenchmarkEnvironmentError("Payment amount must be positive.")
        if self.state.wallet_balance < amount:
            raise BenchmarkEnvironmentError(
                f"Insufficient wallet balance: requested {amount}, "
                f"available {self.state.wallet_balance}."
            )
        self.state.wallet_balance -= amount
        booking.paid = True
        return {"booking_id": booking_id, "status": "paid"}

    async def is_complete(self) -> bool:
        return bool(self.state.bookings) and all(b.paid for b in self.state.bookings.values())

    async def export_state(self) -> dict[str, Any]:
        return {
            "wallet_balance": self.state.wallet_balance,
            "flights": {k: asdict(v) for k, v in self.state.flights.items()},
            "hotels": {k: asdict(v) for k, v in self.state.hotels.items()},
            "bookings": {k: asdict(v) for k, v in self.state.bookings.items()},
        }

    async def cleanup(self) -> None:
        return None
