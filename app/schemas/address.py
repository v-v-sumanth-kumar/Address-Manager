"""Pydantic schemas for address API requests and responses."""

from datetime import datetime
from typing import Any, Generic, Literal, TypeVar
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

T = TypeVar("T")

BLANK_FIELD_MESSAGE = "must not be blank or whitespace only"


def strip_and_validate_non_blank(value: str, field_name: str) -> str:
    """Strip whitespace and ensure the string is not empty."""
    stripped = value.strip()
    if not stripped:
        raise ValueError(f"{field_name} {BLANK_FIELD_MESSAGE}")
    return stripped


class AddressBase(BaseModel):
    """Shared address fields with validation rules."""

    name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Contact or location name",
        examples=["Acme Corporation"],
    )
    address_line1: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Primary street address",
        examples=["123 Main Street"],
    )
    address_line2: str | None = Field(
        default=None,
        max_length=500,
        description="Secondary address line (optional)",
        examples=["Suite 400"],
    )
    city: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="City name",
        examples=["San Francisco"],
    )
    state: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="State or province",
        examples=["CA"],
    )
    country: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Country name",
        examples=["United States"],
    )
    postal_code: str = Field(
        ...,
        min_length=1,
        max_length=20,
        description="Postal or ZIP code",
        examples=["94105"],
    )
    latitude: float = Field(
        ...,
        ge=-90.0,
        le=90.0,
        description="Latitude in decimal degrees",
        examples=[37.7749],
    )
    longitude: float = Field(
        ...,
        ge=-180.0,
        le=180.0,
        description="Longitude in decimal degrees",
        examples=[-122.4194],
    )

    @field_validator("name", "address_line1", "city", "state", "country", "postal_code")
    @classmethod
    def validate_required_strings(cls, value: str) -> str:
        """Ensure required string fields are not blank after stripping."""
        return strip_and_validate_non_blank(value, "field")

    @field_validator("address_line2")
    @classmethod
    def validate_optional_line2(cls, value: str | None) -> str | None:
        """Normalize optional address line 2."""
        if value is None:
            return None
        stripped = value.strip()
        return stripped or None


class AddressCreate(AddressBase):
    """Schema for creating a new address."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "name": "Acme Corporation",
                    "address_line1": "123 Main Street",
                    "address_line2": "Suite 400",
                    "city": "San Francisco",
                    "state": "CA",
                    "country": "United States",
                    "postal_code": "94105",
                    "latitude": 37.7749,
                    "longitude": -122.4194,
                }
            ]
        }
    )


class AddressUpdate(BaseModel):
    """Schema for partially or fully updating an address."""

    name: str | None = Field(default=None, min_length=1, max_length=255)
    address_line1: str | None = Field(default=None, min_length=1, max_length=500)
    address_line2: str | None = Field(default=None, max_length=500)
    city: str | None = Field(default=None, min_length=1, max_length=100)
    state: str | None = Field(default=None, min_length=1, max_length=100)
    country: str | None = Field(default=None, min_length=1, max_length=100)
    postal_code: str | None = Field(default=None, min_length=1, max_length=20)
    latitude: float | None = Field(default=None, ge=-90.0, le=90.0)
    longitude: float | None = Field(default=None, ge=-180.0, le=180.0)

    @field_validator(
        "name",
        "address_line1",
        "city",
        "state",
        "country",
        "postal_code",
    )
    @classmethod
    def validate_optional_strings(cls, value: str | None) -> str | None:
        """Validate optional string fields when provided."""
        if value is None:
            return None
        return strip_and_validate_non_blank(value, "field")

    @field_validator("address_line2")
    @classmethod
    def validate_optional_line2(cls, value: str | None) -> str | None:
        """Normalize optional address line 2 on update."""
        if value is None:
            return None
        stripped = value.strip()
        return stripped or None

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "name": "Acme Corp HQ",
                    "city": "Oakland",
                    "postal_code": "94607",
                }
            ]
        }
    )


class AddressResponse(AddressBase):
    """Schema for address API responses."""

    id: UUID = Field(..., description="Unique address identifier")
    created_at: datetime = Field(..., description="Record creation timestamp (UTC)")
    updated_at: datetime = Field(..., description="Record last update timestamp (UTC)")

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "examples": [
                {
                    "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                    "name": "Acme Corporation",
                    "address_line1": "123 Main Street",
                    "address_line2": "Suite 400",
                    "city": "San Francisco",
                    "state": "CA",
                    "country": "United States",
                    "postal_code": "94105",
                    "latitude": 37.7749,
                    "longitude": -122.4194,
                    "created_at": "2024-01-15T10:30:00Z",
                    "updated_at": "2024-01-15T10:30:00Z",
                }
            ]
        },
    )


class PaginationMeta(BaseModel):
    """Pagination metadata for list endpoints."""

    page: int = Field(..., description="Current page number (1-based)")
    page_size: int = Field(..., description="Number of items per page")
    total_items: int = Field(..., description="Total number of matching items")
    total_pages: int = Field(..., description="Total number of pages")
    has_next: bool = Field(..., description="Whether a next page exists")
    has_previous: bool = Field(..., description="Whether a previous page exists")


class PaginatedAddressData(BaseModel):
    """Paginated list of addresses with metadata."""

    items: list[AddressResponse]
    pagination: PaginationMeta


class NearbyAddressResponse(AddressResponse):
    """Address response including distance from search origin."""

    distance_km: float = Field(
        ...,
        ge=0.0,
        description="Distance from the search origin in kilometers",
        examples=[2.45],
    )

    model_config = ConfigDict(from_attributes=True)


class SuccessResponse(BaseModel, Generic[T]):
    """Standard successful API response wrapper."""

    success: bool = True
    data: T

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "success": True,
                    "data": {
                        "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                        "name": "Acme Corporation",
                        "address_line1": "123 Main Street",
                        "city": "San Francisco",
                        "state": "CA",
                        "country": "United States",
                        "postal_code": "94105",
                        "latitude": 37.7749,
                        "longitude": -122.4194,
                        "created_at": "2024-01-15T10:30:00Z",
                        "updated_at": "2024-01-15T10:30:00Z",
                    },
                }
            ]
        }
    )


class ErrorResponse(BaseModel):
    """Standard error API response wrapper."""

    success: bool = False
    message: str

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"success": False, "message": "Address not found"},
            ]
        }
    )


class HealthData(BaseModel):
    """Health check response payload."""

    status: Literal["healthy"] = "healthy"
    app_name: str
    version: str


SortField = Literal["name", "city", "created_at"]
SortOrder = Literal["asc", "desc"]


def format_validation_errors(errors: list[dict[str, Any]]) -> str:
    """
    Convert Pydantic validation errors into a human-readable message.

    Args:
        errors: List of validation error dictionaries from Pydantic.

    Returns:
        Formatted error message string.
    """
    messages: list[str] = []
    for error in errors:
        location = ".".join(str(part) for part in error.get("loc", ()))
        message = error.get("msg", "Invalid value")
        messages.append(f"{location}: {message}" if location else message)
    return "; ".join(messages)
