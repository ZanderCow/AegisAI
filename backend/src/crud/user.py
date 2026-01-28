from typing import Optional
from src.models.user_model import User
from src.schemas.users import UserCreate
from src.core.security import get_password_hash, verify_password

class CRUDUser:
    async def get_by_email(self, email: str) -> Optional[User]:
        return await User.find_one(User.email == email)

    async def get_by_username(self, username: str) -> Optional[User]:
        return await User.find_one(User.username == username)

    async def create(self, obj_in: UserCreate) -> User:
        user = User(
            email=obj_in.email,
            username=obj_in.username,
            hashed_password=get_password_hash(obj_in.password),
        )
        await user.insert()
        return user

    async def authenticate(self, email: str, password: str) -> Optional[User]:
        user = await self.get_by_email(email)
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user

user_crud = CRUDUser()
