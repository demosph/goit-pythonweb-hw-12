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
    return ContactService(db)


def ensure_contact_exists(contact):
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
    Get a list of contacts with optional search query and pagination.
    """
    return await contact_service.get_contacts(skip, limit, user, name, surname, email)


@router.post("/", response_model=ContactResponse, status_code=status.HTTP_201_CREATED)
async def create_contact(
    body: ContactCreate,
    user: User = Depends(get_current_user),
    contact_service: ContactService = Depends(get_contact_service),
):
    """
    Create a new contact with an address.
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
    Get a list of contacts whose birthdays are in the next `days` days.
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
    Get a contact by ID.
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
    Update contact details, including address, by ID.
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
    Remove a contact by ID.
    """
    await contact_service.remove_contact(contact_id, user)
    return None