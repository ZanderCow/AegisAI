"""
service.py
==========
Business-logic / data-access layer for the **Users** domain.

Every function in this module receives an ``AsyncSession`` as its first
argument.  This keeps the service layer decoupled from FastAPI's dependency
injection and makes the functions easy to call from tests, CLI scripts, or
background workers.

Functions
---------
``create_user``
    Insert a new row into the ``users`` table and return it.

``list_users``
    Return a paginated list of all users ordered by creation date.

``get_user_by_id``
    Look up a single user by their UUID primary key.
"""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.users.models import User
from src.users.schemas import UserCreate


async def create_user(session: AsyncSession, data: UserCreate) -> User:
    """Persist a new user and return the created ORM instance.

    Parameters
    ----------
    session : AsyncSession
        The database session for this request.
    data : UserCreate
        Validated request payload describing the new user.

    Returns
    -------
    User
        The newly created user **after** the row has been flushed to the
        database (so server-generated defaults like ``id`` and
        ``created_at`` are populated).
    """
    user = User(**data.model_dump())
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


async def list_users(
    session: AsyncSession,
    skip: int = 0,
    limit: int = 100,
) -> list[User]:
    """Return a paginated list of users ordered by creation date.

    Parameters
    ----------
    session : AsyncSession
        The database session for this request.
    skip : int
        Number of rows to skip (for pagination).  Defaults to ``0``.
    limit : int
        Maximum number of rows to return.  Defaults to ``100``.

    Returns
    -------
    list[User]
        A list of ``User`` ORM instances.
    """
    statement = (
        select(User)
        .order_by(User.created_at)
        .offset(skip)
        .limit(limit)
    )
    result = await session.execute(statement)
    return list(result.scalars().all())


async def get_user_by_id(
    session: AsyncSession,
    user_id: uuid.UUID,
) -> User | None:
    """Fetch a single user by primary key.

    Parameters
    ----------
    session : AsyncSession
        The database session for this request.
    user_id : uuid.UUID
        The UUID of the user to look up.

    Returns
    -------
    User | None
        The matching ``User`` instance, or ``None`` if no row was found.
    """
    return await session.get(User, user_id)
