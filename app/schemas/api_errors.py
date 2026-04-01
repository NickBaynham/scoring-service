"""Error response bodies for OpenAPI."""

from pydantic import BaseModel, Field


class ErrorDetail(BaseModel):
    """Machine-readable error payload."""

    code: str = Field(..., description="Stable error code", examples=["validation_error"])
    message: str = Field(..., description="Human-readable message")


class ErrorResponse(BaseModel):
    """Standard error envelope."""

    error: ErrorDetail
