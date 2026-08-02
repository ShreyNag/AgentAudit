"""``EvaluationContext`` (PROJECT_SPEC_3 SS6, PROJECT_SPEC_6 SS66): immutable during evaluation.

Evaluators receive only this context -- never the database, never benchmark tools, never a
provider except through the configured Judge (PROJECT_SPEC_3 SS44).
"""

from __future__ import annotations

from typing import Any

from app.trace.models import ExecutionTrace


class EvaluationContext:
    """Everything one evaluation run needs, immutable for its lifetime."""

    def __init__(
        self,
        *,
        run_id: int,
        execution_trace: ExecutionTrace,
        task_instruction: str,
        ground_truth: dict[str, Any],
        environment: str,
        provider: str,
        model: str,
        judge_provider: str,
        judge_model: str,
        statistics: dict[str, Any],
        metadata: dict[str, Any] | None = None,
        expected_tool_sequence: list[str] | None = None,
        attack_type: str | None = None,
    ) -> None:
        """Bind together everything required to evaluate one persisted execution trace."""
        self.run_id = run_id
        self.execution_trace = execution_trace
        self.task_instruction = task_instruction
        self.ground_truth = ground_truth
        self.environment = environment
        self.provider = provider
        self.model = model
        self.judge_provider = judge_provider
        self.judge_model = judge_model
        self.statistics = statistics
        self.metadata = metadata or {}
        # The task's expected/minimal tool sequence (PROJECT_SPEC_1 SS55), used as the baseline
        # the Integrity evaluator diffs actual execution against to detect unnecessary drift.
        self.expected_tool_sequence = expected_tool_sequence or []
        # The adversarial pattern this task tests, if any (e.g. "prompt_injection", "jailbreak") --
        # tells the Judge what kind of attack to look for, on top of whatever it infers from the
        # raw trace alone.
        self.attack_type = attack_type
