from beanie import Document
from pydantic import EmailStr
from datetime import datetime
from typing import Optional

class User(Document):
    email: EmailStr
    username: str
    hashed_password: str
    created_at: datetime = datetime.now()
    is_active: bool = True

    class Settings:
        name = "users"
