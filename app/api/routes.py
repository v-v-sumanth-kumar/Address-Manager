"""API route definitions and dependency injection helpers."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import get_db
from app.schemas.address import (
    AddressCreate,
    AddressResponse,
    AddressUpdate,
    HealthData,
    NearbyAddressResponse,
    PaginatedAddressData,
    SortField,
    SortOrder,
    SuccessResponse,
)
from app.services.address_service import AddressService

router = APIRouter()
settings = get_settings()


def get_address_service(
    db: Annotated[Session, Depends(get_db)],
) -> AddressService:
    """Provide an AddressService instance for the current request."""
    return AddressService(db)


AddressServiceDep = Annotated[AddressService, Depends(get_address_service)]


@router.get(
    "/health",
    response_model=SuccessResponse[HealthData],
    summary="Health check",
    description="Returns application health status for load balancers and monitoring.",
    responses={
        200: {
            "description": "Service is healthy",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "data": {
                            "status": "healthy",
                            "app_name": "Address Book API",
                            "version": "1.0.0",
                        },
                    }
                }
            },
        }
    },
)
def health_check() -> SuccessResponse[HealthData]:
    """Verify that the API is running and responsive."""
    return SuccessResponse(
        data=HealthData(
            app_name=settings.app_name,
            version=settings.app_version,
        )
    )


@router.post(
    "/addresses",
    response_model=SuccessResponse[AddressResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Create a new address",
    description="Create a new address record with validated geographic coordinates.",
    responses={
        201: {
            "description": "Address created successfully",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "data": {
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
                        },
                    }
                }
            },
        },
        422: {
            "description": "Validation error",
            "content": {
                "application/json": {
                    "example": {"success": False, "message": "body.latitude: Input should be <= 90"},
                }
            },
        },
    },
)
def create_address(
    payload: AddressCreate,
    service: AddressServiceDep,
) -> SuccessResponse[AddressResponse]:
    """Create a new address in the address book."""
    address = service.create_address(payload)
    return SuccessResponse(data=address)


@router.get(
    "/addresses",
    response_model=SuccessResponse[PaginatedAddressData],
    summary="List all addresses",
    description=(
        "Retrieve addresses with pagination, optional sorting, country filter, and name search."
    ),
    responses={
        200: {
            "description": "Paginated list of addresses",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "data": {
                            "items": [],
                            "pagination": {
                                "page": 1,
                                "page_size": 10,
                                "total_items": 0,
                                "total_pages": 0,
                                "has_next": False,
                                "has_previous": False,
                            },
                        },
                    }
                }
            },
        }
    },
)
def list_addresses(
    service: AddressServiceDep,
    page: Annotated[int, Query(ge=1, description="Page number (1-based)")] = 1,
    page_size: Annotated[
        int | None,
        Query(ge=1, le=100, description="Items per page (max 100)"),
    ] = None,
    sort_by: Annotated[
        SortField,
        Query(description="Field to sort results by"),
    ] = "created_at",
    sort_order: Annotated[
        SortOrder,
        Query(description="Sort direction"),
    ] = "desc",
    country: Annotated[
        str | None,
        Query(description="Filter by country (case-insensitive partial match)"),
    ] = None,
    name: Annotated[
        str | None,
        Query(description="Search by name or city (case-insensitive partial match)"),
    ] = None,
) -> SuccessResponse[PaginatedAddressData]:
    """Return a paginated list of addresses with optional filters."""
    data = service.list_addresses(
        page=page,
        page_size=page_size,
        sort_by=sort_by,
        sort_order=sort_order,
        country=country,
        name=name,
    )
    return SuccessResponse(data=data)


@router.get(
    "/addresses/nearby",
    response_model=SuccessResponse[list[NearbyAddressResponse]],
    summary="Search addresses by proximity",
    description=(
        "Find addresses within a given radius (km) from a latitude/longitude "
        "using the Haversine formula."
    ),
    responses={
        200: {
            "description": "Nearby addresses sorted by distance",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "data": [
                            {
                                "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                                "name": "Acme Corporation",
                                "address_line1": "123 Main Street",
                                "city": "San Francisco",
                                "state": "CA",
                                "country": "United States",
                                "postal_code": "94105",
                                "latitude": 37.7749,
                                "longitude": -122.4194,
                                "distance_km": 0.5,
                                "created_at": "2024-01-15T10:30:00Z",
                                "updated_at": "2024-01-15T10:30:00Z",
                            }
                        ],
                    }
                }
            },
        },
        422: {
            "description": "Invalid coordinates or search parameters",
            "content": {
                "application/json": {
                    "example": {"success": False, "message": "query.latitude: Input should be <= 90"},
                }
            },
        },
    },
)
def search_nearby_addresses(
    service: AddressServiceDep,
    latitude: Annotated[float, Query(ge=-90.0, le=90.0, description="Origin latitude")],
    longitude: Annotated[float, Query(ge=-180.0, le=180.0, description="Origin longitude")],
    distance_km: Annotated[float, Query(gt=0, description="Search radius in kilometers")],
) -> SuccessResponse[list[NearbyAddressResponse]]:
    """Return addresses within the specified distance from the given coordinates."""
    results = service.find_nearby(latitude, longitude, distance_km)
    return SuccessResponse(data=results)


@router.get(
    "/addresses/{address_id}",
    response_model=SuccessResponse[AddressResponse],
    summary="Get a single address",
    description="Retrieve an address by its unique identifier.",
    responses={
        200: {"description": "Address found"},
        404: {
            "description": "Address not found",
            "content": {
                "application/json": {
                    "example": {"success": False, "message": "Address not found"},
                }
            },
        },
    },
)
def get_address(
    address_id: UUID,
    service: AddressServiceDep,
) -> SuccessResponse[AddressResponse]:
    """Retrieve a single address by ID."""
    address = service.get_address(address_id)
    return SuccessResponse(data=address)


@router.put(
    "/addresses/{address_id}",
    response_model=SuccessResponse[AddressResponse],
    summary="Update an address",
    description="Update one or more fields of an existing address.",
    responses={
        200: {"description": "Address updated successfully"},
        404: {
            "description": "Address not found",
            "content": {
                "application/json": {
                    "example": {"success": False, "message": "Address not found"},
                }
            },
        },
        422: {"description": "Validation error"},
    },
)
def update_address(
    address_id: UUID,
    payload: AddressUpdate,
    service: AddressServiceDep,
) -> SuccessResponse[AddressResponse]:
    """Update an existing address."""
    address = service.update_address(address_id, payload)
    return SuccessResponse(data=address)


@router.delete(
    "/addresses/{address_id}",
    response_model=SuccessResponse[dict[str, str]],
    summary="Delete an address",
    description="Permanently remove an address from the address book.",
    responses={
        200: {
            "description": "Address deleted successfully",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "data": {"message": "Address deleted successfully"},
                    }
                }
            },
        },
        404: {
            "description": "Address not found",
            "content": {
                "application/json": {
                    "example": {"success": False, "message": "Address not found"},
                }
            },
        },
    },
)
def delete_address(
    address_id: UUID,
    service: AddressServiceDep,
) -> SuccessResponse[dict[str, str]]:
    """Delete an address by ID."""
    service.delete_address(address_id)
    return SuccessResponse(data={"message": "Address deleted successfully"})
