"""Exercise the full runs -> execution_traces -> trace_events -> tool_calls -> tool_outputs
chain that Phases 7-8 will drive at runtime, verifying foreign keys and ordering hold up.
"""

from __future__ import annotations

import datetime as dt
import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.benchmark_repository import BenchmarkTaskRepository
from app.repositories.run_repository import RunRepository
from app.repositories.tool_call_repository import ToolCallRepository, ToolOutputRepository
from app.repositories.trace_event_repository import TraceEventRepository
from app.repositories.trace_repository import TraceRepository


@pytest.mark.asyncio
class TestRunLifecyclePersistence:
    async def _make_run(self, db_session: AsyncSession) -> int:
        task_repo = BenchmarkTaskRepository(db_session)
        task = await task_repo.create(
            task_id="travel-001",
            title="Book a flight",
            description="Book the cheapest round trip flight.",
            environment="travel",
            difficulty="easy",
            instruction="Book a flight from NYC to SF.",
            ground_truth={"expected_flight": "AA100"},
            expected_tool_sequence=["flight_search", "book_flight"],
            task_metadata={},
        )
        run_repo = RunRepository(db_session)
        run = await run_repo.create(
            run_uuid=str(uuid.uuid4()),
            benchmark_task_id=task.id,
            provider="anthropic",
            model="claude-sonnet-5",
            environment="travel",
            status="running",
        )
        return run.id

    async def test_run_status_transitions(self, db_session: AsyncSession) -> None:
        run_id = await self._make_run(db_session)
        run_repo = RunRepository(db_session)
        updated = await run_repo.update_status(run_id, "completed")
        assert updated is not None
        assert updated.status == "completed"

    async def test_trace_and_events_persist_in_order(self, db_session: AsyncSession) -> None:
        run_id = await self._make_run(db_session)

        trace_repo = TraceRepository(db_session)
        await trace_repo.save_trace(
            run_id,
            trace_json={"final_response": "Booked AA100"},
            planner={"planner_available": False},
            reasoning={"reasoning_available": False},
            messages=[],
            trace_metadata={},
            statistics={},
        )
        assert await trace_repo.exists_for_run(run_id) is True

        event_repo = TraceEventRepository(db_session)
        now = dt.datetime.now(dt.UTC)
        await event_repo.bulk_create(
            [
                {
                    "run_id": run_id,
                    "event_number": 1,
                    "timestamp": now,
                    "event_type": "RunStarted",
                    "component": "runner",
                    "payload": {},
                },
                {
                    "run_id": run_id,
                    "event_number": 2,
                    "timestamp": now,
                    "event_type": "ToolInvoked",
                    "component": "tool_registry",
                    "payload": {"tool": "flight_search"},
                },
            ]
        )
        events = await event_repo.list_by_run(run_id)
        assert [e.event_number for e in events] == [1, 2]

    async def test_tool_call_and_output_link_correctly(self, db_session: AsyncSession) -> None:
        run_id = await self._make_run(db_session)
        tool_call_repo = ToolCallRepository(db_session)
        tool_output_repo = ToolOutputRepository(db_session)

        call = await tool_call_repo.create(
            run_id=run_id,
            tool_name="flight_search",
            arguments={"origin": "NYC", "destination": "SF"},
            validated_arguments={"origin": "NYC", "destination": "SF"},
            execution_order=1,
            status="completed",
        )
        await tool_output_repo.create(
            tool_call_id=call.id,
            output={"flights": ["AA100"]},
            ground_truth={"expected_flight": "AA100"},
            correct=True,
            output_metadata={},
        )

        output = await tool_output_repo.get_by_tool_call(call.id)
        assert output is not None
        assert output.correct is True

        calls_in_order = await tool_call_repo.list_by_run(run_id)
        assert len(calls_in_order) == 1
        assert calls_in_order[0].execution_order == 1
