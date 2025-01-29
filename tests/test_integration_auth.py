from unittest.mock import Mock, AsyncMock
import pytest
from sqlalchemy import select

from src.database.models import User
from src.services.auth import create_email_token
from tests.conftest import TestingSessionLocal


user_data = {
    "username": "agent007",
    "email": "agent007@gmail.com",
    "password": "12345678",
    "role": "USER",
}


def test_register(client, monkeypatch):
    mock_send_email = Mock()
    monkeypatch.setattr("src.api.auth.send_email", mock_send_email)
    response = client.post("api/auth/register", json=user_data)
    assert response.status_code == 201, response.text
    data = response.json()
    assert data["username"] == user_data["username"]
    assert data["email"] == user_data["email"]
    assert "hashed_password" not in data
    assert "avatar" in data
    assert data["role"] == user_data["role"]


def test_repeat_signup(client, monkeypatch):
    mock_send_email = Mock()
    monkeypatch.setattr("src.api.auth.send_email", mock_send_email)
    user_data_new = user_data.copy()
    user_data_new["username"] = "new_user"
    response = client.post("api/auth/register", json=user_data)
    assert response.status_code == 409, response.text
    data = response.json()
    assert data["detail"] == "A user with this email already exists."


def test_signup_failed(client, monkeypatch):
    mock_send_email = Mock()
    monkeypatch.setattr("src.api.auth.send_email", mock_send_email)
    response = client.post("api/auth/register", json=user_data)
    assert response.status_code == 409, response.text
    data = response.json()
    assert data["detail"] == "A user with this email already exists."


def test_not_confirmed_login(client):
    response = client.post(
        "api/auth/login",
        data={
            "username": user_data.get("username"),
            "password": user_data.get("password"),
        },
    )
    assert response.status_code == 401, response.text
    data = response.json()
    assert data["detail"] == "Email not confirmed. Please confirm your email first."


def test_request_email(client, monkeypatch):
    mock_send_email = Mock()
    monkeypatch.setattr("src.api.auth.send_email", mock_send_email)
    response = client.post("api/auth/request-email", json={"email": user_data["email"]})
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["message"] == "Check your email for confirmation link."


@pytest.mark.asyncio
async def test_login(client):
    async with TestingSessionLocal() as session:
        current_user = await session.execute(
            select(User).where(User.email == user_data.get("email"))
        )
        current_user = current_user.scalar_one_or_none()
        if current_user:
            current_user.confirmed = True
            await session.commit()

    response = client.post(
        "api/auth/login",
        data={
            "username": user_data.get("username"),
            "password": user_data.get("password"),
        },
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert "token_type" in data


def test_wrong_password_login(client):
    response = client.post(
        "api/auth/login",
        data={"username": user_data.get("username"), "password": "password"},
    )
    assert response.status_code == 401, response.text
    data = response.json()
    assert data["detail"] == "Invalid username or password."


def test_wrong_username_login(client):
    response = client.post(
        "api/auth/login",
        data={"username": "username", "password": user_data.get("password")},
    )
    assert response.status_code == 401, response.text
    data = response.json()
    assert data["detail"] == "Invalid username or password."


def test_validation_error_login(client):
    response = client.post(
        "api/auth/login", data={"password": user_data.get("password")}
    )
    assert response.status_code == 422, response.text
    data = response.json()
    assert "detail" in data


def test_refresh_token(client, get_refresh_token):
    response = client.post(
        "api/auth/refresh-token",
        json={"refresh_token": get_refresh_token},
        headers={"Authorization": f"Bearer {get_refresh_token}"},
    )
    assert response.status_code == 401, response.text
    data = response.json()
    assert data["detail"] == "Could not validate credentials"


def test_invalid_refresh_token(client):
    response = client.post(
        "api/auth/refresh-token",
        json={"refresh_token": "invalid_token"},
    )
    assert response.status_code == 401, response.text
    data = response.json()
    assert data["detail"] == "Could not validate credentials"


def test_confirm_email_failed(client, get_email_token):
    response = client.get(f"api/auth/confirm-email/{get_email_token}")
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["message"] == "Email already confirmed"


def test_already_confirmed_email(client, get_email_token):
    response = client.get(f"api/auth/confirm-email/{get_email_token}")
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["message"] == "Email already confirmed"


def test_confirm_email_wrong_token(client, get_email_token):
    response = client.get(f"api/auth/confirm-email/eriqur2341341")
    assert response.status_code == 422, response.text
    data = response.json()
    assert data["detail"] == "Invalid token for email verification"


@pytest.mark.asyncio
async def test_request_email_confirmed(client):
    async with TestingSessionLocal() as session:
        # Retrieve the user and set confirmed to False
        user = await session.execute(
            select(User).where(User.email == "agent007@gmail.com")
        )
        user = user.scalar_one_or_none()
        if user:
            user.confirmed = False
            await session.commit()

    # Perform the request
    response = client.post("api/auth/request-email", json={"email": "agent007@gmail.com"})
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["message"] == "Check your email for confirmation link."


def test_request_email_failed(client, monkeypatch):
    mock_send_email = Mock()
    monkeypatch.setattr("src.api.auth.send_email", mock_send_email)
    response = client.post(
        "api/auth/request-email", json={"email": "unexisting@test.com"}
    )
    assert response.status_code == 404, response.text
    data = response.json()
    assert data["detail"] == "User with this email does not exist."


def test_logging_on_failed_login(client, caplog):
    response = client.post(
        "api/auth/login",
        data={"username": user_data["username"], "password": "wrong_password"},
    )
    assert response.status_code == 401, response.text
    assert "Failed login attempt" in caplog.text


def test_request_password_reset(client, monkeypatch):
    """
    Test the request-password-reset endpoint to ensure that it correctly sends a reset email.
    """
    mock_send_reset_password_email = Mock()
    monkeypatch.setattr(
        "src.api.auth.send_reset_password_email", mock_send_reset_password_email
    )

    response = client.post(
        "api/auth/request-password-reset", json={"email": user_data["email"]}
    )

    assert response.status_code == 200, response.text
    data = response.json()
    assert data["message"] == "Password reset email has been sent."
    mock_send_reset_password_email.assert_called_once()


def test_request_password_reset_user_not_found(client):
    """
    Test the request-password-reset endpoint for a non-existent user.
    """
    response = client.post(
        "api/auth/request-password-reset", json={"email": "nonexistent@example.com"}
    )

    assert response.status_code == 404, response.text
    data = response.json()
    assert data["detail"] == "User with this email does not exist."


@pytest.mark.asyncio
async def test_reset_password_success(client, monkeypatch):
    """
    Test the reset-password endpoint for successful password reset.
    """
    mock_send_new_password_email = Mock()
    monkeypatch.setattr(
        "src.api.auth.send_new_password_email", mock_send_new_password_email
    )

    # Generate a valid token
    async with TestingSessionLocal() as session:
        current_user = await session.execute(
            select(User).where(User.email == user_data.get("email"))
        )
        current_user = current_user.scalar_one_or_none()
        if current_user:
            token = create_email_token(data={"sub": current_user.email})

    response = client.get(f"api/auth/reset-password?token={token}")
    assert response.status_code == 200, response.text

    data = response.json()
    assert data["message"] == "Token is valid. Proceed with password reset."
    mock_send_new_password_email.assert_called_once()


@pytest.mark.asyncio
async def test_reset_password_invalid_token(client):
    """
    Test the reset-password endpoint with an invalid token.
    """
    response = client.get("api/auth/reset-password?token=invalid_token")
    assert response.status_code == 400, response.text
    data = response.json()
    assert data["detail"] == "Invalid or expired token."


@pytest.mark.asyncio
async def test_reset_password_user_not_found(client, monkeypatch):
    """
    Test the reset-password endpoint when the user associated with the token does not exist.
    """
    mock_get_email_from_token = AsyncMock(return_value="unknown@example.com")
    monkeypatch.setattr("src.api.auth.get_email_from_token", mock_get_email_from_token)

    response = client.get("api/auth/reset-password?token=some_valid_token")
    assert response.status_code == 404, response.text
    data = response.json()
    assert data["detail"] == "User not found."