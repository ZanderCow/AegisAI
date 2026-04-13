"""Service layer for admin-managed user operations."""
from __future__ import annotations

import uuid

from fastapi import HTTPException, status

from src.core.logger import get_logger
from src.repo.user_repo import UserRepository
from src.schemas.admin_schema import AdminUserOut
from src.security.jwt import AuthenticatedUser

logger = get_logger("ADMIN_SERVICE")


class AdminService:
    """Business logic for admin-only user management."""

    def __init__(self, repo: UserRepository) -> None:
        self.repo = repo

    @staticmethod
    def _require_admin(auth: AuthenticatedUser) -> None:
        if auth.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin role required",
            )

    async def list_users(self, auth: AuthenticatedUser) -> list[AdminUserOut]:
        """Return all persisted users for the admin dashboard."""
        self._require_admin(auth)
        users = await self.repo.list_all()
        return [self._to_out(user) for user in users]

    async def delete_user(self, auth: AuthenticatedUser, user_id: str | uuid.UUID) -> None:
        """Hard delete a user from the database."""
        self._require_admin(auth)
        deleted = await self.repo.delete_user(user_id)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )
        logger.info("Admin %s deleted user %s", auth.user_id, user_id)

    async def update_user_role(
        self,
        auth: AuthenticatedUser,
        user_id: str | uuid.UUID,
        role: str,
    ) -> AdminUserOut:
        """Update a persisted user's role."""
        self._require_admin(auth)
        updated_user = await self.repo.update_role(user_id, role)
        if updated_user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )
        logger.info(
            "Admin %s updated user %s role to %s",
            auth.user_id,
            user_id,
            role,
        )
        return self._to_out(updated_user)

    @staticmethod
    def _to_out(user) -> AdminUserOut:
        return AdminUserOut(
            id=str(user.id),
            full_name=user.full_name,
            email=user.email,
            role=user.role,
            created_at=user.created_at,
            last_login=user.last_login,
        )
