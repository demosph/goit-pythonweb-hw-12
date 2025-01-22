from typing import List, Optional
from datetime import datetime, timedelta

from sqlalchemy import and_, or_, select, extract
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.database.models import Contact, Address, User
from src.schemas import ContactUpdate, ContactCreate


class ContactRepository:
    def __init__(self, session: AsyncSession):
        self.db = session

    def _base_query(self):
        """
        Base query for retrieving contacts.
        """
        return select(Contact)

    async def get_contacts(
        self,
        skip: int,
        limit: int,
        user: User,
        name: Optional[str] = None,
        surname: Optional[str] = None,
        email: Optional[str] = None,
    ) -> List[Contact]:
        """
        Retrieve a list of contacts for a specific user with optional search query and pagination.
        """
        filters = [Contact.user == user]  # Ensure contacts belong to the user
        if name:
            filters.append(Contact.name.ilike(f"%{name}%"))
        if surname:
            filters.append(Contact.surname.ilike(f"%{surname}%"))
        if email:
            filters.append(Contact.email.ilike(f"%{email}%"))

        stmt = (
            self._base_query()
            .options(selectinload(Contact.address))
            .filter(and_(*filters))
            .offset(skip)
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_contact_by_id(self, contact_id: int, user: User) -> Optional[Contact]:
        """
        Retrieve a single contact by ID for a specific user with related address.
        """
        stmt = (
            self._base_query()
            .options(selectinload(Contact.address))
            .filter(and_(Contact.id == contact_id, Contact.user == user))
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_contact_by_email(
        self,
        email: str,
        user: User,
    ) -> Optional[Contact]:
        """
        Retrieve a single contact by email for a specific user with related address.
        """
        stmt = (
            self._base_query()
            .options(selectinload(Contact.address))
            .filter(and_(Contact.email == email, Contact.user == user))
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def create_contact(self, body: ContactCreate, user: User) -> Contact:
        """
        Create a new contact for a specific user with address.
        """
        address_data = body.address
        address = None
        if address_data:
            address = Address(**address_data.model_dump(exclude_unset=True))
            self.db.add(address)

        contact = Contact(
            **body.model_dump(exclude={"address"}, exclude_unset=True),
            address=address,
            user=user
        )
        self.db.add(contact)
        await self.db.commit()
        await self.db.refresh(contact)
        return contact

    async def remove_contact(self, contact_id: int, user: User) -> Optional[Contact]:
        """
        Remove a contact by ID for a specific user.
        """
        contact = await self.get_contact_by_id(contact_id, user)
        if contact:
            if contact.address:
                await self.db.delete(contact.address)
            await self.db.delete(contact)
            await self.db.commit()
        return contact

    async def update_contact(
        self, contact_id: int, body: ContactUpdate, user: User
    ) -> Optional[Contact]:
        """
        Update contact details for a specific user.
        """
        contact = await self.get_contact_by_id(contact_id, user)
        if not contact:
            return None

        for key, value in body.model_dump(exclude_unset=True, exclude={"address"}).items():
            setattr(contact, key, value)

        if body.address:
            if contact.address:
                for key, value in body.address.model_dump(exclude_unset=True).items():
                    setattr(contact.address, key, value)
            else:
                new_address = Address(**body.address.model_dump(exclude_unset=True))
                contact.address = new_address
                self.db.add(new_address)

        await self.db.commit()
        await self.db.refresh(contact)
        return contact

    async def get_upcoming_birthdays(self, user: User, days: int = 7) -> List[Contact]:
        """
        Retrieve contacts with upcoming birthdays within a given number of days for a specific user.
        """
        today = datetime.now().date()
        upcoming_date = today + timedelta(days=days)

        stmt = select(Contact).filter(
            or_(
                (extract("month", Contact.birthday) == today.month) & (extract("day", Contact.birthday) >= today.day),
                (extract("month", Contact.birthday) == upcoming_date.month)
                & (extract("day", Contact.birthday) <= upcoming_date.day),
            ),
            Contact.user == user,
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())