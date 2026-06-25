"""FastAPI application entry point with middleware and exception handlers."""

import time
from collections.abc import AsyncIterator, Callable
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.responses import Response

from app.api.routes import router
from app.core.config import get_settings
from app.core.exceptions import AddressBookError, AddressNotFoundError, InvalidSearchParameterError
from app.core.logging import get_logger, setup_logging
from app.db.database import Base, engine
from app.schemas.address import ErrorResponse, format_validation_errors

settings = get_settings()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """Manage application startup and shutdown lifecycle events."""
    setup_logging(settings.log_level)
    logger.info("Starting %s v%s", settings.app_name, settings.app_version)
    logger.info("Creating database tables if they do not exist")
    Base.metadata.create_all(bind=engine)
    logger.info("Application startup complete")
    yield
    logger.info("Shutting down %s", settings.app_name)
    engine.dispose()
    logger.info("Application shutdown complete")


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=(
        "A production-quality REST API for managing addresses with CRUD operations, "
        "proximity search using the Haversine formula, pagination, and filtering."
    ),
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

app.include_router(router)


@app.middleware("http")
async def log_requests(
    request: Request,
    call_next: Callable[[Request], Any],
) -> Response:
    """Log incoming HTTP requests and response status with elapsed time."""
    start = time.perf_counter()
    logger.info("Request: %s %s", request.method, request.url.path)
    try:
        response = await call_next(request)
    except Exception:
        logger.exception("Unhandled error during request: %s %s", request.method, request.url.path)
        raise
    elapsed_ms = (time.perf_counter() - start) * 1000
    logger.info(
        "Response: %s %s -> %s (%.2fms)",
        request.method,
        request.url.path,
        response.status_code,
        elapsed_ms,
    )
    return response


@app.exception_handler(AddressNotFoundError)
async def address_not_found_handler(
    _request: Request,
    exc: AddressNotFoundError,
) -> JSONResponse:
    """Return a consistent 404 response when an address is not found."""
    logger.error("Address not found: %s", exc.message)
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content=ErrorResponse(message="Address not found").model_dump(),
    )


@app.exception_handler(InvalidSearchParameterError)
async def invalid_search_parameter_handler(
    _request: Request,
    exc: InvalidSearchParameterError,
) -> JSONResponse:
    """Return a 422 response for invalid business validation."""
    logger.error("Invalid search parameter: %s", exc.message)
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=ErrorResponse(message=exc.message).model_dump(),
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    _request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    """Return a consistent 422 response for request validation failures."""
    message = format_validation_errors(exc.errors())
    logger.error("Validation error: %s", message)
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=ErrorResponse(message=message).model_dump(),
    )


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(
    _request: Request,
    exc: StarletteHTTPException,
) -> JSONResponse:
    """Normalize HTTP exceptions into the standard error response format."""
    if exc.status_code == status.HTTP_404_NOT_FOUND:
        message = "Resource not found"
    else:
        message = str(exc.detail) if exc.detail else "HTTP error"
    logger.error("HTTP %s: %s", exc.status_code, message)
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(message=message).model_dump(),
    )


@app.exception_handler(AddressBookError)
async def address_book_error_handler(
    _request: Request,
    exc: AddressBookError,
) -> JSONResponse:
    """Handle generic application errors."""
    logger.error("Application error: %s", exc.message)
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=ErrorResponse(message=exc.message).model_dump(),
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(
    _request: Request,
    exc: Exception,
) -> JSONResponse:
    """Return a consistent 500 response for unexpected server errors."""
    logger.exception("Unhandled server error: %s", exc)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorResponse(message="Internal server error").model_dump(),
    )
