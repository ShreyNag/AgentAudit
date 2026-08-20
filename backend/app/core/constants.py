"""Process-wide constants that are not environment configuration.

Values that never change between deployments (API versioning, pagination bounds) live here
rather than in :mod:`app.config.settings`, per PROJECT_SPEC_2 SS13-SS14.
"""

API_V1_PREFIX: str = "/api/v1"

DEFAULT_PAGE_SIZE: int = 50
MAX_PAGE_SIZE: int = 500

CORRELATION_ID_HEADER: str = "X-Request-ID"

# Note: the supported LLM provider list is NOT duplicated here -- it lives solely in
# app.providers.factory.ProviderFactory's registry to avoid the two ever drifting apart.

# A run is either driven by AgentAudit's own execution engine, or merely observed via
# app.trace.tracer.AgentAuditTracer for an independently running agent (see
# docs/external-agent-tracing-guide.md). Stored on runs.execution_mode.
EXECUTION_MODES: tuple[str, ...] = ("benchmark", "external")

# PROJECT_SPEC_1 SS29: supported benchmark environments.
SUPPORTED_ENVIRONMENTS: tuple[str, ...] = (
    "banking",
    "payments",
    "marketplace",
    "trip_planner",
    "email",
    "identity_documents",
    "jailbreak",
    "memory_poisoning",
)

# PROJECT_SPEC_1 SS87: valid behavioural classification labels.
BEHAVIOUR_CLASSIFICATIONS: tuple[str, ...] = (
    "SAFE_CORRECT",
    "SAFE_BY_INCOMPETENCE",
    "UNSAFE_COMPLIANCE",
    "PARTIAL_SUCCESS",
)

# PROJECT_SPEC_3 SS30 / PROJECT_SPEC_2 SS86: the ten independent evaluators. PROJECT_SPEC_1's
# principle-2 list ("Grounding"/"Behaviour") is a looser paraphrase in the vision doc; the
# detailed evaluation spec (PROJECT_SPEC_3) is authoritative for exact names (docs/adr/0008-*.md).
EVALUATOR_NAMES: tuple[str, ...] = (
    "instruction_integrity",
    "planner",
    "memory",
    "tool_selection",
    "tool_invocation",
    "tool_correctness",
    "alignment",
    "tool_faithfulness",
    "security",
    "integrity",
)
