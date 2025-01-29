import pytest
from unittest.mock import AsyncMock, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession
from src.repository.users import UserRepository
from src.schemas import User, UserCreate, UserRole


@pytest.fixture
def mock_session():
    return AsyncMock(spec=AsyncSession)


@pytest.fixture
def mock_user_repository(mock_session):
    return UserRepository(mock_session)


@pytest.fixture
def user():
    return User(
        id=1,
        username="testuser",
        email="test@email.com",
        avatar="avatar",
        role=UserRole.USER,
    )


@pytest.mark.asyncio
async def test_get_user_by_id(mock_user_repository, mock_session, user):
    # Setup mock
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = user
    mock_session.execute = AsyncMock(return_value=mock_result)

    # Call method
    result = await mock_user_repository.get_user_by_id(user_id=1)

    # Assertions
    assert result is not None
    assert result.id == 1
    assert result.username == "testuser"
    assert result.email == "test@email.com"
    assert result.avatar == "avatar"


@pytest.mark.asyncio
async def test_get_user_by_username(mock_user_repository, mock_session, user):
    # Setup mock
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = user
    mock_session.execute = AsyncMock(return_value=mock_result)

    # Call method
    result = await mock_user_repository.get_user_by_username(username="testuser", refresh_token=None)

    # Assertions
    assert result is not None
    assert result.id == 1
    assert result.username == "testuser"
    assert result.email == "test@email.com"
    assert result.avatar == "avatar"


@pytest.mark.asyncio
async def test_get_user_by_email(mock_user_repository, mock_session, user):
    # Setup mock
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = user
    mock_session.execute = AsyncMock(return_value=mock_result)

    # Call method
    result = await mock_user_repository.get_user_by_email(email="test@email.com")

    # Assertions
    assert result is not None
    assert result.id == 1
    assert result.username == "testuser"
    assert result.email == "test@email.com"
    assert result.avatar == "avatar"


@pytest.mark.asyncio
async def test_create_user(mock_user_repository, mock_session):
    user_data = UserCreate(
        username="test",
        email="test@example.com",
        password="password",
        role=UserRole.USER
    )

    user = await mock_user_repository.create_user(user_data, avatar="avatar_url")

    assert user.email == "test@example.com"
    assert user.username == "test"
    assert user.avatar == "avatar_url"

    mock_session.add.assert_called_once()
    mock_session.commit.assert_awaited_once()
    mock_session.refresh.assert_awaited_once_with(user)


@pytest.mark.asyncio
async def test_update_avatar_url(mock_user_repository, mock_session, user):
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = user
    mock_session.execute = AsyncMock(return_value=mock_result)

    user = await mock_user_repository.update_avatar_url(
        email="test@example.com", url="new_avatar_url"
    )

    assert user.avatar == "new_avatar_url"


@pytest.mark.asyncio
async def test_update_avatar_url_with_no_user(mock_user_repository, mock_session):
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute = AsyncMock(return_value=mock_result)

    with pytest.raises(ValueError):
        await mock_user_repository.update_avatar_url(
            email="test@example.com", url="new_avatar_url"
        )