from beanie import init_beanie
from pymongo import AsyncMongoClient
from src.core.config import settings

# Import all models here to register them with Beanie
# We will add the User model here once created
from src.models.user_model import User

async def init_db():
    """
    Initialize the database connection and Beanie ODM.
    """
    # Create the native AsyncMongoClient
    client = AsyncMongoClient(settings.MONGODB_URL)
    
    # Access the specific database
    database = client[settings.DATABASE_NAME]
    
    # Initialize Beanie with the database and models
    await init_beanie(database=database, document_models=[User])
