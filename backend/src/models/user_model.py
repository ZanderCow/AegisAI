"""SQLAlchemy ORM base models for the application's domain.

This module houses the declarative mappings between Python classes
and the backend PostgreSQL database tables.
"""
import uuid
from sqlalchemy import Column, String, Uuid
from sqlalchemy.orm import declarative_base

ROLE_USER = "user"
ROLE_SECURITY = "security"
ROLE_ADMIN = "admin"
PRIVILEGED_ROLES = {ROLE_SECURITY, ROLE_ADMIN}

Base = declarative_base()

class User(Base):
    """Database model representing a registered application user.

    Attributes:
        id (uuid.UUID): The primary UUID key for the user.
        email (str): The unique, indexed email address used for login.
        hashed_password (str): The heavily salted, securely hashed password.
        role (str): The user's role (user, admin, security).
    """
    __tablename__ = "users"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(String(20), nullable=False, default=ROLE_USER)
