"""``BankingEnvironment``."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import asdict
from typing import Any

from app.core.exceptions import BenchmarkEnvironmentError
from app.environments.banking.state import BankingState, Transaction
from app.environments.base import BaseEnvironment


class BankingEnvironment(BaseEnvironment):
    """Account balance lookup and funds transfer, with balance enforcement.

    Also the Selective Memory benchmark's environment: it holds four distinct customers'
    accounts so a task can instruct the agent to remember only one and forget the rest --
    the environment itself enforces nothing about confidentiality, only balances (PROJECT_SPEC_1
    SS62/SS106: appropriateness is entirely an evaluation concern, never an environment one).
    """

    name = "banking"

    def __init__(self) -> None:
        super().__init__()
        self.state: BankingState = BankingState()

    async def initialize(self) -> None:
        self.state = BankingState()
        self._initialized = True

    async def reset(self) -> None:
        await self.initialize()

    async def observe(self) -> dict[str, Any]:
        return {
            "accounts": {k: v.balance for k, v in self.state.accounts.items()},
            "transaction_count": len(self.state.transactions),
        }

    def _handlers(self) -> dict[str, Callable[..., dict[str, Any]]]:
        return {"account_lookup": self.lookup_account, "bank_transfer": self.transfer_funds}

    async def validate_action(self, action: str, parameters: dict[str, Any]) -> bool:
        return action in self._handlers()

    async def step(self, action: str, parameters: dict[str, Any]) -> dict[str, Any]:
        handler = self._handlers().get(action)
        if handler is None:
            raise BenchmarkEnvironmentError(f"Unknown banking action '{action}'.")
        return handler(**parameters)

    def lookup_account(self, account_id: str) -> dict[str, Any]:
        """Return the balance for ``account_id``."""
        account = self.state.accounts.get(account_id)
        if account is None:
            raise BenchmarkEnvironmentError(f"Unknown account_id '{account_id}'.")
        return asdict(account)

    def transfer_funds(self, from_account: str, to_account: str, amount: float) -> dict[str, Any]:
        """Transfer ``amount`` from ``from_account`` to ``to_account``.

        Enforces sufficient balance -- the environment enforces state consistency; whether the
        transfer was an *appropriate* action for the task is left entirely to evaluation
        (PROJECT_SPEC_1 SS62/SS106), never decided here.
        """
        source = self.state.accounts.get(from_account)
        destination = self.state.accounts.get(to_account)
        if source is None or destination is None:
            raise BenchmarkEnvironmentError("Unknown source or destination account.")
        if amount <= 0:
            raise BenchmarkEnvironmentError("Transfer amount must be positive.")
        if source.balance < amount:
            raise BenchmarkEnvironmentError(
                f"Insufficient balance in '{from_account}': requested {amount}, "
                f"available {source.balance}."
            )
        source.balance -= amount
        destination.balance += amount
        transaction = Transaction(
            id=f"txn-{len(self.state.transactions) + 1}",
            from_account=from_account,
            to_account=to_account,
            amount=amount,
        )
        self.state.transactions.append(transaction)
        return {"transaction_id": transaction.id, "status": "completed"}

    async def is_complete(self) -> bool:
        return len(self.state.transactions) > 0

    async def export_state(self) -> dict[str, Any]:
        return {
            "accounts": {k: asdict(v) for k, v in self.state.accounts.items()},
            "transactions": [asdict(t) for t in self.state.transactions],
        }

    async def cleanup(self) -> None:
        return None
