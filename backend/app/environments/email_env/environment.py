"""``EmailEnvironment``."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import asdict
from typing import Any

from app.core.exceptions import BenchmarkEnvironmentError
from app.environments.base import BaseEnvironment
from app.environments.email_env.state import EmailMessage, EmailState


class EmailEnvironment(BaseEnvironment):
    """Inbox search and email sending."""

    name = "email"

    def __init__(self) -> None:
        super().__init__()
        self.state: EmailState = EmailState()

    async def initialize(self) -> None:
        self.state = EmailState()
        self._initialized = True

    async def reset(self) -> None:
        await self.initialize()

    async def observe(self) -> dict[str, Any]:
        return {"inbox_count": len(self.state.inbox), "sent_count": len(self.state.sent)}

    def _handlers(self) -> dict[str, Callable[..., dict[str, Any]]]:
        return {"email_search": self.search_email, "send_email": self.send_email}

    async def validate_action(self, action: str, parameters: dict[str, Any]) -> bool:
        return action in self._handlers()

    async def step(self, action: str, parameters: dict[str, Any]) -> dict[str, Any]:
        handler = self._handlers().get(action)
        if handler is None:
            raise BenchmarkEnvironmentError(f"Unknown email action '{action}'.")
        return handler(**parameters)

    def search_email(self, query: str) -> dict[str, Any]:
        """Search the inbox for messages whose subject or body contains ``query``."""
        query_lower = query.lower()
        matches = [
            asdict(message)
            for message in self.state.inbox.values()
            if query_lower in message.subject.lower() or query_lower in message.body.lower()
        ]
        return {"messages": matches}

    def send_email(self, to: str, subject: str, body: str) -> dict[str, Any]:
        """Send a new email, recording it in the ``sent`` folder."""
        message = EmailMessage(
            id=f"sent-{len(self.state.sent) + 1}",
            sender=to,
            subject=subject,
            body=body,
            label="sent",
        )
        self.state.sent.append(message)
        return {"message_id": message.id, "status": "sent"}

    async def is_complete(self) -> bool:
        return len(self.state.sent) > 0

    async def export_state(self) -> dict[str, Any]:
        return {
            "inbox": {k: asdict(v) for k, v in self.state.inbox.items()},
            "sent": [asdict(m) for m in self.state.sent],
        }

    async def cleanup(self) -> None:
        return None
