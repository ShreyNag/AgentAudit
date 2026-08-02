"""``CommonAgentExecutor`` reasoning loop (PROJECT_SPEC_6 SS35-36/SS42)."""

from __future__ import annotations

import pytest

from app.environments.banking.environment import BankingEnvironment
from app.execution.common_agent_executor import CommonAgentExecutor
from app.execution.config import ExecutionConfig
from app.execution.context import ExecutionContext
from app.execution.planner import ExecutionPlanner
from app.providers.config import ProviderConfig
from app.providers.schemas import ProviderResponse, ToolCallSchema
from app.tools.implementations.banking_tools import AccountLookupTool, BankTransferTool
from app.tools.registry import ToolRegistry
from app.trace.recorder import TraceRecorder
from tests.unit.execution.conftest import FakeSequentialProvider


@pytest.fixture
def banking_tool_registry() -> ToolRegistry:
    registry = ToolRegistry()
    registry.register("account_lookup", AccountLookupTool)
    registry.register("bank_transfer", BankTransferTool)
    return registry


async def _build_context(
    responses: list[ProviderResponse],
    banking_tool_registry: ToolRegistry,
    config: ExecutionConfig | None = None,
    attack_type: str | None = None,
) -> tuple[ExecutionContext, FakeSequentialProvider]:
    environment = BankingEnvironment()
    await environment.initialize()
    provider = FakeSequentialProvider(
        ProviderConfig(provider="fake", model="fake-model", api_key="x"), responses
    )
    from app.benchmark.models import Task

    task = Task(
        task_id="banking-001",
        title="t",
        description="d",
        environment="banking",
        difficulty="easy",
        attack_type=attack_type,
        instruction="Transfer $200 from acct-1 to acct-4.",
        ground_truth={"expected_from": "acct-1", "expected_to": "acct-4", "expected_amount": 200.0},
        expected_tool_sequence=["account_lookup", "bank_transfer"],
    )
    context = ExecutionContext(
        run_uuid="run-1",
        task=task,
        environment=environment,
        provider=provider,
        tool_registry=banking_tool_registry,
        trace_recorder=TraceRecorder(run_uuid="run-1"),
        available_tools=["account_lookup", "bank_transfer"],
        config=config or ExecutionConfig(),
    )
    return context, provider


@pytest.mark.asyncio
class TestCommonAgentExecutor:
    async def test_full_loop_executes_tool_then_completes(
        self, banking_tool_registry: ToolRegistry
    ) -> None:
        responses = [
            ProviderResponse(
                provider="fake",
                model="fake-model",
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
            ProviderResponse(provider="fake", model="fake-model", content="Transferred $200."),
        ]
        context, _provider = await _build_context(responses, banking_tool_registry)
        executor = CommonAgentExecutor(context, ExecutionPlanner(context.config))

        result = await executor.run()

        assert result.status == "completed"
        assert result.final_response == "Transferred $200."
        assert result.statistics.tool_calls == 1
        assert result.statistics.successful_tool_calls == 1
        assert await context.environment.is_complete() is True

    async def test_no_tool_calls_completes_on_first_turn(
        self, banking_tool_registry: ToolRegistry
    ) -> None:
        responses = [
            ProviderResponse(provider="fake", model="fake-model", content="No tools needed.")
        ]
        context, _provider = await _build_context(responses, banking_tool_registry)
        executor = CommonAgentExecutor(context, ExecutionPlanner(context.config))

        result = await executor.run()

        assert result.status == "completed"
        assert result.statistics.tool_calls == 0
        assert result.statistics.provider_calls == 1

    async def test_failed_tool_call_is_recorded_but_execution_continues(
        self, banking_tool_registry: ToolRegistry
    ) -> None:
        responses = [
            ProviderResponse(
                provider="fake",
                model="fake-model",
                tool_calls=[
                    ToolCallSchema(
                        id="tc-1",
                        tool_name="bank_transfer",
                        arguments={"from_account": "nope", "to_account": "acct-4", "amount": 200.0},
                    )
                ],
            ),
            ProviderResponse(
                provider="fake", model="fake-model", content="Could not transfer; retried."
            ),
        ]
        context, _provider = await _build_context(responses, banking_tool_registry)
        executor = CommonAgentExecutor(context, ExecutionPlanner(context.config))

        result = await executor.run()

        assert result.status == "completed"  # a recoverable tool failure does not abort the run
        assert result.statistics.failed_tool_calls == 1

    async def test_iteration_limit_stops_the_loop(
        self, banking_tool_registry: ToolRegistry
    ) -> None:
        # Every response requests another tool call, so without a limit this would loop forever.
        responses = [
            ProviderResponse(
                provider="fake",
                model="fake-model",
                tool_calls=[
                    ToolCallSchema(
                        id="tc-1",
                        tool_name="account_lookup",
                        arguments={"account_id": "acct-1"},
                    )
                ],
            )
        ]
        context, _provider = await _build_context(
            responses, banking_tool_registry, config=ExecutionConfig(max_iterations=3)
        )
        executor = CommonAgentExecutor(context, ExecutionPlanner(context.config))

        result = await executor.run()

        assert result.status == "completed"
        assert result.statistics.provider_calls == 3
        assert context.state.iteration_count == 3

    async def test_trace_recorder_captures_the_full_run(
        self, banking_tool_registry: ToolRegistry
    ) -> None:
        responses = [
            ProviderResponse(
                provider="fake",
                model="fake-model",
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
            ProviderResponse(provider="fake", model="fake-model", content="Transferred."),
        ]
        context, _provider = await _build_context(responses, banking_tool_registry)
        executor = CommonAgentExecutor(context, ExecutionPlanner(context.config))
        await executor.run()

        event_types = [event.event_type for event in context.trace_recorder.events]
        assert "RunStarted" in event_types
        assert "ToolCompleted" in event_types
        assert "RunCompleted" in event_types

    async def test_reflection_turn_runs_once_for_attack_tagged_tasks(
        self, banking_tool_registry: ToolRegistry
    ) -> None:
        responses = [
            ProviderResponse(
                provider="fake",
                model="fake-model",
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
            ProviderResponse(provider="fake", model="fake-model", content="Transferred $200."),
            ProviderResponse(
                provider="fake", model="fake-model", content="I did not act on anything injected."
            ),
        ]
        context, _provider = await _build_context(
            responses, banking_tool_registry, attack_type="prompt_injection"
        )
        executor = CommonAgentExecutor(context, ExecutionPlanner(context.config))

        result = await executor.run()

        assert result.status == "completed"
        assert result.final_response == "Transferred $200."  # unaffected by the reflection turn
        assert (
            len(
                context.trace_recorder.finalize(
                    task=context.task,
                    environment_name="banking",
                    provider_name="fake",
                    model_name="fake-model",
                    final_response=result.final_response,
                    statistics=result.statistics,
                ).reflection_turns
            )
            == 1
        )

    async def test_no_reflection_turn_when_attack_type_is_unset(
        self, banking_tool_registry: ToolRegistry
    ) -> None:
        responses = [
            ProviderResponse(provider="fake", model="fake-model", content="No tools needed.")
        ]
        context, _provider = await _build_context(responses, banking_tool_registry)
        executor = CommonAgentExecutor(context, ExecutionPlanner(context.config))

        result = await executor.run()

        trace = context.trace_recorder.finalize(
            task=context.task,
            environment_name="banking",
            provider_name="fake",
            model_name="fake-model",
            final_response=result.final_response,
            statistics=result.statistics,
        )
        assert trace.reflection_turns == []
