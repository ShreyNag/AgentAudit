"""Every environment's declared toolset is actually registered on the shared tool_registry."""

from __future__ import annotations

import pytest

import app.tools.implementations  # noqa: F401 - triggers registration of all tools
from app.environments import environment_registry
from app.environments.banking import TOOLSET as BANKING_TOOLS
from app.environments.email_env import TOOLSET as EMAIL_TOOLS
from app.environments.identity_documents import TOOLSET as IDENTITY_DOCUMENTS_TOOLS
from app.environments.jailbreak import TOOLSET as JAILBREAK_TOOLS
from app.environments.marketplace import TOOLSET as MARKETPLACE_TOOLS
from app.environments.memory_poisoning import TOOLSET as MEMORY_POISONING_TOOLS
from app.environments.payments import TOOLSET as PAYMENTS_TOOLS
from app.environments.trip_planner import TOOLSET as TRIP_PLANNER_TOOLS
from app.tools.registry import tool_registry

ALL_TOOLSETS = {
    "banking": BANKING_TOOLS,
    "payments": PAYMENTS_TOOLS,
    "marketplace": MARKETPLACE_TOOLS,
    "trip_planner": TRIP_PLANNER_TOOLS,
    "email": EMAIL_TOOLS,
    "identity_documents": IDENTITY_DOCUMENTS_TOOLS,
    "jailbreak": JAILBREAK_TOOLS,
    "memory_poisoning": MEMORY_POISONING_TOOLS,
}


class TestAllToolsRegistered:
    @pytest.mark.parametrize(
        "environment_name,tool_name",
        [(env_name, tool_name) for env_name, tools in ALL_TOOLSETS.items() for tool_name in tools],
    )
    def test_tool_is_registered(self, environment_name: str, tool_name: str) -> None:
        assert tool_registry.is_registered(tool_name), (
            f"Tool '{tool_name}' declared by environment '{environment_name}' is not "
            "registered on tool_registry."
        )

    @pytest.mark.asyncio
    async def test_a_tool_from_every_environment_can_be_created_and_run_health_check(self) -> None:
        for environment_name, tools in ALL_TOOLSETS.items():
            env = await environment_registry.create(environment_name)
            tool = tool_registry.create(tools[0], env)
            assert await tool.health_check() is True
