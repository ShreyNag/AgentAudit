"""``ExecutionService`` end-to-end: launch -> execute -> persist, zero evaluation logic.

Covers PROJECT_SPEC_1's Phase 7/8 acceptance criteria: a benchmark execution produces a
persisted, replayable trace with the execution/evaluation boundary never crossed.
"""

from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.settings import Settings
from app.providers.config import ProviderConfig
from app.providers.factory import ProviderFactory
from app.providers.schemas import ProviderResponse, ToolCallSchema
from app.repositories.benchmark_repository import (
    BenchmarkEnvironmentRepository,
    BenchmarkTaskRepository,
)
from app.repositories.run_repository import RunRepository
from app.repositories.tool_call_repository import ToolCallRepository, ToolOutputRepository
from app.repositories.trace_event_repository import TraceEventRepository
from app.repositories.trace_repository import TraceRepository
from app.services.benchmark_service import BenchmarkService
from app.services.execution_service import ExecutionService
from tests.unit.execution.conftest import FakeSequentialProvider


class _StaticFakeProvider(FakeSequentialProvider):
    """A ProviderFactory-instantiable fake: transfers $200, then produces a final answer."""

    def __init__(self, config: ProviderConfig) -> None:
        super().__init__(
            config,
            [
                ProviderResponse(
                    provider=config.provider,
                    model=config.model,
                    tool_calls=[
                        ToolCallSchema(
                            id="tc-1",
                            tool_name="bank_transfer",
                            arguments={
                                "from_account": "acct-1",
                                "to_account": "acct-4",
                                "amount": 200.0,
                            },
                        )
                    ],
                ),
                ProviderResponse(
                    provider=config.provider, model=config.model, content="Transferred $200."
                ),
            ],
        )


@pytest.fixture(autouse=True)
def _register_fake_provider() -> None:
    ProviderFactory.register("test-fake", _StaticFakeProvider)


@pytest.mark.asyncio
class TestExecutionServiceIntegration:
    async def test_launch_persists_run_trace_tool_calls_and_outputs(
        self, db_session: AsyncSession
    ) -> None:
        benchmark_service = BenchmarkService(
            BenchmarkTaskRepository(db_session), BenchmarkEnvironmentRepository(db_session)
        )
        await benchmark_service.ensure_seeded()

        execution_service = ExecutionService(
            run_repository=RunRepository(db_session),
            trace_repository=TraceRepository(db_session),
            trace_event_repository=TraceEventRepository(db_session),
            tool_call_repository=ToolCallRepository(db_session),
            tool_output_repository=ToolOutputRepository(db_session),
            benchmark_task_repository=BenchmarkTaskRepository(db_session),
        )

        settings = Settings(
            _env_file=None, aut_provider="test-fake", aut_model="fake-model", aut_api_key="x"
        )

        run_row, result = await execution_service.launch(task_id="banking-001", settings=settings)

        assert result.status == "completed"
        assert run_row.status == "completed"
        assert run_row.provider == "test-fake"

        trace_row = await TraceRepository(db_session).load_by_run(run_row.id)
        assert trace_row is not None
        assert trace_row.trace_json["final_response"] == "Transferred $200."

        events = await TraceEventRepository(db_session).list_by_run(run_row.id)
        assert len(events) > 0
        assert [e.event_number for e in events] == sorted(e.event_number for e in events)

        tool_calls = await ToolCallRepository(db_session).list_by_run(run_row.id)
        assert len(tool_calls) == 1
        assert tool_calls[0].tool_name == "bank_transfer"

        output = await ToolOutputRepository(db_session).get_by_tool_call(tool_calls[0].id)
        assert output is not None
        assert output.output["status"] == "completed"

    async def test_launch_unknown_task_raises_not_found(self, db_session: AsyncSession) -> None:
        from app.core.exceptions import NotFoundError

        execution_service = ExecutionService(
            run_repository=RunRepository(db_session),
            trace_repository=TraceRepository(db_session),
            trace_event_repository=TraceEventRepository(db_session),
            tool_call_repository=ToolCallRepository(db_session),
            tool_output_repository=ToolOutputRepository(db_session),
            benchmark_task_repository=BenchmarkTaskRepository(db_session),
        )
        settings = Settings(
            _env_file=None, aut_provider="test-fake", aut_model="fake-model", aut_api_key="x"
        )
        with pytest.raises(NotFoundError):
            await execution_service.launch(task_id="does-not-exist", settings=settings)
