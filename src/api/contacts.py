from typing import List, Optional

from fastapi import APIRouter, HTTPException, Depends, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.db import get_db
from src.schemas import (
    ContactCreate,
    ContactUpdate,
    ContactResponse,
    User
)
from src.services.contacts import ContactService
from src.services.auth import get_current_user

router = APIRouter(prefix="/contacts", tags=["contacts"])


def get_contact_service(db: AsyncSession = Depends(get_db)) -> ContactService:
    """
    Provides a ContactService instance with a database session dependency.

    Args:
        db (AsyncSession): The database session provided by dependency injection.

    Returns:
        ContactService: An instance of the ContactService class.
    """
    return ContactService(db)


def ensure_contact_exists(contact):
    """
    Raises an HTTPException if the provided contact is None.

    Args:
        contact (Contact): The contact to check.

    Returns:
        Contact: The contact if it exists.

    Raises:
        HTTPException: If the contact does not exist.
    """
    if contact is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found"
        )
    return contact


@router.get("/", response_model=List[ContactResponse])
async def read_contacts(
    skip: int = Query(0, ge=0, description="Number of contacts to skip"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of contacts to return"),
    name: Optional[str] = Query(None),
    surname: Optional[str] = Query(None),
    email: Optional[str] = Query(None),
    contact_service: ContactService = Depends(get_contact_service),
    user: User = Depends(get_current_user)
):
    """
    Retrieves a list of contacts for the user with optional search query and pagination.

    Args:
        skip (int): The number of contacts to skip.
        limit (int): The maximum number of contacts to return.
        name (Optional[str]): The name to search for.
        surname (Optional[str]): The surname to search for.
        email (Optional[str]): The email to search for.

    Returns:
        List[ContactResponse]: A list of contacts matching the search criteria.
    """
    return await contact_service.get_contacts(skip, limit, user, name, surname, email)


@router.post("/", response_model=ContactResponse, status_code=status.HTTP_201_CREATED)
async def create_contact(
    body: ContactCreate,
    user: User = Depends(get_current_user),
    contact_service: ContactService = Depends(get_contact_service),
):
    """
    Creates a new contact for the user if it doesn't already exist.

    Args:
        body (ContactCreate): The contact creation data.
        user (User): The user creating the contact.

    Raises:
        HTTPException: If a contact with the provided email already exists, or if the contact creation fails.

    Returns:
        ContactResponse: The newly created contact.
    """
    contact = await contact_service.create_contact(body, user)
    if not contact:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create contact"
        )
    return contact


router.get("/birthdays-next-week", response_model=List[ContactResponse])


@router.get("/birthdays/upcoming", response_model=List[ContactResponse])
async def get_upcoming_birthdays(
    days: int = Query(7), db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """
    Retrieves a list of contacts with birthdays in the upcoming specified number of days.

    Args:
        days (int): The number of days ahead to check for upcoming birthdays. Defaults to 7.
        db (AsyncSession): The database session provided by dependency injection.
        user (User): The user whose contacts' birthdays are being retrieved.

    Returns:
        List[ContactResponse]: A list of contacts with upcoming birthdays.
    """
    contact_service = ContactService(db)
    contacts = await contact_service.get_upcoming_birthdays(user, days)
    return contacts


@router.get("/{contact_id}", response_model=ContactResponse)
async def read_contact(
    contact_id: int,
    user: User = Depends(get_current_user),
    contact_service: ContactService = Depends(get_contact_service),
):
    """
    Retrieves a single contact by ID for the user.

    Args:
        contact_id (int): The ID of the contact to retrieve.
        user (User): The user whose contact to retrieve.
        contact_service (ContactService): The contact service instance.

    Raises:
        HTTPException: If the contact with the provided ID does not exist.

    Returns:
        ContactResponse: The contact with the given ID.
    """
    contact = await contact_service.get_contact(contact_id, user)
    return ensure_contact_exists(contact)


@router.put("/{contact_id}", response_model=ContactResponse)
async def update_contact(
    contact_id: int,
    body: ContactUpdate,
    user: User = Depends(get_current_user),
    contact_service: ContactService = Depends(get_contact_service),
):
    """
    Updates a contact by ID for the user.

    Args:
        contact_id (int): The ID of the contact to update.
        body (ContactUpdate): The contact update data.
        user (User): The user whose contact to update.
        contact_service (ContactService): The contact service instance.

    Raises:
        HTTPException: If the contact with the provided ID does not exist.

    Returns:
        ContactResponse: The updated contact.
    """
    contact = await contact_service.update_contact(contact_id, body, user)
    return ensure_contact_exists(contact)


@router.delete("/{contact_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_contact(
    contact_id: int,
    user: User = Depends(get_current_user),
    contact_service: ContactService = Depends(get_contact_service),
):
    """
    Removes a contact by ID for the user.

    Args:
        contact_id (int): The ID of the contact to remove.
        user (User): The user whose contact to remove.
        contact_service (ContactService): The contact service instance.

    Raises:
        HTTPException: If the contact with the provided ID does not exist.

    Returns:
        None
    """
    await contact_service.remove_contact(contact_id, user)
    return None