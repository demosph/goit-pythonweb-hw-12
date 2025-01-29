from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import User
from src.schemas import UserCreate


class UserRepository:
    def __init__(self, session: AsyncSession):
        """
        Initialize the user repository.

        Args:
            session (AsyncSession): The database session.
        """
        self.db = session

    async def get_user_by_id(self, user_id: int) -> User | None:
        """
        Retrieve a user by their ID.

        Args:
            user_id (int): The ID of the user to retrieve.

        Returns:
            User | None: The user object if found, otherwise None.
        """
        stmt = select(User).filter_by(id=user_id)
        user = await self.db.execute(stmt)
        return user.scalar_one_or_none()

    async def get_user_by_username(self, username: str, refresh_token: str | None) -> User | None:
        """
        Retrieve a user by their username and optionally filter by refresh token.

        Args:
            username (str): The username of the user to retrieve.
            refresh_token (str | None): The refresh token to filter by, if provided.

        Returns:
            User | None: The user object if found, otherwise None.
        """
        stmt = select(User).filter_by(username=username)

        if refresh_token:
            stmt = stmt.filter_by(refresh_token=refresh_token)
        user = await self.db.execute(stmt)
        return user.scalar_one_or_none()

    async def get_user_by_email(self, email: str) -> User | None:
        """
        Retrieve a user by their email address.

        Args:
            email (str): The email address of the user to retrieve.

        Returns:
            User | None: The user object if found, otherwise None.
        """
        stmt = select(User).filter_by(email=email)
        user = await self.db.execute(stmt)
        return user.scalar_one_or_none()

    async def create_user(self, body: UserCreate, avatar: Optional[str] = None) -> User:
        """
        Creates a new user with the given data and a default avatar URL using Gravatar.

        Args:
            body (UserCreate): The data required to create a new user, including username, email, and password.
            avatar (str, optional): The avatar URL for the new user, if provided.

        Returns:
            User: The newly created user object.
        """
        user = User(
            **body.model_dump(exclude_unset=True, exclude={"password"}),
            hashed_password=body.password,
            avatar=avatar
        )
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def update_user(self, user: User) -> User:
        """
        Updates an existing user in the database.

        Args:
            user (User): The user object with updated information.

        Returns:
            User: The updated user object.
        """
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def confirmed_email(self, email: str) -> None:
        """
        Marks a user's email as confirmed.

        Args:
            email (str): The email address of the user to confirm.

        Returns:
            None
        """
        user = await self.get_user_by_email(email)
        user.confirmed = True
        await self.db.commit()

    async def update_avatar_url(self, email: str, url: str) -> User:
        """
        Updates a user's avatar URL.

        Args:
            email (str): The email address of the user to update.
            url (str): The new avatar URL.

        Returns:
            User: The updated user object if found, otherwise raises a ValueError.
        """
        user = await self.get_user_by_email(email)
        if user:
            user.avatar = url
            await self.db.commit()
            await self.db.refresh(user)
            return user
        else:
            raise ValueError("User not found")
