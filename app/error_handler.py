from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from botocore.exceptions import ClientError
from pydantic_ai.exceptions import ModelHTTPError, AgentRunError
from app.lib.constants import (
    ERROR_DATABASE_CONSTRAINT_VIOLATION,
    ERROR_USERNAME_ALREADY_EXISTS,
    ERROR_EMAIL_ALREADY_EXISTS,
    ERROR_RECORD_ALREADY_EXISTS,
    ERROR_REFERENCED_RECORD_NOT_EXISTS,
    ERROR_REQUIRED_FIELD_MISSING,
    ERROR_DATABASE_ERROR,
    ERROR_UNKNOWN_ERROR,
    ERROR_RESOURCE_NOT_FOUND,
    ERROR_ACCESS_DENIED,
    ERROR_SERVICE_UNAVAILABLE,
    ERROR_VALIDATION_ERROR,
    ERROR_MODEL_RESPONSE_TRUNCATED,
    ERROR_AI_MODEL_SERVICE_ERROR,
    ERROR_FAILED_TO_PROCESS_AI_AGENT,
    ERROR_UNEXPECTED_ERROR,
    ERROR_TYPE_INTEGRITY_ERROR,
    ERROR_TYPE_VALUE_ERROR,
    ERROR_TYPE_DATABASE_ERROR,
    ERROR_TYPE_SERVICE_ERROR,
    ERROR_TYPE_VALIDATION_ERROR,
    ERROR_TYPE_MODEL_SERVICE_ERROR,
    ERROR_TYPE_AGENT_ERROR,
    ERROR_TYPE_INTERNAL_SERVER_ERROR,
)
import logging

logger = logging.getLogger(__name__)


def setup_error_handlers(app: FastAPI):
    """Register all error handlers for the FastAPI application."""

    @app.exception_handler(IntegrityError)
    async def integrity_error_handler(request: Request, exc: IntegrityError):
        """Handle database integrity constraint violations. Must be registered before SQLAlchemyError."""
        if hasattr(exc, 'orig') and exc.orig is not None: error_message = str(exc.orig)
        else: error_message = str(exc)
        error_lower = error_message.lower()
        detail = ERROR_DATABASE_CONSTRAINT_VIOLATION
        if "uniqueviolation" in error_lower or "duplicate key" in error_lower or "unique constraint" in error_lower:
            if "ix_user_username" in error_message: detail = ERROR_USERNAME_ALREADY_EXISTS
            elif "ix_user_email" in error_message: detail = ERROR_EMAIL_ALREADY_EXISTS
            else: detail = ERROR_RECORD_ALREADY_EXISTS
        elif "foreign key" in error_lower: detail = ERROR_REFERENCED_RECORD_NOT_EXISTS
        elif "not null" in error_lower: detail = ERROR_REQUIRED_FIELD_MISSING
        logger.error(f"IntegrityError: {error_message} - Path: {request.url.path}")
        return JSONResponse(status_code=status.HTTP_409_CONFLICT, content={"detail": detail, "type": ERROR_TYPE_INTEGRITY_ERROR})

    @app.exception_handler(ValueError)
    async def value_error_handler(request: Request, exc: ValueError):
        """Handle ValueError exceptions - typically from business logic or repository."""
        error_message = str(exc)
        keywords = ["not found", "already exists", "duplicate", "unique", "constraint"]
        if "not found" in error_message.lower(): status_code = status.HTTP_404_NOT_FOUND
        elif any(keyword in error_message.lower() for keyword in keywords): status_code = status.HTTP_409_CONFLICT
        else: status_code = status.HTTP_400_BAD_REQUEST
        logger.error(f"ValueError: {error_message} - Path: {request.url.path}")
        return JSONResponse(status_code=status_code, content={"detail": error_message, "type": "ValueError"})

    @app.exception_handler(SQLAlchemyError)
    async def sqlalchemy_error_handler(request: Request, exc: SQLAlchemyError):
        """Handle general SQLAlchemy database errors (but not IntegrityError, which is handled separately)."""
        error_message = str(exc)
        logger.error(f"SQLAlchemyError: {error_message} - Path: {request.url.path}")
        content = {"detail": ERROR_DATABASE_ERROR, "type": ERROR_TYPE_DATABASE_ERROR}
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content=content)

    @app.exception_handler(ClientError)
    async def client_error_handler(request: Request, exc: ClientError):
        """Handle AWS/boto3 client errors."""
        error_code = exc.response.get("Error", {}).get("Code", ERROR_UNKNOWN_ERROR) if hasattr(exc, 'response') else ERROR_UNKNOWN_ERROR
        error_message = exc.response.get("Error", {}).get("Message", str(exc)) if hasattr(exc, 'response') else str(exc)
        if error_code == "NoSuchKey" or error_code == "404":
            status_code = status.HTTP_404_NOT_FOUND
            detail = ERROR_RESOURCE_NOT_FOUND
        elif error_code == "AccessDenied" or error_code == "403":
            status_code = status.HTTP_403_FORBIDDEN
            detail = ERROR_ACCESS_DENIED
        else:
            status_code = status.HTTP_503_SERVICE_UNAVAILABLE
            detail = ERROR_SERVICE_UNAVAILABLE
        logger.error(f"ClientError ({error_code}): {error_message} - Path: {request.url.path}")
        return JSONResponse(status_code=status_code, content={"detail": detail, "type": ERROR_TYPE_SERVICE_ERROR, "service": "AWS"})

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(request: Request, exc: RequestValidationError):
        """Handle Pydantic validation errors from request bodies."""
        errors = exc.errors()
        error_messages = []
        for error in errors:
            field = ".".join(str(loc) for loc in error["loc"])
            message = error["msg"]
            error_messages.append(f"{field}: {message}")
        logger.error(f"ValidationError: {error_messages} - Path: {request.url.path}")
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"detail": ERROR_VALIDATION_ERROR, "errors": error_messages, "type": ERROR_TYPE_VALIDATION_ERROR}
        )

    @app.exception_handler(ModelHTTPError)
    async def model_http_error_handler(request: Request, exc: ModelHTTPError):
        """Handle AI model HTTP errors from pydantic_ai."""
        error_detail = str(exc)
        logger.error(f"ModelHTTPError: {error_detail} - Path: {request.url.path}")
        if "Invalid JSON" in error_detail or "EOF" in error_detail:
            detail = ERROR_MODEL_RESPONSE_TRUNCATED
        else: detail = ERROR_AI_MODEL_SERVICE_ERROR.format(error_detail=error_detail)
        return JSONResponse(status_code=status.HTTP_502_BAD_GATEWAY, content={"detail": detail, "type": ERROR_TYPE_MODEL_SERVICE_ERROR, "service": "AI"})

    @app.exception_handler(AgentRunError)
    async def agent_run_error_handler(request: Request, exc: AgentRunError):
        """Handle AI agent execution errors from pydantic_ai."""
        error_message = str(exc)
        logger.error(f"AgentRunError: {error_message} - Path: {request.url.path}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": ERROR_FAILED_TO_PROCESS_AI_AGENT.format(error_message=error_message), "type": ERROR_TYPE_AGENT_ERROR}
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        """Catch-all handler for any unhandled exceptions."""
        error_message = str(exc)
        error_type = type(exc).__name__
        logger.exception(f"Unhandled {error_type}: {error_message} - Path: {request.url.path}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": ERROR_UNEXPECTED_ERROR, "type": ERROR_TYPE_INTERNAL_SERVER_ERROR}
        )
