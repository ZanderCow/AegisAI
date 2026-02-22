"""
api/deps.py
===========

Purpose:
Provides dependency injection components for FastAPI route handlers.

Responsibilities:
- Instantiates service layer components (e.g., UserService) with their required database repositories.
- Plugs into FastAPI's `Depends` system to supply request-scoped dependencies.

Dependencies:
- fastapi.Depends
- sqlalchemy.ext.asyncio.AsyncSession
- core.db.get_db
- repo.user_repository.UserRepository
- service.user_service.UserService

Who/What Should Use It:
- Route handlers in `api/v1/endpoints/` use these dependencies to access service-layer logic.

Agent Usage Note:
When an agent creates a new route that requires a service, it should first check or add a dependency provider here. Call `get_user_service` as a FastAPI dependency, not as a direct function call.
"""
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core.db import get_db
from repo.user_repository import UserRepository
from service.user_service import UserService


def get_user_service(db: AsyncSession = Depends(get_db)) -> UserService:
    """
    Dependency inject the UserService.

    Parameters:
    - `db` (AsyncSession): The asynchronous SQLAlchemy database session, automatically injected by FastAPI.

    Returns:
    - `UserService`: An instantiated user service configured with a user repository.

    Raises:
    - None directly. Underlying `get_db` may raise database connection errors.

    Usage Example:
    ```python
    @router.post("/login")
    async def login(service: UserService = Depends(get_user_service)):
        return await service.login_user(...)
    ```
    """
    return UserService(UserRepository(db))
