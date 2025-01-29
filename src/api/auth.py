import logging, random, string

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Request
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.security import OAuth2PasswordRequestForm
from src.schemas import User, UserCreate, Token, TokenRefreshRequest, RequestEmail
from src.services.users import UserService
from src.services.auth import (
    Hash,
    create_access_token,
    create_refresh_token,
    verify_refresh_token,
    get_email_from_token
)
from src.services.email import (
    send_email,
    create_email_token,
    send_reset_password_email,
    send_new_password_email
)
from src.database.db import get_db

router = APIRouter(prefix="/auth", tags=["auth"])
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


async def check_user_exists(
    user_service: UserService, email: str, username: str
) -> None:
    """
    Checks if a user with a given email or username already exists in the database.

    Args:
        user_service (UserService): Service for performing user-related operations.
        email (str): Email of the user to check.
        username (str): Username of the user to check.

    Raises:
        HTTPException: If a user with the given email or username exists.

    Returns:
        None
    """
    email_user = await user_service.get_user_by_email(email)
    if email_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this email already exists.",
        )

    username_user = await user_service.get_user_by_username(username)
    if username_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this username already exists.",
        )


@router.post("/register", response_model=User, status_code=status.HTTP_201_CREATED)
async def register_user(
    user_data: UserCreate,
    background_tasks: BackgroundTasks,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Registers a new user by creating an account and sending a confirmation email.

    Args:
        user_data (UserCreate): The data required to create a new user, including username, email, and password.
        background_tasks (BackgroundTasks): Used to manage background operations such as sending emails.
        request (Request): Provides information about the current HTTP request.
        db (AsyncSession): The database session dependency for performing operations.

    Raises:
        HTTPException: If a user with the given email or username already exists.

    Returns:
        User: The newly created user object.
    """
    user_service = UserService(db)
    await check_user_exists(user_service, user_data.email, user_data.username)

    user_data.password = Hash().get_password_hash(user_data.password)
    new_user = await user_service.create_user(user_data)
    background_tasks.add_task(
        send_email, new_user.email, new_user.username, request.base_url
    )

    logger.info(f"User {new_user.username} registered successfully.")
    return new_user


@router.post("/login", response_model=Token)
async def login_user(
    form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)
):
    """
    Authenticates a user and returns JWT tokens for authorized access.

    Args:
        form_data: OAuth2PasswordRequestForm containing the username and password.
        db: Database session for performing database operations.

    Raises:
        HTTPException: If the username or password is incorrect, or if the email is not confirmed.

    Returns:
        A dictionary containing the access token, refresh token, and token type.
    """
    user_service = UserService(db)
    user = await user_service.get_user_by_username(form_data.username)

    if not user or not Hash().verify_password(form_data.password, user.hashed_password):
        logger.warning(f"Failed login attempt for username: {form_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.confirmed:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email not confirmed. Please confirm your email first.",
        )

    # Generate tokens
    access_token = await create_access_token(data={"sub": user.username})
    refresh_token = await create_refresh_token(data={"sub": user.username})

    # Store the refresh token in the database
    user.refresh_token = refresh_token
    await db.commit()
    await db.refresh(user)
    logger.info(f"User {user.username} logged in successfully.")

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


@router.post("/refresh-token", response_model=Token)
async def new_token(request: TokenRefreshRequest, db: AsyncSession = Depends(get_db)):
    """
    Create new access and refresh token

    Args:
        request: TokenRefreshRequest
        db: AsyncSession

    Returns:
        AccessToken
        RefreshToken
        TokenType
    """
    user = await verify_refresh_token(request.refresh_token, db)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )

    new_access_token = await create_access_token(data={"sub": user.username})
    new_refresh_token = await create_refresh_token(data={"sub": user.username})
    user.refresh_token = new_refresh_token
    await db.commit()
    await db.refresh(user)
    return {
        "access_token": new_access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer",
    }


@router.post("/request-password-reset", status_code=status.HTTP_200_OK)
async def request_password_reset(
    user_data: RequestEmail,
    background_tasks: BackgroundTasks,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Initiates the password reset process for a user by sending a reset email.

    Args:
        user_data: Contains the email of the user requesting the password reset.
        background_tasks: Manages background tasks such as sending emails.
        request: Provides information about the current HTTP request.
        db: Database session for performing database operations.

    Raises:
        HTTPException: If a user with the specified email does not exist.

    Returns:
        A message indicating that the password reset email has been sent.
    """
    user_service = UserService(db)
    user = await user_service.get_user_by_email(user_data.email)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User with this email does not exist.",
        )

    reset_token = create_email_token(data={"sub": user.email})
    background_tasks.add_task(
        send_reset_password_email, user.email, user.username, request.base_url, reset_token
    )
    return {"message": "Password reset email has been sent."}


@router.get("/reset-password", status_code=status.HTTP_200_OK)
async def validate_reset_token(
    token: str,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """
    Validates a password reset token, resets the user's password, and sends a new password email.

    Args:
        token (str): The token used to validate the user's identity for password reset.
        background_tasks (BackgroundTasks): Manages background tasks such as sending emails.
        db (AsyncSession): The database session dependency for performing operations.

    Raises:
        HTTPException: If the token is invalid, expired, or the user does not exist.

    Returns:
        dict: A message indicating the token is valid and the email address associated with it.
    """
    try:
        # Validate token and retrieve email
        email = await get_email_from_token(token)
    except Exception:
        # If token is invalid or expired
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired token.",
        )

    user_service = UserService(db)
    user = await user_service.get_user_by_email(email)

    if not user:
        # If user is not found in the database
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )

    # Generate a new password
    new_password = ''.join(random.choices(string.ascii_letters + string.digits, k=12))
    hashed_password = Hash().get_password_hash(new_password)

    # Update password
    await user_service.update_password(email, hashed_password)

    # Automatically trigger password reset email
    background_tasks.add_task(send_new_password_email, email, user.username, new_password)
    return {"message": "Token is valid. Proceed with password reset.", "email": email}


@router.get("/confirm-email/{token}")
async def confirmed_email(token: str, db: AsyncSession = Depends(get_db)):
    """
    Confirms a user's email address using a provided token.

    Args:
        token (str): The token to verify the user's identity.
        db (AsyncSession): Database session dependency.

    Raises:
        HTTPException: If the token is invalid or the user does not exist.

    Returns:
        dict: A success message indicating the email has been confirmed.
    """
    email = await get_email_from_token(token)
    user_service = UserService(db)
    user = await user_service.get_user_by_email(email)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Verification error"
        )
    if user.confirmed:
        return {"message": "Email already confirmed"}
    await user_service.confirmed_email(email)
    return {"message": "Email confirmed successfully"}


@router.post("/request-email")
async def request_email(
    user_data: RequestEmail,
    background_tasks: BackgroundTasks,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Requests an email confirmation link to be sent to a user's email.

    Args:
        user_data (RequestEmail): Contains the email of the user requesting the confirmation link.
        background_tasks (BackgroundTasks): Manages background tasks such as sending emails.
        request (Request): Provides information about the current HTTP request.
        db (AsyncSession): Database session for performing database operations.

    Raises:
        HTTPException: If a user with the specified email does not exist.

    Returns:
        dict: A message indicating that the confirmation email has been sent.
    """
    user_service = UserService(db)
    user = await user_service.get_user_by_email(user_data.email)

    # Handle the case when the user does not exist
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User with this email does not exist.",
        )

    if user.confirmed:
        return {"message": "Email already confirmed"}

    if user:
        background_tasks.add_task(
            send_email, user.email, user.username, request.base_url
        )
    return {"message": "Check your email for confirmation link."}