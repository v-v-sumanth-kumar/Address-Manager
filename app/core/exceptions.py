"""Custom application exceptions."""

from uuid import UUID


class AddressBookError(Exception):
    """Base exception for address book application errors."""

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class AddressNotFoundError(AddressBookError):
    """Raised when an address with the given ID does not exist."""

    def __init__(self, address_id: UUID) -> None:
        super().__init__(f"Address not found: {address_id}")
        self.address_id = address_id


class InvalidSearchParameterError(AddressBookError):
    """Raised when search parameters are invalid."""
