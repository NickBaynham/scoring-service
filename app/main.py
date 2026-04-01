"""FastAPI application entrypoint."""

from __future__ import annotations

import logging
import uuid
from collections.abc import AsyncGenerator, Awaitable, Callable
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response

from app.api.router import api_router
from app.api.routes.openapi import CONTACT, OPENAPI_TAGS_METADATA
from app.core.config import get_settings
from app.core.exceptions import (
    DomainValidationError,
    NotFoundError,
    ScoringServiceError,
    UnauthorizedError,
)
from app.core.logging import setup_logging
from app.core.telemetry import init_telemetry
from app.db.session import dispose_engine, init_engine
from app.schemas.api_errors import ErrorDetail, ErrorResponse

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    settings = get_settings()
    setup_logging(settings.log_level, json_logs=settings.is_production)
    init_engine(settings)
    init_telemetry(settings)
    logger.info("Application startup", extra={"env": settings.app_env})
    yield
    await dispose_engine()
    logger.info("Application shutdown")


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="VerifiedSignal Scoring Service",
        description=(
            "AI-based document credibility scoring: queue jobs, run multi-dimension LLM scorers, "
            "and retrieve structured credibility profiles."
        ),
        version="0.1.0",
        openapi_tags=OPENAPI_TAGS_METADATA,
        contact=CONTACT,
        license_info={"name": "Proprietary", "url": "https://example.com/license"},
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"] if settings.app_env in ("local", "dev", "staging") else [],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.middleware("http")
    async def add_correlation_id(
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        cid = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        request.state.correlation_id = cid
        response = await call_next(request)
        response.headers["X-Request-ID"] = cid
        return response

    @app.exception_handler(NotFoundError)
    async def not_found_handler(request: Request, exc: NotFoundError) -> JSONResponse:
        body = ErrorResponse(error=ErrorDetail(code=exc.code, message=exc.message))
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content=body.model_dump())

    @app.exception_handler(DomainValidationError)
    async def validation_exc_handler(request: Request, exc: DomainValidationError) -> JSONResponse:
        body = ErrorResponse(error=ErrorDetail(code=exc.code, message=exc.message))
        return JSONResponse(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, content=body.model_dump())

    @app.exception_handler(UnauthorizedError)
    async def unauthorized_handler(request: Request, exc: UnauthorizedError) -> JSONResponse:
        body = ErrorResponse(error=ErrorDetail(code=exc.code, message=exc.message))
        return JSONResponse(status_code=status.HTTP_401_UNAUTHORIZED, content=body.model_dump())

    @app.exception_handler(ScoringServiceError)
    async def service_error_handler(request: Request, exc: ScoringServiceError) -> JSONResponse:
        body = ErrorResponse(error=ErrorDetail(code=exc.code, message=exc.message))
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content=body.model_dump())

    @app.exception_handler(RequestValidationError)
    async def request_validation_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"detail": exc.errors()},
        )

    app.include_router(api_router)
    return app


app = create_app()


def run() -> None:
    """CLI entrypoint for `pdm run scoring-api` / console script."""
    settings = get_settings()
    uvicorn.run(
        "app.main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=settings.app_env == "local",
        factory=False,
    )


if __name__ == "__main__":
    run()
