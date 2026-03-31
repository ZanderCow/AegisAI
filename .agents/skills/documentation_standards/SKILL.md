---
name: Documentation Standards
description: Apply comprehensive documentation standards across the codebase (Python/FastAPI Backend and React/TypeScript Frontend)
---

# Documentation Standards

This skill defines the strict documentation standards required for all code, covering both Python backend (FastAPI) and Frontend (React/TypeScript). Adhering to these standards ensures the codebase remains maintainable, readable, and maximizes developer experience.

## Backend: Python and FastAPI Documentation Standards

### 1. Docstring Format (Google Style)

All modules, classes, methods, and functions must be documented using **Google Style Docstrings**. 
- Always use triple-double quotes (`"""`) for docstrings.
- The docstring should immediately follow the definition line.
- For multi-line docstrings, start with a one-line summary, followed by a blank line, and then a more detailed description.

#### Class Documentation Example
```python
class UserRepository:
    """Repository for managing User database operations.
    
    This class handles all Create, Read, Update, and Delete (CRUD) 
    operations related to the User model in the database.
    
    Attributes:
        session (AsyncSession): The SQLAlchemy asynchronous database session.
    """
```

#### Function/Method Documentation Example
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

### 2. Pydantic and FastAPI OpenAPI Integration

FastAPI automatically parses docstrings and Pydantic models to construct the Swagger UI (`/docs`). To maximize the value of this feature:

- **Pydantic Field Descriptions:** When defining request or response schemas (e.g., `BaseModel`), use `Field(description="...")` to provide explicit descriptions for external API consumers.
- **Endpoint Docstrings:** Write clear docstrings on the FastAPI route functions (`@router.get(...)`). FastAPI will extract the summary and description directly from the docstring to populate the Swagger UI path operation.

#### Pydantic Schema Example
```python
from pydantic import BaseModel, Field, EmailStr

class SignupRequest(BaseModel):
    """Schema for a new user registration request."""
    email: EmailStr = Field(description="The user's valid email address.")
    password: str = Field(min_length=8, description="The user's chosen password, minimum 8 characters.")
```

#### FastAPI Endpoint Example
```python
@router.post("/signup", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def signup(request: SignupRequest, service: AuthService = Depends(get_auth_service)):
    """Register a new user in the system.
    
    This endpoint accepts a new user's email and password, creates a secure hash 
    of the password, stores the user in the database, and returns a JWT access token.
    """
    return await service.signup(request)
```

### 3. Strict Type Hinting

All functions, methods, and class attributes must contain strict Python type hints.
- Use built-in types (`str`, `int`, `dict`, `list`) or standard library types from `typing` (`Optional`, `Any`, `Callable`, `AsyncGenerator`).
- Use new union syntax (`Type | None`) instead of `Optional[Type]` for Python 3.10+.
- Type hints act as live documentation and are critical for FastAPI's data validation and serialization to function properly.

## Frontend: React and Vite Documentation Standards

### 1. Component Documentation (TSDoc/JSDoc)

All React components must be documented using TSDoc/JSDoc comment blocks immediately preceding the component definition.
- Use `/** ... */` for comments.
- Start with a clear, concise description of the component's purpose and usage.
- Document any important state or side-effects (hooks usage) if they are complex.

#### Component Documentation Example
```tsx
import React from 'react';

/**
 * Renders a primary call-to-action button with loading state support.
 * 
 * This component wraps the standard HTML button and applies Tailwind CSS
 * classes for consistent branding.
 */
export const PrimaryButton: React.FC<PrimaryButtonProps> = ({ 
  label, 
  isLoading, 
  onClick 
}) => {
  // ...
};
```

### 2. Props Documentation

All component props must be defined using TypeScript `interface` or `type` aliases. Each property within the interface must have a TSDoc comment explaining its purpose, expected values, and whether it's optional.

#### Props Documentation Example
```tsx
/**
 * Props for the PrimaryButton component.
 */
export interface PrimaryButtonProps {
  /** The text displayed inside the button. */
  label: string;
  
  /** 
   * Indicates whether the button is in a loading state. 
   * If true, a spinner is displayed and the button is disabled.
   * @default false
   */
  isLoading?: boolean;
  
  /** Callback function executed when the button is clicked. */
  onClick: () => void;
}
```

### 3. Hook and Utility Documentation

Custom React hooks and utility functions must also be fully documented with TSDoc, explicitly defining arguments (`@param`) and return values (`@returns`).

#### Hook Documentation Example
```ts
/**
 * Custom hook to manage the local storage state.
 *
 * @param key - The local storage key to read/write.
 * @param initialValue - The default value if the key does not exist.
 * @returns A stateful value and a function to update it.
 */
export function useLocalStorage<T>(key: string, initialValue: T): [T, (value: T) => void] {
  // ...
}
```

### 4. File Naming and Structure

- **Components:** Use PascalCase for both component names and their filenames (e.g., `PrimaryButton.tsx`).
- **Hooks:** Use camelCase starting with "use" (e.g., `useLocalStorage.ts`).
- **Utilities:** Use camelCase or kebab-case (e.g., `format-date.ts`).

## Instructions for Execution

When you are asked to apply this skill:
1. Review the target file(s) and determine if it is Frontend (TypeScript/React) or Backend (Python).
2. For Backend:
   - Ensure every class and function has a valid Google-style docstring.
   - Ensure every Pydantic attribute has a `Field(description="...")` if it is a public-facing schema.
   - Verify strict type hinting is present on all arguments and return values.
   - Add module-level docstrings at the top of the file summarizing the file's purpose.
3. For Frontend:
   - Ensure every exported component, interface, type alias, hook, and significant utility function has a valid TSDoc/JSDoc comment block.
   - Validate that strict TypeScript typing is used for all props, function arguments, and return values.
   - Ensure the component adheres to modern React functional component patterns using Hooks.
   - Apply the standard naming conventions.
4. Commit or write the changes back to the target files securely, ensuring no existing functionality is broken.
