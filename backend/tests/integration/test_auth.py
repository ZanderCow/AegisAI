import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from src.main import app
from src.core.database import get_db
from src.models.user_model import Base

# Setup isolated in-memory testing database
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestingSessionLocal = async_sessionmaker(
    test_engine, class_=AsyncSession, expire_on_commit=False
)

async def override_get_db():
    async with TestingSessionLocal() as session:
        yield session

# Override the application production Database connection dependency
app.dependency_overrides[get_db] = override_get_db

@pytest_asyncio.fixture(autouse=True)
async def setup_database():
    """Runs database schemas creation before each test & destroys after"""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest_asyncio.fixture
async def client():
    # Use ASGITransport logic natively inside FastAPI's core without running network
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

@pytest.mark.asyncio
async def test_successful_signup(client: AsyncClient):
    response = await client.post(
        "/api/v1/auth/signup", 
        json={"email": "newuser@example.com", "password": "supersecurepassword"}
    )
    assert response.status_code == 201
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

@pytest.mark.asyncio
async def test_duplicate_email_signup(client: AsyncClient):
    payload = {"email": "duplicate@example.com", "password": "password123"}
    # First sign up
    await client.post("/api/v1/auth/signup", json=payload)
    # Attempt duplicate
    response = await client.post("/api/v1/auth/signup", json=payload)
    assert response.status_code == 400
    assert response.json()["detail"] == "Email already registered"

@pytest.mark.asyncio
async def test_successful_login(client: AsyncClient):
    payload = {"email": "login@example.com", "password": "password123"}
    await client.post("/api/v1/auth/signup", json=payload)
    
    response = await client.post("/api/v1/auth/login", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

@pytest.mark.asyncio
async def test_wrong_password_login(client: AsyncClient):
    await client.post(
        "/api/v1/auth/signup", 
        json={"email": "wrongpwd@example.com", "password": "password123"}
    )
    
    response = await client.post(
        "/api/v1/auth/login", 
        json={"email": "wrongpwd@example.com", "password": "wrongpassword"}
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid credentials"

@pytest.mark.asyncio
async def test_unknown_email_login(client: AsyncClient):
    response = await client.post(
        "/api/v1/auth/login", 
        json={"email": "unknown@example.com", "password": "password123"}
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid credentials"
