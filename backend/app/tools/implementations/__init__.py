"""Concrete tool implementations, one module per benchmark environment.

Importing this package registers every tool on the process-wide
:data:`app.tools.registry.tool_registry`.
"""

from app.tools.implementations import (
    banking_tools,
    email_tools,
    identity_documents_tools,
    jailbreak_tools,
    marketplace_tools,
    memory_poisoning_tools,
    payments_tools,
    trip_planner_tools,
)

for _module in (
    banking_tools,
    payments_tools,
    marketplace_tools,
    trip_planner_tools,
    email_tools,
    identity_documents_tools,
    jailbreak_tools,
    memory_poisoning_tools,
):
    _module.register()
