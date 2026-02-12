"""
router.py
=========
FastAPI router for the **Users** API.

Endpoints
---------
=======  ================  ===========================  ===============
Method   Path              Description                  Response Model
=======  ================  ===========================  ===============
POST     ``/users/``       Create a new user            ``UserRead``
GET      ``/users/``       List all users (paginated)   ``list[UserRead]``
GET      ``/users/{id}``   Retrieve a user by UUID      ``UserRead``
=======  ================  ===========================  ===============

All endpoints inject an ``AsyncSession`` via the ``get_session`` dependency
and delegate to the service layer for actual database work.
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_session
from src.users import service
from src.users.schemas import UserCreate, UserRead

router = APIRouter(
    prefix="/users",
    tags=["Users"],
)


@router.post(
    "/",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new user",
    description=(
        "Register a new user with a unique email and username. "
        "Returns the created user object including server-generated fields."
    ),
)
async def create_user(
    data: UserCreate,
    session: AsyncSession = Depends(get_session),
) -> UserRead:
    """Handle **POST /users/** – create a user."""
    user = await service.create_user(session, data)
    return UserRead.model_validate(user)


@router.get(
    "/",
    response_model=list[UserRead],
    status_code=status.HTTP_200_OK,
    summary="List all users",
    description=(
        "Return a paginated list of users ordered by their creation date. "
        "Use ``skip`` and ``limit`` query parameters for pagination."
    ),
)
async def list_users(
    skip: int = Query(default=0, ge=0, description="Rows to skip."),
    limit: int = Query(
        default=100, ge=1, le=1000, description="Max rows to return."
    ),
    session: AsyncSession = Depends(get_session),
) -> list[UserRead]:
    """Handle **GET /users/** – list users."""
    users = await service.list_users(session, skip=skip, limit=limit)
    return [UserRead.model_validate(u) for u in users]


@router.get(
    "/{user_id}",
    response_model=UserRead,
    status_code=status.HTTP_200_OK,
    summary="Get a user by ID",
    description="Retrieve a single user by their UUID. Returns 404 if not found.",
)
async def get_user(
    user_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
) -> UserRead:
    """Handle **GET /users/{user_id}** – get one user."""
    user = await service.get_user_by_id(session, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id '{user_id}' not found.",
        )
    return UserRead.model_validate(user)