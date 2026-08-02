"""Provider-agnostic LLM abstraction layer (PROJECT_SPEC_1 SS12-14, PROJECT_SPEC_2 Part 2).

Nothing outside this package may import a vendor SDK or call a vendor API directly
(PROJECT_SPEC_1 SS121/SS557-565). Everything else depends only on :class:`BaseProvider`,
:mod:`app.providers.schemas`, and :class:`ProviderFactory`.
"""

from app.providers.base import BaseProvider
from app.providers.config import ProviderConfig
from app.providers.factory import ProviderFactory
from app.providers.schemas import (
    HealthCheckResult,
    ModelInfo,
    ProviderMessage,
    ProviderRequest,
    ProviderResponse,
    TokenUsage,
    ToolCallSchema,
)

__all__ = [
    "BaseProvider",
    "ProviderConfig",
    "ProviderFactory",
    "HealthCheckResult",
    "ModelInfo",
    "ProviderMessage",
    "ProviderRequest",
    "ProviderResponse",
    "ToolCallSchema",
    "TokenUsage",
]
