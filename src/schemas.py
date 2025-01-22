from datetime import datetime, date
from typing import  Optional
from pydantic import BaseModel, Field, ConfigDict, EmailStr

class AddressBase(BaseModel):
    country: str = Field(min_length=2, max_length=50)
    index: int = Field(gt=0)
    city: str = Field(min_length=2, max_length=50)
    street: str = Field(min_length=2, max_length=50)
    house: str = Field(min_length=1, max_length=4)
    apartment: Optional[str] = Field(max_length=4)

class AddressCreate(AddressBase):
    pass

class AddressUpdate(AddressBase):
    pass

class AddressResponse(AddressBase):
    id: int

    model_config = ConfigDict(from_attributes=True)

class ContactBase(BaseModel):
    name: str = Field(min_length=2, max_length=150)
    surname: str = Field(min_length=2, max_length=150)
    email: str = Field(min_length=5, max_length=150)
    phone_number: str = Field(min_length=3, max_length=20)
    birthday: date = Field(default=None)


class ContactCreate(ContactBase):
    address: Optional[AddressCreate]


class ContactUpdate(ContactBase):
    address: Optional[AddressUpdate]


class ContactResponse(ContactBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime]
    address: Optional[AddressResponse] = None

    model_config = ConfigDict(from_attributes=True)


class User(BaseModel):
    id: int
    username: str
    email: str
    avatar: str

    model_config = ConfigDict(from_attributes=True)


class UserCreate(BaseModel):
    username: str
    email: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str

class RequestEmail(BaseModel):
    email: EmailStr