from pathlib import Path

from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from fastapi_mail.errors import ConnectionErrors
from pydantic import EmailStr

from src.services.auth import create_email_token
from src.conf.config import settings

conf = ConnectionConfig(
    MAIL_USERNAME=settings.MAIL_USERNAME,
    MAIL_PASSWORD=settings.MAIL_PASSWORD,
    MAIL_FROM=settings.MAIL_FROM,
    MAIL_PORT=settings.MAIL_PORT,
    MAIL_SERVER=settings.MAIL_SERVER,
    MAIL_FROM_NAME=settings.MAIL_FROM_NAME,
    MAIL_STARTTLS=settings.MAIL_STARTTLS,
    MAIL_SSL_TLS=settings.MAIL_SSL_TLS,
    USE_CREDENTIALS=settings.USE_CREDENTIALS,
    VALIDATE_CERTS=settings.VALIDATE_CERTS,
    TEMPLATE_FOLDER=Path(__file__).parent / "templates",
)

async def send_email(email: EmailStr, username: str, host: str):
    """
    Sends an email to a user with a link to verify their email address.

    Args:
        email (EmailStr): The email address of the user.
        username (str): The username of the user.
        host (str): The host of the API.

    Raises:
        ConnectionErrors: If there is an error connecting to the email server.
    """
    try:
        token_verification = create_email_token(data={"sub": email})
        message = MessageSchema(
            subject="Confirm your email",
            recipients=[email],
            template_body={
                "host": host,
                "username": username,
                "token": token_verification,
            },
            subtype=MessageType.html,
        )

        fm = FastMail(conf)
        await fm.send_message(message, template_name="verify_email.html")
    except ConnectionErrors as e:
        print(e)

async def send_reset_password_email(email: EmailStr, username: str, host: str, token: str):
    """
    Sends an email to a user with a link to reset their password.

    Args:
        email (EmailStr): The email address of the user.
        username (str): The username of the user.
        host (str): The host of the API.
        token (str): The token to be used for password reset.

    Raises:
        ConnectionErrors: If there is an error connecting to the email server.
    """
    try:
        message = MessageSchema(
            subject="Reset your credentials",
            recipients=[email],
            template_body={
                "host": host,
                "username": username,
                "token": token,
            },
            subtype=MessageType.html,
        )

        fm = FastMail(conf)
        await fm.send_message(message, template_name="reset_password.html")
    except ConnectionErrors as e:
        print(e)

async def send_new_password_email(email: EmailStr, username: str, new_password: str):
    """Sends an email to a user with their new password.

    Args:
        email (EmailStr): The email address of the user.
        username (str): The username of the user.
        new_password (str): The new password of the user.

    Raises:
        ConnectionErrors: If there is an error connecting to the email server.
    """
    try:
        message = MessageSchema(
            subject="Your New Credentials",
            recipients=[email],
            template_body={
                "username": username,
                "new_password": new_password,
            },
            subtype=MessageType.html,
        )

        fm = FastMail(conf)
        await fm.send_message(message, template_name="new_password.html")

    except ConnectionErrors as e:
        print(e)