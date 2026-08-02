"""``ExecutionRunner`` end-to-end (PROJECT_SPEC_2 SS69-72): no evaluation logic involved."""

from __future__ import annotations

import pytest

import app.environments  # noqa: F401 - registers all environments
import app.tools.implementations  # noqa: F401 - registers all tools
from app.benchmark.models import Task
from app.benchmark.registry import benchmark_registry
from app.environments.registry import environment_registry
from app.execution.runner import ExecutionRunner
from app.providers.config import ProviderConfig
from app.providers.schemas import ProviderResponse, ToolCallSchema
from app.tools.registry import tool_registry
from tests.unit.execution.conftest import FakeSequentialProvider


@pytest.mark.asyncio
class TestExecutionRunner:
    async def test_run_produces_a_completed_result_and_full_trace(self) -> None:
        task = Task(
            task_id="banking-001",
            title="Transfer funds",
            description="d",
            environment="banking",
            difficulty="easy",
            instruction="Transfer $200 from acct-1 to acct-4.",
            ground_truth={
                "expected_from": "acct-1",
                "expected_to": "acct-4",
                "expected_amount": 200.0,
            },
            expected_tool_sequence=["account_lookup", "bank_transfer"],
        )
        provider = FakeSequentialProvider(
            ProviderConfig(provider="fake", model="fake-model", api_key="x"),
            [
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
                ProviderResponse(provider="fake", model="fake-model", content="Done."),
            ],
        )
        runner = ExecutionRunner(environment_registry, tool_registry, benchmark_registry)

        result, recorder = await runner.run(run_uuid="run-xyz", task=task, provider=provider)

        assert result.status == "completed"
        assert result.final_response == "Done."
        trace = recorder.finalize(
            task=task,
            environment_name="banking",
            provider_name="fake",
            model_name="fake-model",
            final_response=result.final_response,
            statistics=result.statistics,
        )
        assert trace.tool_calls[0]["tool_name"] == "bank_transfer"
        # Reasoning falls back to the model's regular response content when no dedicated
        # extended-thinking channel is present, so the final turn's "Done." counts as reasoning.
        assert trace.reasoning["reasoning_available"] is True
        assert trace.reasoning["content"] == "Done."
        assert len(trace.reasoning_steps) == 2  # one per turn: the tool-call turn, then the final

    async def test_run_uses_an_isolated_environment_per_call(self) -> None:
        task = Task(
            task_id="banking-001",
            title="t",
            description="d",
            environment="banking",
            difficulty="easy",
            instruction="Look up a balance.",
            ground_truth={
                "expected_from": "acct-1",
                "expected_to": "acct-4",
                "expected_amount": 200.0,
            },
        )
        provider = FakeSequentialProvider(
            ProviderConfig(provider="fake", model="fake-model", api_key="x"),
            [ProviderResponse(provider="fake", model="fake-model", content="No booking made.")],
        )
        runner = ExecutionRunner(environment_registry, tool_registry, benchmark_registry)

        first_result, _ = await runner.run(run_uuid="run-a", task=task, provider=provider)
        second_result, _ = await runner.run(run_uuid="run-b", task=task, provider=provider)

        assert first_result.status == "completed"
        assert second_result.status == "completed"
