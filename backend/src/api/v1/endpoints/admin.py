"""HTTP router for admin-only user management."""
from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.repo.user_repo import UserRepository
from src.schemas.admin_schema import AdminUserOut, AdminUserRoleUpdateRequest
from src.security.jwt import AuthenticatedUser, get_current_user_with_role
from src.service.admin_service import AdminService

router = APIRouter(prefix="/admin", tags=["admin"])


def get_admin_service(session: AsyncSession = Depends(get_db)) -> AdminService:
    """Dependency factory for admin user-management service wiring."""
    return AdminService(UserRepository(session))


@router.get("/users", response_model=list[AdminUserOut])
async def list_admin_users(
    auth: AuthenticatedUser = Depends(get_current_user_with_role),
    service: AdminService = Depends(get_admin_service),
) -> list[AdminUserOut]:
    """Return every user for the admin user table."""
    return await service.list_users(auth)


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_admin_user(
    user_id: UUID,
    auth: AuthenticatedUser = Depends(get_current_user_with_role),
    service: AdminService = Depends(get_admin_service),
) -> Response:
    """Hard delete a user record."""
    await service.delete_user(auth, user_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.patch("/users/{user_id}/role", response_model=AdminUserOut)
async def update_admin_user_role(
    user_id: UUID,
    body: AdminUserRoleUpdateRequest,
    auth: AuthenticatedUser = Depends(get_current_user_with_role),
    service: AdminService = Depends(get_admin_service),
) -> AdminUserOut:
    """Persist an inline admin-table role change."""
    return await service.update_user_role(auth, user_id, body.role)
