import enum
from datetime import datetime, date
from typing import Optional

from sqlalchemy import Column, Enum as SqlEnum, Integer, String, Boolean, func
from sqlalchemy.orm import mapped_column, Mapped, DeclarativeBase, relationship
from sqlalchemy.sql.schema import ForeignKey
from sqlalchemy.sql.sqltypes import DateTime, Date


class Base(DeclarativeBase):
    pass


class UserRole(enum.Enum):
    USER = "USER"
    ADMIN = "ADMIN"


class Contact(Base):
    __tablename__ = "contact"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    surname: Mapped[str] = mapped_column(String(150), nullable=False)
    email: Mapped[str] = mapped_column(String(150), nullable=False, unique=True, index=True)
    phone_number: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    birthday: Mapped[date] = mapped_column(Date, nullable=False)
    address_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("address.id", ondelete="CASCADE"))
    address: Mapped[Optional["Address"]] = relationship(
        "Address", back_populates="contacts", lazy="joined", single_parent=True
    )
    user_id = mapped_column(
        "user_id", ForeignKey("users.id", ondelete="CASCADE"), default=None
    )
    user = relationship("User", backref="contacts")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())

    def __repr__(self):
        """Return a string representation of the Contact object.

        The representation includes the ID, name and email of the contact.

        Returns:
            str: A string representation of the Contact object.
        """
        return f"<Contact(id={self.id}, name={self.name}, email={self.email})>"


class Address(Base):
    __tablename__ = "address"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    country: Mapped[str] = mapped_column(String(50), nullable=False)
    index: Mapped[int] = mapped_column(Integer, nullable=False)
    city: Mapped[str] = mapped_column(String(50), nullable=False)
    street: Mapped[str] = mapped_column(String(50), nullable=False)
    house: Mapped[str] = mapped_column(String(4), nullable=False)
    apartment: Mapped[str] = mapped_column(String(4))
    contacts: Mapped["Contact"] = relationship(
        "Contact", back_populates="address", cascade="all, delete-orphan", uselist=False
    )

    def __repr__(self):
        """
        Return a string representation of the Address object.

        The representation includes the ID, city, and street of the address.

        Returns:
            str: A string representation of the Address object.
        """
        return f"<Address(id={self.id}, city={self.city}, street={self.street})>"


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String, unique=True)
    email: Mapped[str] = mapped_column(String, unique=True)
    hashed_password: Mapped[str] = mapped_column(String)
    refresh_token: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    avatar: Mapped[str] = mapped_column(String(255), nullable=True)
    confirmed: Mapped[bool] = mapped_column(
        "confirmed", Boolean, default=False, nullable=True
    )
    role = Column(SqlEnum(UserRole, name="user_role"), default=UserRole.USER, nullable=False)