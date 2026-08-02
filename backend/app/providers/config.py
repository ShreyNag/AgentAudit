"""Per-provider configuration (PROJECT_SPEC_2 SS33). Immutable after construction."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class ProviderConfig(BaseModel):
    """Configuration for a single provider instance.

    Built by :class:`~app.providers.factory.ProviderFactory` from either the ``AUT_*`` or
    ``JUDGE_*`` settings group (PROJECT_SPEC_1 SS100) -- never constructed ad hoc elsewhere.
    """

    model_config = ConfigDict(frozen=True)

    provider: str
    model: str
    api_key: str
    base_url: str | None = None
    timeout: float = 60.0
    max_retries: int = 5
    temperature: float = 0.7
    max_tokens: int = 4096
