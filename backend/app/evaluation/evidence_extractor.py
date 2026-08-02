"""``EvidenceExtractor`` (PROJECT_SPEC_6 SS71-72): shared, reusable evidence extraction.

Every evaluator asks for the trace categories relevant to its rubric; extraction logic lives
here once rather than being duplicated across all ten evaluators.
"""

from __future__ import annotations

import uuid

from app.evaluation.context import EvaluationContext
from app.evaluation.models import Evidence


class EvidenceExtractor:
    """Extracts categorized :class:`~app.evaluation.models.Evidence` from an evaluation context."""

    def extract(self, context: EvaluationContext, categories: list[str]) -> list[Evidence]:
        """Return evidence for every requested category found in ``context``."""
        trace = context.execution_trace
        evidence: list[Evidence] = []

        if "planner" in categories:
            evidence.append(
                Evidence(
                    evidence_id=str(uuid.uuid4()),
                    category="planner",
                    description=f"planner_available={trace.planner.get('planner_available')}",
                    supporting_data=trace.planner,
                )
            )
        if "reasoning" in categories:
            evidence.append(
                Evidence(
                    evidence_id=str(uuid.uuid4()),
                    category="reasoning",
                    description=f"reasoning_available={trace.reasoning.get('reasoning_available')}",
                    supporting_data=trace.reasoning,
                )
            )
        if "reasoning_steps" in categories:
            for index, step in enumerate(trace.reasoning_steps, start=1):
                content = step.get("content")
                evidence.append(
                    Evidence(
                        evidence_id=str(uuid.uuid4()),
                        category="reasoning_steps",
                        description=(
                            f"Turn {index} reasoning: "
                            f"{content or '(the model stated no reasoning this turn)'}"
                        ),
                        severity="warning" if not step.get("reasoning_available") else "info",
                        supporting_data=step,
                    )
                )
        if "reflection" in categories:
            for index, turn in enumerate(trace.reflection_turns, start=1):
                evidence.append(
                    Evidence(
                        evidence_id=str(uuid.uuid4()),
                        category="reflection",
                        description=(
                            f"Reflection probe {index} response: "
                            f"{turn.get('response') or '(no response given)'}"
                        ),
                        severity="warning" if not turn.get("response") else "info",
                        supporting_data=turn,
                    )
                )
        if "tool_sequence" in categories or "tool_calls" in categories:
            for call in trace.tool_calls:
                evidence.append(
                    Evidence(
                        evidence_id=str(uuid.uuid4()),
                        category="tool_calls",
                        description=(
                            f"Tool '{call.get('tool_name')}' invoked, status={call.get('status')}."
                        ),
                        severity="warning" if call.get("status") != "completed" else "info",
                        supporting_data=call,
                    )
                )
        if "tool_outputs" in categories:
            for output in trace.tool_outputs:
                evidence.append(
                    Evidence(
                        evidence_id=str(uuid.uuid4()),
                        category="tool_outputs",
                        description=f"Tool '{output.get('tool_name')}' returned an output.",
                        severity="warning" if output.get("error") else "info",
                        supporting_data=output,
                    )
                )
        if "messages" in categories or "assistant_messages" in categories:
            for message in trace.messages:
                evidence.append(
                    Evidence(
                        evidence_id=str(uuid.uuid4()),
                        category="messages",
                        description=f"{message.get('role', 'assistant')} message recorded.",
                        supporting_data=message,
                    )
                )
        if "errors" in categories:
            for error in trace.errors:
                evidence.append(
                    Evidence(
                        evidence_id=str(uuid.uuid4()),
                        category="errors",
                        description=error,
                        severity="error",
                        supporting_data={"error": error},
                    )
                )
        if "environment_changes" in categories:
            for change in trace.environment_changes:
                evidence.append(
                    Evidence(
                        evidence_id=str(uuid.uuid4()),
                        category="environment_changes",
                        description="Environment state change recorded.",
                        supporting_data=change,
                    )
                )
        if "final_response" in categories:
            evidence.append(
                Evidence(
                    evidence_id=str(uuid.uuid4()),
                    category="final_response",
                    description=trace.final_response or "No final response was produced.",
                    severity="warning" if not trace.final_response else "info",
                    supporting_data={"final_response": trace.final_response},
                )
            )
        if "expected_tool_sequence" in categories:
            evidence.append(
                Evidence(
                    evidence_id=str(uuid.uuid4()),
                    category="expected_tool_sequence",
                    description=(
                        f"Expected/baseline tool sequence for this task: "
                        f"{context.expected_tool_sequence or '(none defined)'}"
                    ),
                    supporting_data={"expected_tool_sequence": context.expected_tool_sequence},
                )
            )
        if "ground_truth" in categories:
            evidence.append(
                Evidence(
                    evidence_id=str(uuid.uuid4()),
                    category="ground_truth",
                    description="Benchmark ground truth for this task.",
                    supporting_data=context.ground_truth,
                )
            )
        if "instructions" in categories:
            evidence.append(
                Evidence(
                    evidence_id=str(uuid.uuid4()),
                    category="instructions",
                    description=context.task_instruction,
                    supporting_data={"instruction": context.task_instruction},
                )
            )
        if "entire_trace" in categories:
            evidence.append(
                Evidence(
                    evidence_id=str(uuid.uuid4()),
                    category="entire_trace",
                    description=f"{len(trace.events)} total trace events recorded.",
                    supporting_data={"event_count": len(trace.events)},
                )
            )
        return evidence
