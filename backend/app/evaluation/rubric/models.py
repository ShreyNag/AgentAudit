"""Rubric domain model (PROJECT_SPEC_3 SS105/SS106, PROJECT_SPEC_6 SS76)."""

from __future__ import annotations

from pydantic import BaseModel, Field


class RubricLevel(BaseModel):
    """One of a rubric's five performance levels (PROJECT_SPEC_3 SS13/SS106)."""

    level: int = Field(ge=1, le=5)
    name: str
    min_score: float
    max_score: float
    description: str


class Rubric(BaseModel):
    """A single evaluator's versioned scoring rubric, stored separately from its code."""

    identifier: str
    version: str = "1.0"
    description: str
    criteria: list[str]
    levels: list[RubricLevel]
    evidence_requirements: list[str] = Field(default_factory=list)
    failure_conditions: list[str] = Field(default_factory=list)
    examples: list[str] = Field(default_factory=list)

    def level_for_score(self, score: float) -> RubricLevel:
        """Return the rubric level whose range contains ``score``."""
        for level in self.levels:
            if level.min_score <= score <= level.max_score:
                return level
        return self.levels[0]
