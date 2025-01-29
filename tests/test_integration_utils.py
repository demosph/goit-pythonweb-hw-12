from unittest.mock import AsyncMock, patch
import pytest


@pytest.mark.asyncio
async def test_healthchecker_success(client):
    mock_db = AsyncMock()
    mock_db.execute.return_value.scalar_one_or_none.return_value = 1
    with patch("src.api.utils.get_db", return_value=mock_db):
        response = client.get("api/healthchecker")
        assert response.status_code == 200
        data = response.json()
        assert data == {"message": "Welcome to FastAPI!"}


@pytest.mark.asyncio
async def test_healthchecker_db_not_configured(client):
    mock_db = AsyncMock()
    mock_db.execute.return_value.scalar_one_or_none.return_value = None
    with patch("src.api.utils.get_db", return_value=mock_db):
        with pytest.raises(Exception):
            await client()


@pytest.mark.asyncio
async def test_healthchecker_db_connection_error(client):
    mock_db = AsyncMock()
    mock_db.execute.side_effect = Exception("Error connecting to the database")
    with patch("src.api.utils.get_db", return_value=mock_db):
        with pytest.raises(Exception):
            await client()