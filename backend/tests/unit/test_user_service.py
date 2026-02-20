"""
Unit Tests — UserService
All dependencies (repository, security) are fully mocked.
SQLAlchemy is never imported — no database needed.
Run with: pytest tests/unit/test_user_service.py -v
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_repo():
    """Fake repository — no database, no SQLAlchemy."""
    repo = MagicMock()
    repo.get_user_by_email = AsyncMock(return_value=None)
    repo.get_user_by_id = AsyncMock(return_value=None)
    repo.create_user = AsyncMock()
    return repo


@pytest.fixture
def mock_user():
    """Fake User object."""
    user = MagicMock()
    user.id = 1
    user.email = "test@example.com"
    user.hashed_password = "hashed_secret"
    return user


@pytest.fixture
def service(mock_repo):
    """UserService with mocked repo — import happens here so patches apply first."""
    from service.user_service import UserService
    return UserService(mock_repo)


# ---------------------------------------------------------------------------
# register_user
# ---------------------------------------------------------------------------

class TestRegisterUser:
    @pytest.mark.asyncio
    async def test_register_success(self, service, mock_repo, mock_user):
        mock_repo.get_user_by_email.return_value = None
        mock_repo.create_user.return_value = mock_user

        with patch("service.user_service.hash_password", return_value="hashed_secret"), \
             patch("service.user_service.create_access_token", return_value="jwt.token"):
            user, token = await service.register_user("test@example.com", "password123")

        mock_repo.create_user.assert_awaited_once_with(
            email="test@example.com", hashed_password="hashed_secret"
        )
        assert user == mock_user
        assert token == "jwt.token"

    @pytest.mark.asyncio
    async def test_register_duplicate_email(self, service, mock_repo, mock_user):
        from fastapi import HTTPException
        mock_repo.get_user_by_email.return_value = mock_user

        with pytest.raises(HTTPException) as exc:
            await service.register_user("test@example.com", "password123")

        assert exc.value.status_code == 400
        mock_repo.create_user.assert_not_awaited()


# ---------------------------------------------------------------------------
# login_user
# ---------------------------------------------------------------------------

class TestLoginUser:
    @pytest.mark.asyncio
    async def test_login_success(self, service, mock_repo, mock_user):
        mock_repo.get_user_by_email.return_value = mock_user

        with patch("service.user_service.verify_password", return_value=True), \
             patch("service.user_service.create_access_token", return_value="jwt.token"):
            token = await service.login_user("test@example.com", "password123")

        assert token == "jwt.token"

    @pytest.mark.asyncio
    async def test_login_user_not_found(self, service, mock_repo):
        from fastapi import HTTPException
        mock_repo.get_user_by_email.return_value = None

        with pytest.raises(HTTPException) as exc:
            await service.login_user("ghost@example.com", "password123")

        assert exc.value.status_code == 401

    @pytest.mark.asyncio
    async def test_login_wrong_password(self, service, mock_repo, mock_user):
        from fastapi import HTTPException
        mock_repo.get_user_by_email.return_value = mock_user

        with patch("service.user_service.verify_password", return_value=False):
            with pytest.raises(HTTPException) as exc:
                await service.login_user("test@example.com", "wrongpass")

        assert exc.value.status_code == 401


# ---------------------------------------------------------------------------
# get_current_user
# ---------------------------------------------------------------------------

class TestGetCurrentUser:
    @pytest.mark.asyncio
    async def test_get_current_user_success(self, service, mock_repo, mock_user):
        mock_repo.get_user_by_id.return_value = mock_user

        import uuid
        fake_uuid = uuid.UUID("00000000-0000-0000-0000-000000000001")
        with patch("service.user_service.decode_access_token", return_value={"sub": str(fake_uuid)}):
            result = await service.get_current_user("valid.token")

        mock_repo.get_user_by_id.assert_awaited_once_with(fake_uuid)
        assert result == mock_user

    @pytest.mark.asyncio
    async def test_get_current_user_invalid_token(self, service):
        from fastapi import HTTPException
        with patch("service.user_service.decode_access_token", return_value={}):
            with pytest.raises(HTTPException) as exc:
                await service.get_current_user("bad.token")

        assert exc.value.status_code == 401

    @pytest.mark.asyncio
    async def test_get_current_user_not_found(self, service, mock_repo):
        from fastapi import HTTPException
        mock_repo.get_user_by_id.return_value = None

        with patch("service.user_service.decode_access_token", return_value={"sub": "00000000-0000-0000-0000-000000000099"}):
            with pytest.raises(HTTPException) as exc:
                await service.get_current_user("valid.token")

        assert exc.value.status_code == 404