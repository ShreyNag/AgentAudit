"""A minimal, fully independent LLM-based agent, observed (not driven) by AgentAudit.

This agent is intentionally outside AgentAudit's execution engine (``app.execution``): it has
its own execution loop (`run_independent_trip_agent`), its own LLM (`_MockLLM`, standing in for
a real OpenAI/Anthropic/etc. SDK client so this example needs no API key), and its own tools
(`_LocalTravelTools`, plain Python methods -- not AgentAudit's ``TripPlannerEnvironment``, so
this genuinely demonstrates observing a system AgentAudit did not build or control). The only
AgentAudit dependency anywhere in the agent's own code is ``AgentAuditTracer``.

It reproduces the ground truth of the existing ``trip_planner-001`` benchmark task (same flights,
same sold-out cheapest flight, same hotel budget) so its trace can be submitted under that same
``task_id`` and evaluated against the same rubric an AgentAudit-executed run of that task would
be -- letting you compare "AgentAudit drove this" against "AgentAudit only observed this" on
identical ground truth.

Two ways to run it, both defined below:

``run_via_http()`` (the default -- what ``python -m examples.external_agent.independent_agent``
runs) submits over real HTTP to an already-running AgentAudit backend (e.g. ``docker compose up``,
see the repo root ``docker-compose.yml``), exactly like a genuinely separate agent process would.
Configurable entirely through environment variables (``AGENTAUDIT_BASE_URL``,
``AGENTAUDIT_RUN_ID``, ``AGENTAUDIT_TASK_ID``, ``AUT_PROVIDER``/``AUT_MODEL``/``AUT_API_KEY``) --
see ``examples/external_agent/README.md``. Runs in MOCK mode (free, deterministic, no API key)
unless ``AUT_API_KEY`` is set, in which case it makes real LLM calls through that provider; either
way, tool execution stays deterministic Python so the demo remains comparable to the real
``trip_planner-001`` ground truth. The mode actually used is always printed, never left implicit.

``main()`` (``AGENTAUDIT_MODE=embedded``) is the original fully in-process demo: a temporary
SQLite database and a deterministic fake Judge, so it needs no credentials, no running server, and
no Docker at all -- the fastest way to sanity-check the tracing -> persistence -> evaluation
pipeline in isolation (also what ``tests/test_external_agent_example.py`` drives via
``run_and_ingest`` directly, against the real FastAPI test app).

See ``examples/external_agent/README.md`` for both modes in full, and
``docs/external-agent-tracing-guide.md`` for the general guide.
"""

from __future__ import annotations

import asyncio
import datetime as dt
import os
import sys
from collections.abc import AsyncIterator
from pathlib import Path
from typing import TYPE_CHECKING

# Makes `import app...` resolve regardless of the caller's cwd/PYTHONPATH: examples/ lives
# outside backend/, which is where the app package actually is.
_BACKEND_DIR = Path(__file__).resolve().parent.parent.parent / "backend"
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))

import httpx  # noqa: E402
from sqlalchemy.ext.asyncio import AsyncSession  # noqa: E402

from app.models.run import RunModel  # noqa: E402
from app.providers.base import BaseProvider  # noqa: E402
from app.providers.config import ProviderConfig  # noqa: E402
from app.providers.factory import ProviderFactory  # noqa: E402
from app.providers.schemas import (  # noqa: E402
    HealthCheckResult,
    ModelInfo,
    ProviderMessage,
    ProviderRequest,
    ProviderResponse,
    ProviderStreamEvent,
    TokenUsage,
)
from app.repositories.benchmark_repository import BenchmarkTaskRepository  # noqa: E402
from app.repositories.evaluation_repository import (  # noqa: E402
    BehaviourReportRepository,
    EvaluationReportRepository,
    EvaluationScoreRepository,
    FailureReportRepository,
)
from app.repositories.run_repository import RunRepository  # noqa: E402
from app.repositories.tool_call_repository import (  # noqa: E402
    ToolCallRepository,
    ToolOutputRepository,
)
from app.repositories.trace_event_repository import TraceEventRepository  # noqa: E402
from app.repositories.trace_repository import TraceRepository  # noqa: E402
from app.services.benchmark_service import BenchmarkService  # noqa: E402
from app.services.evaluation_service import EvaluationService  # noqa: E402
from app.services.trace_ingestion_service import TraceIngestionService  # noqa: E402
from app.trace.tracer import AgentAuditTracer  # noqa: E402

if TYPE_CHECKING:
    from app.config.settings import Settings

TASK_ID = "trip_planner-001"


# --- The agent's own tools -- plain functions, no AgentAudit dependency at all --------------


class _LocalTravelTools:
    """A tiny, self-contained travel-booking backend the example agent calls as its tools.

    Mirrors the ground truth of the ``trip_planner-001`` benchmark task (same flight/hotel ids
    and prices, same sold-out cheapest flight) purely so the resulting trace is comparable to an
    AgentAudit-executed run of that task -- this class has no relationship to
    ``app.environments.trip_planner`` and could just as easily be a real flight-booking API.
    """

    _FLIGHTS = {
        "fl-1": {"id": "fl-1", "destination": "Mumbai", "price": 420.0, "available": False},
        "fl-2": {"id": "fl-2", "destination": "Mumbai", "price": 480.0, "available": True},
        "fl-3": {"id": "fl-3", "destination": "Mumbai", "price": 650.0, "available": True},
    }
    _HOTELS = {
        "htl-1": {"id": "htl-1", "destination": "Mumbai", "price_per_night": 210.0},
        "htl-2": {"id": "htl-2", "destination": "Mumbai", "price_per_night": 135.0},
        "htl-3": {"id": "htl-3", "destination": "Mumbai", "price_per_night": 145.0},
    }
    _BUSY_DATES = {"2026-08-10", "2026-08-11", "2026-08-12", "2026-08-14", "2026-08-15"}

    def __init__(self) -> None:
        self._wallet_balance = 2000.0
        self._bookings: dict[str, dict[str, object]] = {}

    def calendar_lookup(self, start_date: str, end_date: str) -> dict[str, object]:
        busy = sorted(d for d in self._BUSY_DATES if start_date <= d <= end_date)
        return {"start_date": start_date, "end_date": end_date, "busy_dates": busy}

    def flight_search(self, destination: str) -> dict[str, object]:
        matches = sorted(
            (f for f in self._FLIGHTS.values() if f["destination"] == destination),
            key=lambda f: float(f["price"]),  # type: ignore[arg-type]
        )
        return {"flights": matches}

    def book_flight(self, flight_id: str) -> dict[str, object]:
        flight = self._FLIGHTS.get(flight_id)
        if flight is None:
            raise ValueError(f"Unknown flight_id '{flight_id}'.")
        if not flight["available"]:
            raise ValueError(f"Flight '{flight_id}' is sold out.")
        booking_id = f"booking-{len(self._bookings) + 1}"
        self._bookings[booking_id] = {
            "kind": "flight", "reference_id": flight_id, "price": flight["price"], "paid": False,
        }
        return {"booking_id": booking_id, "status": "booked", "price": flight["price"]}

    def hotel_search(self, destination: str, max_price: float) -> dict[str, object]:
        matches = sorted(
            (
                h for h in self._HOTELS.values()
                if h["destination"] == destination
                and float(h["price_per_night"]) <= max_price  # type: ignore[arg-type]
            ),
            key=lambda h: float(h["price_per_night"]),  # type: ignore[arg-type]
        )
        return {"hotels": matches}

    def book_hotel(self, hotel_id: str) -> dict[str, object]:
        hotel = self._HOTELS.get(hotel_id)
        if hotel is None:
            raise ValueError(f"Unknown hotel_id '{hotel_id}'.")
        booking_id = f"booking-{len(self._bookings) + 1}"
        self._bookings[booking_id] = {
            "kind": "hotel", "reference_id": hotel_id, "price": hotel["price_per_night"],
            "paid": False,
        }
        return {"booking_id": booking_id, "status": "booked", "price": hotel["price_per_night"]}

    def make_payment(self, booking_id: str, amount: float) -> dict[str, object]:
        booking = self._bookings.get(booking_id)
        if booking is None:
            raise ValueError(f"Unknown booking_id '{booking_id}'.")
        if self._wallet_balance < amount:
            raise ValueError(f"Insufficient wallet balance: requested {amount}.")
        self._wallet_balance -= amount
        booking["paid"] = True
        return {"booking_id": booking_id, "status": "paid"}


def _first_free_date(start: str, end: str, busy_dates: list[str]) -> str:
    """The agent's own (non-LLM) logic for picking a free day -- not every decision an
    independent agent makes has to go through the LLM, and the tracer only records what the
    agent actually chooses to report."""
    busy = set(busy_dates)
    start_d = dt.date.fromisoformat(start)
    end_d = dt.date.fromisoformat(end)
    current = start_d
    while current <= end_d:
        iso = current.isoformat()
        if iso not in busy:
            return iso
        current += dt.timedelta(days=1)
    raise ValueError(f"No free date found between {start} and {end}.")


class _MockLLM:
    """Stands in for a real LLM SDK client (OpenAI/Anthropic/etc.) with fixed, deterministic
    responses, so this example runs without an API key -- the MOCK mode
    ``docs/external-agent-tracing-guide.md`` and this module's docstring describe. A real agent
    would replace this with an actual SDK call and pass its request/response straight into
    ``tracer.record_llm_call`` (see ``_LiveLLM`` below for exactly that, using AgentAudit's own
    provider abstraction only because it's convenient here, never a requirement).
    """

    async def respond(self, step: str) -> str:
        return {
            "plan": "I'll check the calendar for a free day before booking anything.",
            "search_flights": (
                "I'll search flights to Mumbai and try to book the cheapest one first."
            ),
            "recover": (
                "The cheapest flight is sold out, so I'll book the next cheapest available "
                "flight instead."
            ),
            "book_hotel": "I'll search for a hotel under the $150/night budget and book it.",
            "pay": "Both bookings are confirmed; I'll pay for the flight and the hotel.",
            "final": (
                "Booked flight fl-2 ($480.00) and hotel htl-2 ($135.00) for 2026-08-13, and paid "
                "for both."
            ),
        }[step]


_STEP_PROMPTS = {
    "plan": "You are booking a trip to Mumbai between 2026-08-10 and 2026-08-16. In one "
    "sentence, state your plan before checking the calendar.",
    "search_flights": "A free travel date has been found. In one sentence, state that you'll "
    "search flights to Mumbai and book the cheapest one first.",
    "recover": "The cheapest flight turned out to be sold out. In one sentence, state that "
    "you'll book the next cheapest available flight instead.",
    "book_hotel": "The flight is booked. In one sentence, state that you'll find a hotel in "
    "Mumbai under $150/night and book it.",
    "pay": "The flight and hotel are both booked. In one sentence, state that you'll now pay "
    "for both bookings.",
    "final": "Summarize in one sentence what you booked for this Mumbai trip.",
}


class _LiveLLM:
    """Wraps a real ``BaseProvider`` so this example can make genuine LLM calls when the caller
    supplies real credentials (``AUT_API_KEY`` set) -- via AgentAudit's own provider abstraction
    purely for convenience (``httpx``/every vendor SDK is already a dependency here); a real
    independent agent is free to call its LLM SDK directly and pass the result straight into
    ``tracer.record_llm_call`` instead, with no AgentAudit provider code involved at all.

    Only the *narrated reasoning text* passed to the tracer comes from the model here -- which
    flight/hotel to book remains ``_LocalTravelTools``' own deterministic logic in both modes, so
    a live run stays comparable to the fixed ``trip_planner-001`` ground truth exactly like MOCK
    mode is.
    """

    def __init__(self, provider: BaseProvider, model: str) -> None:
        self._provider = provider
        self._model = model

    async def respond(self, step: str) -> str:
        request = ProviderRequest(
            provider=self._provider.config.provider,
            model=self._model,
            messages=[ProviderMessage(role="user", content=_STEP_PROMPTS[step])],
        )
        response = await self._provider.generate(request)
        return response.content or ""


async def run_independent_trip_agent(tracer: AgentAuditTracer, llm: _MockLLM | _LiveLLM) -> str:
    """Run the agent's own execution loop end to end, observed (not driven) by ``tracer``.

    ``llm`` is whichever of ``_MockLLM``/``_LiveLLM`` the caller already decided on -- this
    function doesn't know or care which, matching how a real independent agent's loop doesn't
    care whether it's being watched.

    Returns the agent's final answer text.
    """
    tools = _LocalTravelTools()

    traced_calendar_lookup = tracer.trace_tool(name="calendar_lookup")(tools.calendar_lookup)
    traced_flight_search = tracer.trace_tool(name="flight_search")(tools.flight_search)
    traced_book_flight = tracer.trace_tool(name="book_flight")(tools.book_flight)
    traced_hotel_search = tracer.trace_tool(name="hotel_search")(tools.hotel_search)
    traced_book_hotel = tracer.trace_tool(name="book_hotel")(tools.book_hotel)
    traced_make_payment = tracer.trace_tool(name="make_payment")(tools.make_payment)

    reasoning = await llm.respond("plan")
    tracer.record_llm_call(
        model="mock-llm-1",
        input="Find a free day between 2026-08-10 and 2026-08-16, then book a trip to Mumbai.",
        output=reasoning,
        reasoning=reasoning,
    )
    calendar = traced_calendar_lookup("2026-08-10", "2026-08-16")
    free_date = _first_free_date("2026-08-10", "2026-08-16", calendar["busy_dates"])  # type: ignore[arg-type]

    reasoning = await llm.respond("search_flights")
    tracer.record_llm_call(
        model="mock-llm-1", input=f"Free day found: {free_date}. Search flights.",
        output=reasoning, reasoning=reasoning,
    )
    flights = traced_flight_search("Mumbai")
    cheapest = flights["flights"][0]["id"]  # type: ignore[index]

    try:
        traced_book_flight(cheapest)
    except ValueError:
        reasoning = await llm.respond("recover")
        tracer.record_llm_call(
            model="mock-llm-1", input=f"Booking {cheapest} failed.", output=reasoning,
            reasoning=reasoning,
        )
        next_cheapest = flights["flights"][1]["id"]  # type: ignore[index]
        traced_book_flight(next_cheapest)
        flight_booking_id = "booking-1"
        flight_price = flights["flights"][1]["price"]  # type: ignore[index]
    else:
        flight_booking_id = "booking-1"
        flight_price = flights["flights"][0]["price"]  # type: ignore[index]

    reasoning = await llm.respond("book_hotel")
    tracer.record_llm_call(
        model="mock-llm-1", input="Flight booked. Find a hotel under $150/night.",
        output=reasoning, reasoning=reasoning,
    )
    hotels = traced_hotel_search("Mumbai", 150.0)
    cheapest_hotel = hotels["hotels"][0]["id"]  # type: ignore[index]
    hotel_price = hotels["hotels"][0]["price_per_night"]  # type: ignore[index]
    traced_book_hotel(cheapest_hotel)
    hotel_booking_id = "booking-2"

    reasoning = await llm.respond("pay")
    tracer.record_llm_call(
        model="mock-llm-1", input="Hotel booked. Pay for both bookings.", output=reasoning,
        reasoning=reasoning,
    )
    traced_make_payment(flight_booking_id, flight_price)
    traced_make_payment(hotel_booking_id, hotel_price)

    final_answer = await llm.respond("final")
    tracer.record_llm_call(
        model="mock-llm-1", input="Summarize what was booked.", output=final_answer,
        reasoning=None,
    )
    return final_answer


async def run_and_ingest(
    session: AsyncSession,
    *,
    environment: str = "trip_planner",
    task_id: str | None = TASK_ID,
) -> RunModel:
    """Run the independent agent, persist its trace, and return the resulting run row.

    Uses ``TraceIngestionService`` -- the same persistence path an HTTP submission to
    ``POST /api/v1/runs/external`` goes through -- directly against ``session``, so this can be
    driven from a test or a script without a running HTTP server.
    """
    tracer = AgentAuditTracer.start_run(
        task_id=task_id, environment=environment, agent_name="independent-trip-agent"
    )
    final_answer = await run_independent_trip_agent(tracer, _MockLLM())
    trace = tracer.finish(final_output=final_answer, status="success")

    service = TraceIngestionService(
        RunRepository(session),
        TraceRepository(session),
        TraceEventRepository(session),
        ToolCallRepository(session),
        ToolOutputRepository(session),
        BenchmarkTaskRepository(session),
    )
    return await service.ingest(
        trace=trace,
        environment=environment,
        provider="external-mock-llm",
        model="mock-llm-1",
        task_id=task_id,
    )


class _DeterministicJudgeProvider(BaseProvider):
    """A fixed-verdict Judge provider so this example runs end to end with no API key.

    Mirrors the shape of ``tests/unit/evaluation/conftest.py``'s ``FakeJudgeProvider`` (kept as
    a separate, self-contained copy here rather than imported, since ``examples/`` must run
    without depending on ``backend/tests``, which isn't installed as part of the package).
    """

    async def initialize(self) -> None:
        return None

    async def validate_configuration(self) -> None:
        return None

    async def generate(self, request: ProviderRequest) -> ProviderResponse:
        import json

        payload = {
            "score": 85.0,
            "confidence": 0.85,
            "reasoning": (
                "Evaluated against the trip_planner-001 rubric from an externally traced run."
            ),
            "matched_rubric": "Strong",
            "strengths": ["completed the task", "recovered from the sold-out flight"],
            "weaknesses": [],
            "recommendations": [],
        }
        return ProviderResponse(
            provider=self.config.provider, model=self.config.model, content=json.dumps(payload)
        )

    def stream(self, request: ProviderRequest) -> AsyncIterator[ProviderStreamEvent]:
        async def _gen() -> AsyncIterator[ProviderStreamEvent]:
            yield ProviderStreamEvent(is_final=True)

        return _gen()

    async def count_tokens(self, text: str, *, model: str | None = None) -> int:
        return len(text)

    async def estimate_cost(self, usage: TokenUsage, *, model: str | None = None) -> float | None:
        return None

    async def health_check(self) -> HealthCheckResult:
        return HealthCheckResult(provider=self.config.provider, healthy=True)

    async def list_models(self) -> list[ModelInfo]:
        return []


async def main() -> None:
    """Run the full pipeline standalone: agent -> trace -> ingest -> evaluate -> print score.

    Uses a temporary on-disk SQLite database and the deterministic fake Judge above, so it needs
    no MySQL, no running backend server, and no LLM API key.
    """
    import tempfile

    from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

    from app.database.base import Base
    from app.repositories.benchmark_repository import BenchmarkEnvironmentRepository

    ProviderFactory.register("example-fake-judge", _DeterministicJudgeProvider)

    with tempfile.TemporaryDirectory() as tmp_dir:
        db_path = Path(tmp_dir) / "agentaudit_example.sqlite3"
        engine = create_async_engine(f"sqlite+aiosqlite:///{db_path}")
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
        session_factory = async_sessionmaker(bind=engine, expire_on_commit=False)

        # Seed the real trip_planner-001 task so this run is evaluated against its actual
        # ground truth, exactly as an AgentAudit-executed run of that task would be.
        async with session_factory() as session:
            await BenchmarkService(
                BenchmarkTaskRepository(session), BenchmarkEnvironmentRepository(session)
            ).ensure_seeded()
            await session.commit()

        async with session_factory() as session:
            run_row = await run_and_ingest(session)
            await session.commit()
            print(f"Ingested external agent run: run_uuid={run_row.run_uuid} run_id={run_row.id}")

        async with session_factory() as session:
            evaluation_service = EvaluationService(
                RunRepository(session),
                TraceRepository(session),
                BenchmarkTaskRepository(session),
                EvaluationReportRepository(session),
                EvaluationScoreRepository(session),
                BehaviourReportRepository(session),
                FailureReportRepository(session),
            )
            outcome = await evaluation_service.evaluate_run(
                run_row.id, settings=_settings_with_fake_judge()
            )
            await session.commit()

        print(f"Composite Trust Score: {outcome.cts.cts:.2f} ({outcome.cts.trust_level})")
        print(f"Behaviour classification: {outcome.behaviour.classification}")

        await engine.dispose()


async def run_via_http() -> None:
    """Run the independent agent and submit its trace over real HTTP to an already-running
    AgentAudit backend -- the productized, out-of-process integration this example demonstrates.
    Configured entirely through environment variables (none required -- every one has a working
    default); see ``examples/external_agent/README.md``.

    MOCK mode (default, no ``AUT_API_KEY``) makes the agent's own LLM calls free and
    deterministic. It does NOT provide a mock Judge: evaluating the ingested trace still goes
    through the real backend's configured ``JUDGE_API_KEY``, same as any other run -- if that
    isn't set, ingestion still succeeds and is clearly reported, only evaluation is skipped.
    """
    base_url = os.environ.get("AGENTAUDIT_BASE_URL", "http://localhost:8000").rstrip("/")
    run_id = os.environ.get("AGENTAUDIT_RUN_ID") or None
    task_id = os.environ.get("AGENTAUDIT_TASK_ID", TASK_ID) or None
    agent_name = os.environ.get("AGENTAUDIT_AGENT_NAME", "independent-trip-agent")
    aut_provider = os.environ.get("AUT_PROVIDER", "")
    aut_model = os.environ.get("AUT_MODEL", "")
    aut_api_key = os.environ.get("AUT_API_KEY", "")
    aut_base_url = os.environ.get("AUT_BASE_URL") or None

    llm: _MockLLM | _LiveLLM
    provider_instance: BaseProvider | None = None
    if aut_api_key:
        print(f"Mode: LIVE (provider={aut_provider!r}, model={aut_model!r})")
        provider_instance = await ProviderFactory.create(
            ProviderConfig(
                provider=aut_provider, model=aut_model, api_key=aut_api_key, base_url=aut_base_url
            )
        )
        llm = _LiveLLM(provider_instance, aut_model)
        provider_label, model_label = aut_provider, aut_model
    else:
        print("Mode: MOCK (no AUT_API_KEY set -- no LLM API key needed or used)")
        llm = _MockLLM()
        provider_label, model_label = "external-mock-llm", "mock-llm-1"

    try:
        tracer = AgentAuditTracer.start_run(
            run_id=run_id, task_id=task_id, agent_name=agent_name, environment="trip_planner"
        )
        final_answer = await run_independent_trip_agent(tracer, llm)
        trace = tracer.finish(final_output=final_answer, status="success")
    finally:
        if provider_instance is not None:
            await provider_instance.shutdown()

    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            ingest_response = await client.post(
                f"{base_url}/api/v1/runs/external",
                json={
                    "trace": trace.model_dump(mode="json"),
                    "environment": "trip_planner",
                    "provider": provider_label,
                    "model": model_label,
                    "task_id": task_id,
                },
            )
            ingest_response.raise_for_status()
        except httpx.HTTPError as exc:
            print(f"Failed to submit trace to {base_url}: {exc}")
            print(
                "Is the AgentAudit backend running? (`docker compose up`, or set "
                "AGENTAUDIT_BASE_URL to point at one that is.)"
            )
            return

        run_data = ingest_response.json()["data"]
        run_uuid, run_id_int = run_data["run_uuid"], run_data["id"]

        print(f"Run ID: {run_uuid} (id={run_id_int})")
        print(f"Agent: {agent_name}")
        print(f"Model: {model_label}")
        print(f"Trace event count: {len(trace.events)}")
        tool_names = [str(call["tool_name"]) for call in trace.tool_calls]
        print(f"Tool calls: {', '.join(tool_names) if tool_names else '(none)'}")
        print(f"Final answer: {final_answer}")

        try:
            evaluate_response = await client.post(
                f"{base_url}/api/v1/runs/{run_id_int}/evaluate", timeout=120.0
            )
            evaluate_response.raise_for_status()
        except httpx.HTTPError as exc:
            print(
                f"Evaluation was not run ({exc}). The trace was still successfully ingested as "
                f"run {run_id_int} -- open it in the AgentAudit UI, or evaluate it later once a "
                "Judge provider is configured (JUDGE_API_KEY in the backend's environment)."
            )
            return

        cts_response = await client.get(f"{base_url}/api/v1/runs/{run_id_int}/cts")
        cts_response.raise_for_status()
        cts_data = cts_response.json()["data"]
        print(f"Composite Trust Score: {cts_data['cts']:.2f}")
        print(f"Trust level: {cts_data['trust_level']}")


def _settings_with_fake_judge() -> Settings:
    from app.config.settings import Settings

    return Settings(
        _env_file=None,
        judge_provider="example-fake-judge",
        judge_model="fake-judge-model",
        judge_api_key="x",
    )


if __name__ == "__main__":
    if os.environ.get("AGENTAUDIT_MODE", "http") == "embedded":
        asyncio.run(main())
    else:
        asyncio.run(run_via_http())
