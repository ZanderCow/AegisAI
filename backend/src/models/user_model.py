"""SQLAlchemy ORM base models for the application's domain.

This module houses the declarative mappings between Python classes
and the backend PostgreSQL database tables.
"""
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class User(Base):
    """Database model representing a registered application user.
    
    Attributes:
        id (int): The primary key for the user.
        email (str): The unique, indexed email address used for login.
        hashed_password (str): The heavily salted, securely hashed password.
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
