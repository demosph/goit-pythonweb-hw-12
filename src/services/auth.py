import logging
import json

from datetime import datetime, timedelta, UTC
from typing import Literal,Optional

from fastapi import Depends, HTTPException, status
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from jose import JWTError, jwt

from src.redis import get_redis
from src.database.db import get_db
from src.conf.config import settings
from src.services.users import UserService
from src.database.models import User, UserRole


logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

class Hash:
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    def verify_password(self, plain_password, hashed_password):
        """
        Verifies that the plain password matches the hashed password.
        """
        return self.pwd_context.verify(plain_password, hashed_password)

    def get_password_hash(self, password: str) -> str:
        """
        Returns the hashed version of the given password.
        """
        return self.pwd_context.hash(password)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


# define a function to generate a new access token
async def create_token(
    data: dict, token_type: Literal["access", "refresh"], expires_delta: timedelta
):
    """
    Create a new access or refresh token.

    Args:
        data (dict): The data to be included in the token.
        token_type (str): The type of token to be created.
        expires_delta (timedelta): The expiration time for the token.

    Returns:
        str: The generated token.
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(UTC) + timedelta(seconds=expires_delta)
    else:
        expire = datetime.now(UTC) + timedelta(
            seconds=int(settings.JWT_EXPIRATION_SECONDS)
        )
    to_encode.update({"exp": expire, "token_type": token_type})
    encoded_jwt = jwt.encode(
        to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM
    )
    return encoded_jwt


# define a function to create a new access token
async def create_access_token(data: dict, expires_delta: Optional[float] = None):
    """
    Create a new access token.

    Args:
        data (dict): The data to be included in the token.
        expires_delta (timedelta): The expiration time for the token.

    Returns:
        str: The generated access token.
    """
    if expires_delta:
        access_token = await create_token(data, "access", expires_delta)
    else:
        access_token = await create_token(data, "access", settings.JWT_EXPIRATION_SECONDS)
    return access_token


# define a function to create a new refresh token
async def create_refresh_token(data: dict, expires_delta: Optional[float] = None):
    """
    Create a new refresh token.

    Args:
        data (dict): The data to be included in the token.
        expires_delta (timedelta): The expiration time for the token.

    Returns:
        str: The generated refresh token.
    """
    if expires_delta:
        refresh_token = await create_token(data, "refresh", expires_delta)
    else:
        refresh_token = await create_token(
            data, "refresh", settings.JWT_REFRESH_EXPIRATION_SECONDS
        )
    return refresh_token


async def verify_refresh_token(
        refresh_token: str, db: AsyncSession = Depends(get_db)
    ):
    """
    Verify the refresh token.

    Args:
        refresh_token (str): The refresh token to be verified.
        db (Session): The database session to be used to verify the refresh token.

    Returns:
        User: The user associated with the refresh token.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(
            refresh_token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM]
        )
        username = payload.get("sub")
        token_type = payload.get("token_type")
        if username is None or token_type != "refresh":
            raise credentials_exception
        user = await UserService(db).get_user_by_username(username, refresh_token)
        return user
    except JWTError as e:
        raise credentials_exception


def create_email_token(data: dict):
    """
    Creates a token for email verification.

    Args:
        data (dict): The data to be included in the token.

    Returns:
        str: The generated token.
    """
    to_encode = data.copy()
    expire = datetime.now(UTC) + timedelta(days=7)
    to_encode.update({"iat": datetime.now(UTC), "exp": expire})
    token = jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    return token


async def get_email_from_token(token: str):
    """
    Extracts an email from a given token.

    Args:
        token (str): The token containing the email information.

    Raises:
        HTTPException: If the token is invalid or cannot be processed.

    Returns:
        str: The email extracted from the token.
    """
    try:
        payload = jwt.decode(
            token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM]
        )
        email = payload["sub"]
        return email
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid token for email verification",
        )


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
    redis_client=Depends(get_redis),
):
    """
    Retrieves the currently authenticated user from the database and caches it in Redis.

    Args:
        token (str): The JWT token from the Authorization header.
        db (AsyncSession): The database session to use for queries.
        redis_client (Redis): The Redis client to use for caching.

    Raises:
        HTTPException: If the token is invalid or if the user is not found in the database.

    Returns:
        User: The authenticated user.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(
            token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM]
        )
        username = payload.get("sub")
        token_type = payload.get("token_type")
        if username is None or token_type != "access":
            logger.error("Token is missing 'sub' claim.")
            raise credentials_exception
        logger.info(f"Token payload: {payload}")
    except JWTError as e:
        logger.error(f"JWT decode error: {e} | Token: {token}")
        raise credentials_exception

    # Check Redis cache
    cached_user = await redis_client.get(f"user:{username}")
    if cached_user:
        logger.info(f"User {username} retrieved from cache")
        user_data = json.loads(cached_user)
        return User(
            id=user_data["id"],
            username=user_data["username"],
            email=user_data["email"],
            avatar=user_data["avatar"],
            role=UserRole(user_data["role"]) if user_data["role"] else None,
        )

    # Fetch user from the database if not in cache
    user_service = UserService(db)
    user = await user_service.get_user_by_username(username)
    if user is None:
        logger.error(f"User not found: {username}")
        raise credentials_exception

    # Cache the user in Redis
    user_data = {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "avatar": user.avatar,
        "role": user.role.value if user.role else None,
    }

    await redis_client.set(f"user:{username}", json.dumps(user_data), ex=int(settings.REDIS_TTL or 3600))  # Cache for 1 hour
    logger.info(f"User {username} cached in Redis")
    logger.info(f"Authenticated user: {user.username}")

    return user

async def get_current_admin_user(current_user: User = Depends(get_current_user)):
    """
    Verifies that the current user is an admin.

    Args:
        current_user (User): The currently authenticated user, obtained from the get_current_user function.

    Raises:
        HTTPException: If the current user is not an admin.

    Returns:
        User: The current user if they are an admin.
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=403,
            detail="Only admin users can access this endpoint",
        )
    return current_user