"""``BaseEvaluator`` (PROJECT_SPEC_3 SS10, PROJECT_SPEC_6 SS69; see ``docs/adr/0008-*.md``).

``evaluate()`` is a template method whose steps are PROJECT_SPEC_3's internal workflow
(``validate -> extract_evidence -> build prompt -> invoke Judge -> generate_reasoning /
compute_confidence``); ``name``/``description``/``version``/``supported_trace_versions``/
``required_events`` are PROJECT_SPEC_6's discovery/identity interface. Concrete evaluators only
ever override :attr:`evidence_categories` and :meth:`evaluator_instructions`.
"""

from __future__ import annotations

import time
from abc import ABC, abstractmethod

from app.core.exceptions import EvaluationError
from app.evaluation.context import EvaluationContext
from app.evaluation.evidence_extractor import EvidenceExtractor
from app.evaluation.judge import JudgeService
from app.evaluation.models import CriterionAssessment, EvaluationResult, Evidence
from app.evaluation.rubric.loader import RubricLoader


class BaseEvaluator(ABC):
    """Abstract base class every one of the ten evaluators implements."""

    #: Canonical evaluator name; must match a key in ``app.evaluation.rubric.definitions.RUBRICS``
    #: and an entry in ``app.core.constants.EVALUATOR_NAMES``.
    name: str
    description: str
    version: str = "1.0"
    #: Evidence categories this evaluator needs (PROJECT_SPEC_3 SS31-40's "Evidence" sections).
    evidence_categories: list[str] = []

    def __init__(
        self,
        judge: JudgeService,
        evidence_extractor: EvidenceExtractor,
        rubric_loader: RubricLoader,
    ) -> None:
        """Bind the evaluator to its Judge, shared evidence extractor, and rubric."""
        self.judge = judge
        self.evidence_extractor = evidence_extractor
        self.rubric = rubric_loader.get(self.name)

    def supported_trace_versions(self) -> list[str]:
        """Return the execution trace schema versions this evaluator can consume."""
        return ["1.0"]

    def required_events(self) -> list[str]:
        """Return trace event types this evaluator expects to find (empty means "any")."""
        return []

    @abstractmethod
    def evaluator_instructions(self) -> str:
        """Evaluator-specific guidance appended to the Judge's system prompt

        (PROJECT_SPEC_3 SS104).
        """

    def validate(self, context: EvaluationContext) -> None:
        """Verify the context is usable by this evaluator before extracting evidence.

        Raises:
            EvaluationError: if no execution trace is present.
        """
        if context.execution_trace is None:
            raise EvaluationError(f"Evaluator '{self.name}' requires an execution trace.")

    def extract_evidence(self, context: EvaluationContext) -> list[Evidence]:
        """Extract this evaluator's declared evidence categories from ``context``."""
        return self.evidence_extractor.extract(context, self.evidence_categories)

    def generate_reasoning(self, judge_output: dict[str, object]) -> str:
        """Return the Judge's reasoning verbatim (never fabricated or rewritten)."""
        return str(judge_output.get("reasoning", ""))

    def compute_confidence(
        self, context: EvaluationContext, evidence: list[Evidence], judge_output: dict[str, object]
    ) -> float:
        """Combine the Judge's self-reported confidence with an evidence-completeness penalty.

        Missing evidence lowers confidence (PROJECT_SPEC_3 SS19/SS68).
        """
        confidence = float(judge_output.get("confidence", 0.5))  # type: ignore[arg-type]
        if not evidence:
            confidence *= 0.5
        return max(0.0, min(1.0, confidence))

    def metadata(self) -> dict[str, object]:
        """Return reproducibility metadata attached to every result (PROJECT_SPEC_3 SS26)."""
        return {"version": self.version, "rubric_version": self.rubric.version}

    async def evaluate(self, context: EvaluationContext) -> EvaluationResult:
        """Run the full evaluation workflow and return a standardized :class:`EvaluationResult`."""
        start = time.perf_counter()
        self.validate(context)
        evidence = self.extract_evidence(context)

        system_prompt, user_prompt = self.judge.build_prompt(
            evaluator_name=self.name,
            evaluator_instructions=self.evaluator_instructions(),
            rubric=self.rubric,
            context=context,
            evidence=evidence,
        )
        response = await self.judge.submit(system_prompt, user_prompt)
        judge_output = self.judge.validate_response(response)

        return EvaluationResult(
            evaluator_name=self.name,
            score=judge_output["score"],  # type: ignore[arg-type]
            confidence=self.compute_confidence(context, evidence, judge_output),
            reasoning=self.generate_reasoning(judge_output),
            expected_outcome=str(judge_output.get("expected_outcome", "")),
            actual_outcome=str(judge_output.get("actual_outcome", "")),
            evidence=evidence,
            strengths=judge_output.get("strengths", []),  # type: ignore[arg-type]
            weaknesses=judge_output.get("weaknesses", []),  # type: ignore[arg-type]
            recommendations=judge_output.get("recommendations", []),  # type: ignore[arg-type]
            matched_rubric=judge_output.get("matched_rubric", "unknown"),  # type: ignore[arg-type]
            criteria_assessment=[
                CriterionAssessment(**item)
                for item in judge_output.get("criteria_assessment", [])  # type: ignore[arg-type]
            ],
            metadata=self.metadata(),
            execution_time=time.perf_counter() - start,
        )
