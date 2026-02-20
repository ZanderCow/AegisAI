from pydantic import BaseModel, EmailStr, Field


# ---------------------------------------------------------------------------
# Request Schemas
# ---------------------------------------------------------------------------

class UserRegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, description="Minimum 8 characters")

    model_config = {"json_schema_extra": {"example": {"email": "user@example.com", "password": "securepass123"}}}


class UserLoginRequest(BaseModel):
    email: EmailStr
    password: str

    model_config = {"json_schema_extra": {"example": {"email": "user@example.com", "password": "securepass123"}}}


# ---------------------------------------------------------------------------
# Response Schemas
# ---------------------------------------------------------------------------

class UserResponse(BaseModel):
    id: int
    email: str

    model_config = {"from_attributes": True}  # Allows ORM model -> schema conversion


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"