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
        """
        Initialize the contact service.

        Args:
            db (AsyncSession): The database session.
        """
        self.contact_repository = ContactRepository(db)

    async def _ensure_exists(self, check_func, error_message: str, status_code: int):
        """
        Ensure that the given check_func returns a truthy value.

        Args:
            check_func (Callable): A function that takes no arguments and returns a value.
            error_message (str): The error message to log and return if the check_func returns a falsy value.
            status_code (int): The HTTP status code to use for the HTTPException.

        Returns:
            The result of the check_func.

        Raises:
            HTTPException: If the check_func returns a falsy value.
        """
        obj = await check_func()
        if not obj:
            logger.error(error_message)
            raise HTTPException(status_code=status_code, detail=error_message)
        return obj

    async def create_contact(self, body: ContactCreate, user: User):
        """
        Create a new contact for the user if it doesn't already exist.

        Args:
            body (ContactCreate): The contact creation data.
            user (User): The user creating the contact.

        Raises:
            HTTPException: If a contact with the provided email already exists.

        Returns:
            Contact: The newly created contact.
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
        Retrieves a list of contacts for the user with optional search query and pagination.

        Args:
            skip (int): The number of contacts to skip.
            limit (int): The maximum number of contacts to return.
            user (User): The user whose contacts to retrieve.
            name (Optional[str]): The name to search for.
            surname (Optional[str]): The surname to search for.
            email (Optional[str]): The email to search for.

        Returns:
            List: A list of contacts matching the search criteria.
        """
        contacts = await self.contact_repository.get_contacts(
            skip, limit, user, name, surname, email
        )
        logger.info(f"Retrieved {len(contacts)} contacts for user: {user}")
        return contacts

    async def get_contact(self, contact_id: int, user: User):
        """
        Retrieves a single contact by ID for the user.

        Args:
            contact_id (int): The ID of the contact to retrieve.
            user (User): The user whose contact to retrieve.

        Raises:
            HTTPException: If the contact with the provided ID does not exist.

        Returns:
            Contact: The contact with the provided ID.
        """
        return await self._ensure_exists(
            lambda: self.contact_repository.get_contact_by_id(contact_id, user),
            f"Contact with ID {contact_id} not found",
            status.HTTP_404_NOT_FOUND,
        )

    async def update_contact(self, contact_id: int, body: ContactUpdate, user: User):
        """
        Updates a contact by ID for the user.

        Args:
            contact_id (int): The ID of the contact to update.
            body (ContactUpdate): The contact update data.
            user (User): The user whose contact to update.

        Raises:
            HTTPException: If the contact with the provided ID does not exist.

        Returns:
            Contact: The updated contact.
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

        Args:
            contact_id (int): The ID of the contact to remove.
            user (User): The user whose contact to remove.

        Raises:
            HTTPException: If the contact with the provided ID does not exist.

        Returns:
            None
        """
        contact = await self.get_contact(contact_id, user)
        await self.contact_repository.remove_contact(contact.id, user)
        logger.info(f"Contact removed: ID {contact_id}")

    async def get_upcoming_birthdays(self, user: User, days: int = 7):
        """
        Retrieves a list of contacts whose birthdays are in the next given number of days.

        Args:
            user (User): The user whose contacts to retrieve.
            days (int): The number of days to look ahead for upcoming birthdays.

        Returns:
            List[Contact]: A list of contacts with upcoming birthdays.
        """
        contacts = await self.contact_repository.get_upcoming_birthdays(user, days)
        logger.info(
            f"Retrieved {len(contacts)} upcoming birthdays for user: {user}"
        )
        return contacts