"""Application factory.

Builds the single FastAPI application per PROJECT_SPEC_2 SS6: dependency injection, routing,
middleware, exception handling, and OpenAPI documentation. No business logic lives here
(PROJECT_SPEC_2 SS6/SS17) -- startup/shutdown here only wires infrastructure together, following
the lifecycle defined in PROJECT_SPEC_2 SS5.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from app.api.router import api_router
from app.config import get_settings
from app.core.constants import API_V1_PREFIX
from app.core.exceptions import AgentAuditError
from app.core.logging import configure_logging, get_logger
from app.database.session import get_database
from app.middleware.correlation import CorrelationIdMiddleware
from app.middleware.exception_handlers import (
    agentaudit_exception_handler,
    unhandled_exception_handler,
    validation_exception_handler,
)
from app.middleware.request_logging import RequestLoggingMiddleware

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Run startup validation before serving traffic, and clean up on shutdown.

    Startup sequence (PROJECT_SPEC_2 SS5/SS23):
    configuration (already loaded via :func:`get_settings` at import time) -> database
    connectivity -> provider registry -> tool registry -> benchmark/environment registry ->
    ready to serve.
    """
    settings = get_settings()
    logger.info("startup_begin", application_version=settings.application_version)

    database = get_database()
    await database.check_connectivity()
    logger.info("database_connected")

    from app.environments import environment_registry
    from app.providers.factory import ProviderFactory
    from app.tools import implementations  # noqa: F401 - registers tools as a side effect
    from app.tools.registry import tool_registry

    logger.info("providers_loaded", providers=ProviderFactory.supported_providers())
    logger.info("tools_registered", tools=tool_registry.list_tools())
    logger.info("environments_registered", environments=environment_registry.list_environments())

    logger.info("startup_complete")
    yield

    logger.info("shutdown_begin")
    await database.dispose()
    logger.info("shutdown_complete")


def create_app() -> FastAPI:
    """Build and configure the AgentAudit FastAPI application."""
    settings = get_settings()
    configure_logging(settings.log_level)

    app = FastAPI(
        title="AgentAudit",
        description=(
            "An independent, execution-trace-based evaluation framework for tool-using AI "
            "agents."
        ),
        version=settings.application_version,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    # Middleware order matters: Starlette applies middleware in reverse registration order,
    # so the last one added runs outermost (first) for requests.
    app.add_middleware(GZipMiddleware, minimum_size=1000)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"] if settings.debug else [],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(RequestLoggingMiddleware)
    app.add_middleware(CorrelationIdMiddleware)

    app.add_exception_handler(AgentAuditError, agentaudit_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)

    app.include_router(api_router, prefix=API_V1_PREFIX)

    return app


app = create_app()
