"""Common API response models."""

from datetime import datetime
from typing import Any, Dict, List, Optional, Generic, TypeVar
from enum import Enum

from pydantic import BaseModel, Field, ConfigDict

T = TypeVar('T')


class APIStatus(str, Enum):
    """API response status codes."""
    SUCCESS = "success"
    ERROR = "error"
    WARNING = "warning"


class ErrorCode(str, Enum):
    """Standard error codes for the API."""
    VALIDATION_ERROR = "validation_error"
    NOT_FOUND = "not_found"
    UNAUTHORIZED = "unauthorized"
    FORBIDDEN = "forbidden"
    INTERNAL_ERROR = "internal_error"
    STORAGE_ERROR = "storage_error"
    TRANSCRIPTION_ERROR = "transcription_error"
    MEETING_NOT_FOUND = "meeting_not_found"
    TRANSCRIPT_NOT_FOUND = "transcript_not_found"
    INVALID_FORMAT = "invalid_format"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"


class ErrorDetail(BaseModel):
    """Detailed error information."""
    model_config = ConfigDict(from_attributes=True)

    code: ErrorCode = Field(..., description="Error code")
    message: str = Field(..., description="Human-readable error message")
    field: Optional[str] = Field(None, description="Field that caused the error")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")


class APIResponse(BaseModel, Generic[T]):
    """Generic API response wrapper."""
    model_config = ConfigDict(from_attributes=True)

    status: APIStatus = Field(..., description="Response status")
    data: Optional[T] = Field(None, description="Response data")
    message: Optional[str] = Field(None, description="Response message")
    errors: Optional[List[ErrorDetail]] = Field(None, description="Error details")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")
    request_id: Optional[str] = Field(None, description="Request correlation ID")


class SuccessResponse(APIResponse[T]):
    """Success response with data."""

    def __init__(self, data: T, message: Optional[str] = None, **kwargs):
        super().__init__(
            status=APIStatus.SUCCESS,
            data=data,
            message=message,
            **kwargs
        )


class ErrorResponse(APIResponse[None]):
    """Error response with error details."""

    def __init__(
        self,
        errors: List[ErrorDetail],
        message: Optional[str] = None,
        **kwargs
    ):
        super().__init__(
            status=APIStatus.ERROR,
            data=None,
            errors=errors,
            message=message,
            **kwargs
        )


class ValidationErrorResponse(ErrorResponse):
    """Specific response for validation errors."""

    def __init__(self, field_errors: Dict[str, str], **kwargs):
        errors = [
            ErrorDetail(
                code=ErrorCode.VALIDATION_ERROR,
                message=message,
                field=field
            )
            for field, message in field_errors.items()
        ]
        super().__init__(
            errors=errors,
            message="Validation failed",
            **kwargs
        )


class NotFoundResponse(ErrorResponse):
    """Response for resource not found errors."""

    def __init__(self, resource_type: str, resource_id: str, **kwargs):
        error = ErrorDetail(
            code=ErrorCode.NOT_FOUND,
            message=f"{resource_type} with ID '{resource_id}' not found",
            details={"resource_type": resource_type, "resource_id": resource_id}
        )
        super().__init__(
            errors=[error],
            message=f"{resource_type} not found",
            **kwargs
        )


class PaginationInfo(BaseModel):
    """Pagination information for list responses."""
    model_config = ConfigDict(from_attributes=True)

    page: int = Field(..., ge=1, description="Current page number")
    per_page: int = Field(..., ge=1, le=100, description="Items per page")
    total: int = Field(..., ge=0, description="Total number of items")
    total_pages: int = Field(..., ge=0, description="Total number of pages")
    has_next: bool = Field(..., description="Whether there is a next page")
    has_prev: bool = Field(..., description="Whether there is a previous page")


class PaginatedResponse(BaseModel, Generic[T]):
    """Paginated response wrapper."""
    model_config = ConfigDict(from_attributes=True)

    items: List[T] = Field(..., description="List of items")
    pagination: PaginationInfo = Field(..., description="Pagination information")


class HealthResponse(BaseModel):
    """Health check response."""
    model_config = ConfigDict(from_attributes=True)

    status: str = Field(..., description="Overall health status")
    version: str = Field(..., description="API version")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Health check timestamp")
    services: Dict[str, str] = Field(default_factory=dict, description="Service health status")
    uptime_seconds: float = Field(..., description="Application uptime in seconds")


class OperationResult(BaseModel):
    """Result of an operation like create, update, delete."""
    model_config = ConfigDict(from_attributes=True)

    success: bool = Field(..., description="Whether operation succeeded")
    operation: str = Field(..., description="Type of operation performed")
    resource_id: Optional[str] = Field(None, description="ID of affected resource")
    message: Optional[str] = Field(None, description="Operation result message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional operation details")


class BatchOperationResult(BaseModel):
    """Result of a batch operation."""
    model_config = ConfigDict(from_attributes=True)

    total_requested: int = Field(..., description="Total items requested for processing")
    successful: int = Field(..., description="Number of successful operations")
    failed: int = Field(..., description="Number of failed operations")
    errors: List[ErrorDetail] = Field(default_factory=list, description="Errors encountered")
    results: List[OperationResult] = Field(default_factory=list, description="Individual operation results")