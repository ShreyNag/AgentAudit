"""Benchmark environments: each owns its own tools, ground truth, dataset, and state
(PROJECT_SPEC_1 SS29). Importing this package registers every concrete environment on the
process-wide :data:`app.environments.registry.environment_registry` and
:data:`app.benchmark.registry.benchmark_registry`.
"""

from app.environments.banking import register as _register_banking
from app.environments.base import BaseEnvironment
from app.environments.email_env import register as _register_email
from app.environments.identity_documents import register as _register_identity_documents
from app.environments.jailbreak import register as _register_jailbreak
from app.environments.marketplace import register as _register_marketplace
from app.environments.memory_poisoning import register as _register_memory_poisoning
from app.environments.payments import register as _register_payments
from app.environments.registry import EnvironmentRegistry, environment_registry
from app.environments.trip_planner import register as _register_trip_planner

_register_banking()
_register_payments()
_register_marketplace()
_register_trip_planner()
_register_email()
_register_identity_documents()
_register_jailbreak()
_register_memory_poisoning()

__all__ = ["BaseEnvironment", "EnvironmentRegistry", "environment_registry"]
