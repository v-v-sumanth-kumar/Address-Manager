"""Business logic and repository layer for address operations."""

import math
from uuid import UUID

from sqlalchemy import asc, desc, func, or_, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.exceptions import AddressNotFoundError, InvalidSearchParameterError
from app.core.logging import get_logger
from app.models.address import Address, utc_now
from app.schemas.address import (
    AddressCreate,
    AddressResponse,
    AddressUpdate,
    NearbyAddressResponse,
    PaginatedAddressData,
    PaginationMeta,
    SortField,
    SortOrder,
)
from app.utils.geo import haversine_distance_km

logger = get_logger(__name__)
settings = get_settings()


class AddressRepository:
    """Data access layer for address entities."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, address_data: AddressCreate) -> Address:
        """Persist a new address record."""
        address = Address(**address_data.model_dump())
        self.db.add(address)
        self.db.commit()
        self.db.refresh(address)
        return address

    def get_by_id(self, address_id: UUID) -> Address | None:
        """Retrieve an address by primary key."""
        return self.db.get(Address, address_id)

    def get_all(self) -> list[Address]:
        """Retrieve all addresses without filtering."""
        stmt = select(Address)
        return list(self.db.scalars(stmt).all())

    def list_addresses(
        self,
        *,
        page: int,
        page_size: int,
        sort_by: SortField,
        sort_order: SortOrder,
        country: str | None,
        name: str | None,
    ) -> tuple[list[Address], int]:
        """
        List addresses with pagination, sorting, and optional filters.

        Returns:
            Tuple of (addresses for current page, total matching count).
        """
        stmt = select(Address)
        count_stmt = select(func.count()).select_from(Address)

        if country:
            country_term = f"%{country.strip()}%"
            country_filter = Address.country.ilike(country_term)
            stmt = stmt.where(country_filter)
            count_stmt = count_stmt.where(country_filter)

        if name:
            name_term = f"%{name.strip()}%"
            name_filter = or_(
                Address.name.ilike(name_term),
                Address.city.ilike(name_term),
            )
            stmt = stmt.where(name_filter)
            count_stmt = count_stmt.where(name_filter)

        sort_column = getattr(Address, sort_by)
        ordering = asc(sort_column) if sort_order == "asc" else desc(sort_column)
        stmt = stmt.order_by(ordering)

        offset = (page - 1) * page_size
        stmt = stmt.offset(offset).limit(page_size)

        addresses = list(self.db.scalars(stmt).all())
        total = self.db.scalar(count_stmt) or 0
        return addresses, total

    def update(self, address: Address, address_data: AddressUpdate) -> Address:
        """Apply partial updates to an existing address."""
        update_data = address_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(address, field, value)
        address.updated_at = utc_now()
        self.db.commit()
        self.db.refresh(address)
        return address

    def delete(self, address: Address) -> None:
        """Remove an address from the database."""
        self.db.delete(address)
        self.db.commit()


class AddressService:
    """Service layer orchestrating address CRUD and search operations."""

    def __init__(self, db: Session) -> None:
        self.repository = AddressRepository(db)

    def create_address(self, address_data: AddressCreate) -> AddressResponse:
        """Create a new address and return the persisted record."""
        logger.info("Creating address: name=%s city=%s", address_data.name, address_data.city)
        address = self.repository.create(address_data)
        logger.info("Address created successfully: id=%s", address.id)
        return AddressResponse.model_validate(address)

    def get_address(self, address_id: UUID) -> AddressResponse:
        """Retrieve a single address by ID."""
        address = self.repository.get_by_id(address_id)
        if address is None:
            logger.error("Address not found: id=%s", address_id)
            raise AddressNotFoundError(address_id)
        return AddressResponse.model_validate(address)

    def list_addresses(
        self,
        *,
        page: int = 1,
        page_size: int | None = None,
        sort_by: SortField = "created_at",
        sort_order: SortOrder = "desc",
        country: str | None = None,
        name: str | None = None,
    ) -> PaginatedAddressData:
        """Return a paginated, filterable list of addresses."""
        effective_page_size = page_size or settings.default_page_size
        effective_page_size = min(effective_page_size, settings.max_page_size)

        if page < 1:
            raise InvalidSearchParameterError("page must be greater than or equal to 1")
        if effective_page_size < 1:
            raise InvalidSearchParameterError("page_size must be greater than or equal to 1")

        addresses, total = self.repository.list_addresses(
            page=page,
            page_size=effective_page_size,
            sort_by=sort_by,
            sort_order=sort_order,
            country=country,
            name=name,
        )

        total_pages = math.ceil(total / effective_page_size) if total > 0 else 0

        pagination = PaginationMeta(
            page=page,
            page_size=effective_page_size,
            total_items=total,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_previous=page > 1 and total > 0,
        )

        items = [AddressResponse.model_validate(addr) for addr in addresses]
        logger.info(
            "Listed addresses: page=%s page_size=%s total=%s",
            page,
            effective_page_size,
            total,
        )
        return PaginatedAddressData(items=items, pagination=pagination)

    def update_address(
        self,
        address_id: UUID,
        address_data: AddressUpdate,
    ) -> AddressResponse:
        """Update an existing address."""
        address = self.repository.get_by_id(address_id)
        if address is None:
            logger.error("Address not found for update: id=%s", address_id)
            raise AddressNotFoundError(address_id)

        if not address_data.model_dump(exclude_unset=True):
            raise InvalidSearchParameterError("At least one field must be provided for update")

        logger.info("Updating address: id=%s", address_id)
        updated = self.repository.update(address, address_data)
        logger.info("Address updated successfully: id=%s", address_id)
        return AddressResponse.model_validate(updated)

    def delete_address(self, address_id: UUID) -> None:
        """Delete an address by ID."""
        address = self.repository.get_by_id(address_id)
        if address is None:
            logger.error("Address not found for deletion: id=%s", address_id)
            raise AddressNotFoundError(address_id)

        logger.info("Deleting address: id=%s", address_id)
        self.repository.delete(address)
        logger.info("Address deleted successfully: id=%s", address_id)

    def find_nearby(
        self,
        latitude: float,
        longitude: float,
        distance_km: float,
    ) -> list[NearbyAddressResponse]:
        """
        Find all addresses within the given radius using the Haversine formula.

        Args:
            latitude: Origin latitude in degrees.
            longitude: Origin longitude in degrees.
            distance_km: Search radius in kilometers.

        Returns:
            List of matching addresses sorted by ascending distance.
        """
        if distance_km <= 0:
            raise InvalidSearchParameterError("distance_km must be greater than 0")

        all_addresses = self.repository.get_all()
        nearby: list[NearbyAddressResponse] = []

        for address in all_addresses:
            distance = haversine_distance_km(
                latitude,
                longitude,
                address.latitude,
                address.longitude,
            )
            if distance <= distance_km:
                base = AddressResponse.model_validate(address)
                nearby.append(
                    NearbyAddressResponse(
                        **base.model_dump(),
                        distance_km=round(distance, 4),
                    )
                )

        nearby.sort(key=lambda item: item.distance_km)
        logger.info(
            "Nearby search completed: lat=%s lon=%s radius_km=%s results=%s",
            latitude,
            longitude,
            distance_km,
            len(nearby),
        )
        return nearby
