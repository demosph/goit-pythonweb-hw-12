from typing import Optional, List
import logging

from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from src.repository.contacts import ContactRepository
from src.schemas import ContactCreate, ContactUpdate, User

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class ContactService:
    def __init__(self, db: AsyncSession):
        self.contact_repository = ContactRepository(db)

    async def _ensure_exists(self, check_func, error_message: str, status_code: int):
        obj = await check_func()
        if not obj:
            logger.error(error_message)
            raise HTTPException(status_code=status_code, detail=error_message)
        return obj

    async def create_contact(self, body: ContactCreate, user: User):
        """
        Creates a new contact for the given user.
        """
        existing_contact = await self.contact_repository.get_contact_by_email(body.email, user)
        if existing_contact:
            logger.warning(f"Duplicate contact creation attempt: {body.email}")
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Contact with this email already exists",
            )

        new_contact = await self.contact_repository.create_contact(body, user)
        logger.info(f"Contact created: {new_contact}")
        return new_contact

    async def get_contacts(
        self,
        skip: int,
        limit: int,
        user: User,
        name: Optional[str] = None,
        surname: Optional[str] = None,
        email: Optional[str] = None,
    ) -> List:
        """
        Retrieves a list of contacts for the user, with optional filters.
        """
        contacts = await self.contact_repository.get_contacts(
            skip, limit, user, name, surname, email
        )
        logger.info(f"Retrieved {len(contacts)} contacts for user: {user}")
        return contacts

    async def get_contact(self, contact_id: int, user: User):
        """
        Retrieves a specific contact by ID for the user.
        """
        return await self._ensure_exists(
            lambda: self.contact_repository.get_contact_by_id(contact_id, user),
            f"Contact with ID {contact_id} not found",
            status.HTTP_404_NOT_FOUND,
        )

    async def update_contact(self, contact_id: int, body: ContactUpdate, user: User):
        """
        Updates an existing contact for the user.
        """
        contact = await self.get_contact(contact_id, user)
        updated_contact = await self.contact_repository.update_contact(
            contact.id, body, user
        )
        logger.info(f"Contact updated: ID {contact_id}")
        return updated_contact

    async def remove_contact(self, contact_id: int, user: User):
        """
        Removes a contact by ID for the user.
        """
        contact = await self.get_contact(contact_id, user)
        await self.contact_repository.remove_contact(contact.id, user)
        logger.info(f"Contact removed: ID {contact_id}")

    async def get_upcoming_birthdays(self, user: User, days: int = 7):
        """
        Retrieves contacts with upcoming birthdays within the specified number of days.
        """
        contacts = await self.contact_repository.get_upcoming_birthdays(user, days)
        logger.info(
            f"Retrieved {len(contacts)} upcoming birthdays for user: {user}"
        )
        return contacts