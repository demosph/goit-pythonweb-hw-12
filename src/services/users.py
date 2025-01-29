from sqlalchemy.ext.asyncio import AsyncSession

from libgravatar import Gravatar

from src.repository.users import UserRepository
from src.schemas import UserCreate


class UserService:
    def __init__(self, db: AsyncSession):
        """
        Initialize the user service.

        Args:
            db (AsyncSession): The database session.
        """
        self.repository = UserRepository(db)

    async def create_user(self, body: UserCreate):
        """
        Creates a new user with the given data and a default avatar URL using Gravatar.

        Args:
            body (UserCreate): The data required to create a new user, including username, email, and password.

        Returns:
            User: The newly created user object.
        """
        avatar = None
        try:
            g = Gravatar(body.email)
            avatar = g.get_image()
        except Exception as e:
            print(e)

        return await self.repository.create_user(body, avatar)

    async def get_user_by_id(self, user_id: int):
        """
        Retrieves a user by their ID.

        Args:
            user_id (int): The ID of the user to retrieve.

        Returns:
            User | None: The user object if found, otherwise None.
        """
        return await self.repository.get_user_by_id(user_id)

    async def get_user_by_username(self, username: str, refresh_token: str = None):
        """
        Retrieves a user by their username and optionally filters by refresh token.

        Args:
            username (str): The username of the user to retrieve.
            refresh_token (str, optional): The refresh token to filter by.

        Returns:
            User | None: The user object if found, otherwise None.
        """
        return await self.repository.get_user_by_username(username, refresh_token)

    async def get_user_by_email(self, email: str):
        """
        Retrieves a user by their email address.

        Args:
            email (str): The email address of the user to retrieve.

        Returns:
            User | None: The user object if found, otherwise None.
        """
        return await self.repository.get_user_by_email(email)

    async def confirmed_email(self, email: str):
        """
        Marks a user's email as confirmed.

        Args:
            email (str): The email address of the user to confirm.

        Returns:
            None
        """
        return await self.repository.confirmed_email(email)

    async def update_password(self, email: str, hashed_password: str):
        """
        Updates a user's password with a given hashed password.

        Args:
            email (str): The email address of the user to update.
            hashed_password (str): The new hashed password of the user.

        Raises:
            ValueError: If the user is not found.
        """
        user = await self.repository.get_user_by_email(email)
        if not user:
            raise ValueError("User not found")
        user.hashed_password = hashed_password
        await self.repository.update_user(user)

    async def update_avatar_url(self, email: str, url: str):
        """
        Updates a user's avatar URL.

        Args:
            email (str): The email address of the user whose avatar is to be updated.
            url (str): The new avatar URL.

        Returns:
            User: The updated user object with the new avatar URL.
        """
        return await self.repository.update_avatar_url(email, url)