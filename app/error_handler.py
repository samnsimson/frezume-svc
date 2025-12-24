from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from botocore.exceptions import ClientError
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
        detail = "A database constraint violation occurred"
        if "uniqueviolation" in error_lower or "duplicate key" in error_lower or "unique constraint" in error_lower:
            if "ix_user_username" in error_message: detail = "Username already exists"
            elif "ix_user_email" in error_message: detail = "Email already exists"
            else: detail = "A record with this information already exists"
        elif "foreign key" in error_lower: detail = "Referenced record does not exist"
        elif "not null" in error_lower: detail = "Required field is missing"
        logger.error(f"IntegrityError: {error_message} - Path: {request.url.path}")
        return JSONResponse(status_code=status.HTTP_409_CONFLICT, content={"detail": detail, "type": "IntegrityError"})

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
        content = {"detail": "A database error occurred", "type": "DatabaseError"}
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content=content)

    @app.exception_handler(ClientError)
    async def client_error_handler(request: Request, exc: ClientError):
        """Handle AWS/boto3 client errors."""
        error_code = exc.response.get("Error", {}).get("Code", "UnknownError") if hasattr(exc, 'response') else "UnknownError"
        error_message = exc.response.get("Error", {}).get("Message", str(exc)) if hasattr(exc, 'response') else str(exc)
        if error_code == "NoSuchKey" or error_code == "404":
            status_code = status.HTTP_404_NOT_FOUND
            detail = "The requested resource was not found"
        elif error_code == "AccessDenied" or error_code == "403":
            status_code = status.HTTP_403_FORBIDDEN
            detail = "Access denied to the requested resource"
        else:
            status_code = status.HTTP_503_SERVICE_UNAVAILABLE
            detail = "External service is temporarily unavailable"
        logger.error(f"ClientError ({error_code}): {error_message} - Path: {request.url.path}")
        return JSONResponse(status_code=status_code, content={"detail": detail, "type": "ServiceError", "service": "AWS"})

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
            content={"detail": "Validation error", "errors": error_messages, "type": "ValidationError"}
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        """Catch-all handler for any unhandled exceptions."""
        error_message = str(exc)
        error_type = type(exc).__name__
        logger.exception(f"Unhandled {error_type}: {error_message} - Path: {request.url.path}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "An unexpected error occurred", "type": "InternalServerError"}
        )
