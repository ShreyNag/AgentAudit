"""Trip Planner environment tools (PROJECT_SPEC_1 SS31/SS63)."""

from __future__ import annotations

from typing import Any

from app.tools.base import EnvironmentActionTool
from app.tools.registry import tool_registry


class CalendarLookupTool(EnvironmentActionTool):
    name = "calendar_lookup"
    description = "Look up busy dates within a date range."
    environment_name = "trip_planner"
    action_name = "calendar_lookup"

    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "start_date": {"type": "string"},
                "end_date": {"type": "string"},
            },
            "required": ["start_date", "end_date"],
        }


class FlightSearchTool(EnvironmentActionTool):
    name = "flight_search"
    description = "Search available flights to a destination, cheapest first."
    environment_name = "trip_planner"
    action_name = "flight_search"

    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {"destination": {"type": "string"}},
            "required": ["destination"],
        }


class BookFlightTool(EnvironmentActionTool):
    name = "book_flight"
    description = "Book a flight by id."
    environment_name = "trip_planner"
    action_name = "book_flight"

    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {"flight_id": {"type": "string"}},
            "required": ["flight_id"],
        }


class HotelSearchTool(EnvironmentActionTool):
    name = "hotel_search"
    description = "Search hotels in a destination at or under a nightly price."
    environment_name = "trip_planner"
    action_name = "hotel_search"

    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "destination": {"type": "string"},
                "max_price": {"type": "number"},
            },
            "required": ["destination", "max_price"],
        }


class BookHotelTool(EnvironmentActionTool):
    name = "book_hotel"
    description = "Book a hotel by id."
    environment_name = "trip_planner"
    action_name = "book_hotel"

    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {"hotel_id": {"type": "string"}},
            "required": ["hotel_id"],
        }


class MakePaymentTool(EnvironmentActionTool):
    name = "make_payment"
    description = "Pay for a booking by id."
    environment_name = "trip_planner"
    action_name = "make_payment"

    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "booking_id": {"type": "string"},
                "amount": {"type": "number"},
            },
            "required": ["booking_id", "amount"],
        }


def register() -> None:
    """Register every Trip Planner tool factory on the shared tool registry."""
    tool_registry.register("calendar_lookup", CalendarLookupTool)
    tool_registry.register("flight_search", FlightSearchTool)
    tool_registry.register("book_flight", BookFlightTool)
    tool_registry.register("hotel_search", HotelSearchTool)
    tool_registry.register("book_hotel", BookHotelTool)
    tool_registry.register("make_payment", MakePaymentTool)
