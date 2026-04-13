"""Service helpers for idempotent higher-tier user seeding."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from sqlalchemy.ext.asyncio import AsyncSession

from src.core.logger import get_logger
from src.repo.user_repo import UserRepository
from src.security.password import hash_password

logger = get_logger("SEED_SERVICE")

SeedStatus = Literal["created", "skipped"]


@dataclass(frozen=True)
class SeedUserRequest:
    """Resolved seed-user input ready for persistence."""

    email: str
    password: str
    role: str
    label: str


@dataclass(frozen=True)
class SeedUserResult:
    """Outcome for a single privileged-user seed attempt."""

    email: str
    role: str
    status: SeedStatus


class SeedService:
    """Business logic for privileged-user seeding."""

    def __init__(self, session: AsyncSession) -> None:
        self.repo = UserRepository(session)

    async def seed_users(
        self,
        requests: list[SeedUserRequest],
    ) -> list[SeedUserResult]:
        """Create missing privileged users without mutating existing ones."""
        results: list[SeedUserResult] = []

        for request in requests:
            existing_user = await self.repo.get_by_email(request.email)
            if existing_user is not None:
                logger.info(
                    "Skipped seeded %s user because it already exists: %s",
                    request.label,
                    request.email,
                )
                results.append(
                    SeedUserResult(
                        email=request.email,
                        role=request.role,
                        status="skipped",
                    )
                )
                continue

            hashed_password = hash_password(request.password)
            created_user = await self.repo.create_user(
                request.email,
                hashed_password,
                role=request.role,
            )
            logger.info(
                "Created seeded %s user: %s",
                request.label,
                created_user.email,
            )
            results.append(
                SeedUserResult(
                    email=created_user.email,
                    role=created_user.role,
                    status="created",
                )
            )

        return results
