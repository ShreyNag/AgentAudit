"""``BaseService`` (PROJECT_SPEC_6 SS13): common ancestor for every application service."""

from __future__ import annotations


class BaseService:
    """Marker base class for services.

    Services coordinate one business workflow by composing repositories (and, for execution,
    the Execution Engine) -- they hold no direct database session and perform no persistence
    themselves (PROJECT_SPEC_2 SS17-18).
    """
