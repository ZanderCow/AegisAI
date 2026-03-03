---
name: Documentation Standards
description: Apply comprehensive Python and FastAPI documentation standards across the codebase
---

# Python and FastAPI Documentation Standards

This skill defines the strict documentation standards required for all Python backend code, particularly focusing on FastAPI projects. When tasked with documenting code or writing new backend features, you must adhere to the following rules to ensure the codebase remains maintainable, readable, and seamlessly integrates with auto-generated OpenAPI schemas.

## 1. Docstring Format (Google Style)

All modules, classes, methods, and functions must be documented using **Google Style Docstrings**. 
- Always use triple-double quotes (`"""`) for docstrings.
- The docstring should immediately follow the definition line.
- For multi-line docstrings, start with a one-line summary, followed by a blank line, and then a more detailed description.

### Class Documentation Example
```python
class UserRepository:
    """Repository for managing User database operations.
    
    This class handles all Create, Read, Update, and Delete (CRUD) 
    operations related to the User model in the database.
    
    Attributes:
        session (AsyncSession): The SQLAlchemy asynchronous database session.
    """
```

### Function/Method Documentation Example
```python
async def get_by_email(self, email: str) -> User | None:
    """Retrieves a single user by their email address.
    
    Args:
        email (str): The email address of the user to look up.
        
    Returns:
        User | None: The User database model if found, otherwise None.
        
    Raises:
        SQLAlchemyError: If there is an issue executing the database query.
    """
```

## 2. Pydantic and FastAPI OpenAPI Integration

FastAPI automatically parses docstrings and Pydantic models to construct the Swagger UI (`/docs`). To maximize the value of this feature:

- **Pydantic Field Descriptions:** When defining request or response schemas (e.g., `BaseModel`), use `Field(description="...")` to provide explicit descriptions for external API consumers.
- **Endpoint Docstrings:** Write clear docstrings on the FastAPI route functions (`@router.get(...)`). FastAPI will extract the summary and description directly from the docstring to populate the Swagger UI path operation.

### Pydantic Schema Example
```python
from pydantic import BaseModel, Field, EmailStr

class SignupRequest(BaseModel):
    """Schema for a new user registration request."""
    email: EmailStr = Field(description="The user's valid email address.")
    password: str = Field(min_length=8, description="The user's chosen password, minimum 8 characters.")
```

### FastAPI Endpoint Example
```python
@router.post("/signup", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def signup(request: SignupRequest, service: AuthService = Depends(get_auth_service)):
    """Register a new user in the system.
    
    This endpoint accepts a new user's email and password, creates a secure hash 
    of the password, stores the user in the database, and returns a JWT access token.
    """
    return await service.signup(request)
```

## 3. Strict Type Hinting

All functions, methods, and class attributes must contain strict Python type hints.
- Use built-in types (`str`, `int`, `dict`, `list`) or standard library types from `typing` (`Optional`, `Any`, `Callable`, `AsyncGenerator`).
- Use new union syntax (`Type | None`) instead of `Optional[Type]` for Python 3.10+.
- Type hints act as live documentation and are critical for FastAPI's data validation and serialization to function properly.

## Instructions for Execution

When you are asked to apply this skill:
1. Review the target file(s).
2. Ensure every class and function has a valid Google-style docstring.
3. Ensure every Pydantic attribute has a `Field(description="...")` if it is a public-facing schema.
4. Verify strict type hinting is present on all arguments and return values.
5. Add module-level docstrings at the top of the file summarizing the file's purpose.
6. Commit or write the changes back to the target files securely.
