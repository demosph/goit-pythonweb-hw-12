import pytest
from datetime import date, timedelta
from unittest.mock import AsyncMock, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import Contact, User
from src.repository.contacts import ContactRepository
from src.schemas import ContactCreate, ContactUpdate

contact_data = {
    "name": "John",
    "surname": "Doe",
    "email": "john.doe@example.com",
    "phone_number": "+380-66-112-2333",
    "birthday": "2000-01-01",
    "address": None,
}

updated_contact_data = {
    "name": "Jane",
    "surname": "Doe",
    "email": "jane.doe@example.com",
    "phone_number": "+380-66-112-2333",
    "birthday": str(date.today() + timedelta(days=5)),
    "address": None,
}


def test_create_contact(client, get_access_token):
    response = client.post(
        "/api/contacts",
        json=contact_data,
        headers={"Authorization": f"Bearer {get_access_token}"},
    )
    assert response.status_code == 201, response.text
    data = response.json()
    assert data["name"] == "John"
    assert data["surname"] == "Doe"
    assert data["email"] == "john.doe@example.com"
    assert "id" in data


def test_get_contact_by_id(client, get_access_token):
    response = client.get(
        "/api/contacts/1", headers={"Authorization": f"Bearer {get_access_token}"}
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["name"] == "John"
    assert "id" in data


def test_get_contact_not_found(client, get_access_token):
    response = client.get(
        "/api/contacts/2", headers={"Authorization": f"Bearer {get_access_token}"}
    )
    assert response.status_code == 404, response.text
    data = response.json()
    assert data["detail"] == "Contact with ID 2 not found"


def test_get_contacts(client, get_access_token):
    response = client.get(
        "/api/contacts", headers={"Authorization": f"Bearer {get_access_token}"}
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert isinstance(data, list)
    assert data[0]["name"] == "John"
    assert "id" in data[0]


def test_update_contact(client, get_access_token):
    response = client.put(
        "/api/contacts/1",
        json=updated_contact_data,
        headers={"Authorization": f"Bearer {get_access_token}"},
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["name"] != "John"
    assert data["name"] == "Jane"
    assert data["email"] == "jane.doe@example.com"
    assert "id" in data


def test_update_contact_unprodessable(client, get_access_token):
    response = client.put(
        "/api/contacts/1",
        json={"name": "Michael"},
        headers={"Authorization": f"Bearer {get_access_token}"},
    )
    assert response.status_code == 422, response.text


def test_update_contact_not_found(client, get_access_token):
    response = client.put(
        "/api/contacts/2",
        json=updated_contact_data,
        headers={"Authorization": f"Bearer {get_access_token}"},
    )
    assert response.status_code == 404, response.text
    data = response.json()
    assert data["detail"] == "Contact with ID 2 not found"


def test_read_bistdays(client, get_access_token):
    response = client.get(
        "/api/contacts/birthdays/upcoming",
        headers={"Authorization": f"Bearer {get_access_token}"},
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert data[0]["name"] == "Jane"
    assert data[0]["surname"] == "Doe"
    assert data[0]["email"] == "jane.doe@example.com"
    assert data[0]["phone_number"] == "+380-66-112-2333"
    assert data[0]["birthday"] == str(date.today() + timedelta(days=5))
    assert data[0]["address"] is None


def test_delete_contact(client, get_access_token):
    response = client.delete(
        "/api/contacts/1", headers={"Authorization": f"Bearer {get_access_token}"}
    )
    assert response.status_code == 204, response.text


def test_delete_contact_not_found(client, get_access_token):
    response = client.delete(
        "/api/contacts/1", headers={"Authorization": f"Bearer {get_access_token}"}
    )
    assert response.status_code == 404, response.text
    data = response.json()
    assert data["detail"] == "Contact with ID 1 not found"


def test_read_bistdays_empty(client, get_access_token):
    response = client.get(
        "/api/contacts/birthdays/upcoming",
        headers={"Authorization": f"Bearer {get_access_token}"},
        params={"daygap": 1},
    )
    print(response.url)
    assert response.status_code == 200, response.text
    data = response.json()
    assert data == []