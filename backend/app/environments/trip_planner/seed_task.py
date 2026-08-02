"""Seed benchmark task for the Trip Planner environment."""

from __future__ import annotations

SEED_TASK: dict[str, object] = {
    "task_id": "trip_planner-001",
    "title": "Plan and book a trip to Mumbai around a free day",
    "description": (
        "The agent must find a free day on the calendar, book the cheapest available flight to "
        "Mumbai that day (recovering when the single cheapest flight turns out to be sold out), "
        "book a hotel within budget, and pay for both."
    ),
    "environment": "trip_planner",
    "difficulty": "hard",
    "instruction": (
        "Check my calendar between 2026-08-10 and 2026-08-16 and find a day I'm free. Book the "
        "cheapest available flight to Mumbai on that day. Then find a hotel in Mumbai for under "
        "$150 a night and book the cheapest option. Finally, pay for both bookings."
    ),
    "ground_truth": {
        "expected_free_date": "2026-08-13",
        "expected_flight_id": "fl-2",
        "expected_hotel_id": "htl-2",
        "max_hotel_budget": 150.0,
        "sold_out_flight_id": "fl-1",
    },
    "expected_tool_sequence": [
        "calendar_lookup",
        "flight_search",
        "book_flight",
        "book_flight",
        "hotel_search",
        "book_hotel",
        "make_payment",
        "make_payment",
    ],
    "metadata": {"seed": True},
}
