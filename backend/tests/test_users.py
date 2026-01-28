import pytest
from src.core.db import init_db
from src.models.user_model import User
from src.core.config import settings

# Use a separate database for testing
settings.DATABASE_NAME = "aegis_ai_test_db"

@pytest.mark.asyncio
async def test_beanie_initialization():
    """Test that Beanie initializes correctly."""
    await init_db()
    # Check if the User collection works
    count = await User.count()
    assert count >= 0

@pytest.mark.asyncio
async def test_create_and_read_user():
    """Test creating and retrieving a user."""
    await init_db()
    
    # Create a user
    user = User(email="test@example.com", username="testuser", hashed_password="hashed_password")
    await user.insert()
    
    # Retrieve the user
    found_user = await User.find_one(User.email == "test@example.com")
    
    assert found_user is not None
    assert found_user.username == "testuser"
    assert found_user.is_active is True
    
    # Clean up
    await found_user.delete()
