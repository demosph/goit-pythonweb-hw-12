from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile, status
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.db import get_db
from src.schemas import User
from src.conf.config import settings
from src.services.auth import get_current_user
from src.services.users import UserService
from src.services.upload_file import UploadFileService
import logging

router = APIRouter(prefix="/users", tags=["users"])
limiter = Limiter(key_func=get_remote_address)
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

upload_service = UploadFileService(
    settings.CLD_NAME, settings.CLD_API_KEY, settings.CLD_API_SECRET
)


@router.get("/me", response_model=User, description="No more than 10 requests per minute")
@limiter.limit("10/minute")
async def me(request: Request, user: User = Depends(get_current_user)):
    """
    Returns the details of the currently authenticated user.
    """
    logger.info(f"User details accessed: {user.username}")
    return user


@router.patch("/avatar", response_model=User)
async def update_avatar_user(
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Updates the avatar URL for the current user.
    """
    try:
        avatar_url = upload_service.upload_file(file, user.username)
        logger.info(f"Avatar uploaded for user: {user.username}, URL: {avatar_url}")

        user_service = UserService(db)
        updated_user = await user_service.update_avatar_url(user.email, avatar_url)
        logger.info(f"Avatar updated successfully for user: {user.username}")
        return updated_user

    except Exception as e:
        logger.error(f"Failed to update avatar for user {user.username}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while updating the avatar.",
        )