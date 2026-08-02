"""``ReplayLoader`` reconstructs a trace from persisted rows without invoking a provider."""

from __future__ import annotations

import datetime as dt
import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.benchmark_repository import BenchmarkTaskRepository
from app.repositories.run_repository import RunRepository
from app.repositories.trace_event_repository import TraceEventRepository
from app.repositories.trace_repository import TraceRepository
from app.trace.replay import ReplayLoader


@pytest.mark.asyncio
class TestReplayLoader:
    async def test_load_reconstructs_trace_and_ordered_events(
        self, db_session: AsyncSession
    ) -> None:
        task = await BenchmarkTaskRepository(db_session).create(
            task_id="travel-001",
            title="t",
            description="d",
            environment="travel",
            difficulty="easy",
            instruction="book it",
            ground_truth={"x": 1},
            expected_tool_sequence=[],
            task_metadata={},
        )
        run = await RunRepository(db_session).create(
            run_uuid=str(uuid.uuid4()),
            benchmark_task_id=task.id,
            provider="anthropic",
            model="claude-sonnet-5",
            environment="travel",
            status="completed",
        )
        await TraceRepository(db_session).save_trace(
            run.id,
            trace_json={"final_response": "Booked."},
            planner={"planner_available": False},
            reasoning={"reasoning_available": False},
            messages=[],
            trace_metadata={},
            statistics={},
        )
        now = dt.datetime.now(dt.UTC)
        await TraceEventRepository(db_session).bulk_create(
            [
                {
                    "run_id": run.id,
                    "event_number": 2,
                    "timestamp": now,
                    "event_type": "RunCompleted",
                    "component": "runner",
                    "payload": {},
                },
                {
                    "run_id": run.id,
                    "event_number": 1,
                    "timestamp": now,
                    "event_type": "RunStarted",
                    "component": "runner",
                    "payload": {},
                },
            ]
        )

        loader = ReplayLoader(TraceRepository(db_session), TraceEventRepository(db_session))
        replayed = await loader.load(run.id)

        assert replayed.final_response == "Booked."
        assert [e.sequence_number for e in replayed.events] == [1, 2]  # always chronological

    async def test_load_raises_trace_error_when_no_trace_persisted(
        self, db_session: AsyncSession
    ) -> None:
        from app.core.exceptions import TraceError

        loader = ReplayLoader(TraceRepository(db_session), TraceEventRepository(db_session))
        with pytest.raises(TraceError):
            await loader.load(999)
