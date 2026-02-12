---
name: documentation-standards
description: >
  Enforces the project's Python documentation and commenting conventions.
  Use this skill whenever writing new modules, classes, functions, tests,
  or configuration in this codebase to ensure consistent style.
---

# Documentation Standards

This skill defines the exact documentation and commenting conventions used
across the codebase. Follow every rule below when writing or modifying code.

## When to use this skill
- When creating new Python modules, classes, or functions.
- When performing code reviews to ensure documentation consistency.
- When refactoring existing code to improve clarity and adherence to standards.

## How to use it
- Refer to the rules defined in this file for each code element.
- Use the example files in the `examples/` directory for reference implementations.

---

---

## 1. Module-Level Docstrings

Every `.py` file (except `__init__.py`) **must** begin with a module docstring
using the following structure:

```python
"""
<filename>
<underline matching filename length, using '='>
<One-line summary of the module's purpose.>

<Optional extended description. Write in full sentences. Reference
other modules with ``:pymod:`src.module_name``` and inline code
with double backticks ``like_this``.>

<Zero or more named sections (see Section 2 below).>
"""
```

### Rules

- The **first line** is the bare filename (e.g. `database.py`).
- The **second line** is an `=` underline whose length matches the filename.
- A **blank line**, then a one-line summary.
- A **blank line**, then any extended prose / sections.
- Use **reStructuredText** (rST) directives when needed:
  - `.. code-block:: bash` for runnable examples.
  - `.. warning::` for cautionary notes.
- Reference library names in **bold** (`**pydantic-settings**`).
- Reference code identifiers with **double backticks** (``` ``AsyncSession`` ```).
- End the docstring with `"""` on its own line.

### Sections to Use Inside Module Docstrings

Use any combination of these named sections, each with an rST underline:

| Section           | When to use                                        |
|-------------------|----------------------------------------------------|
| `Responsibilities`| List what the module owns (use bullet `*` items)   |
| `Usage`           | Show a short import + usage code block             |
| `Notes`           | Call out non-obvious design choices (bullet items)  |
| `Endpoints`       | Router modules — use an rST table (see §5)         |
| `Functions`       | Service modules — list each public function         |
| `Schemas`         | Schema modules — list each schema with description  |
| `Column Design Choices` | Model modules — explain column decisions     |
| `Running Locally` | Entry-point modules — show the run command          |
| `Test Matrix`     | Test modules — rST table of test names & outcomes   |

### Example (from `database.py`)

```python
"""
database.py
===========
Centralised async database configuration for the application.

Responsibilities
----------------
* Load the ``DATABASE_URL`` from environment variables via **pydantic-settings**.
* Create a single ``AsyncEngine`` (backed by **asyncpg**) with sensible
  connection-pool defaults.
* Provide an ``async_sessionmaker`` factory that produces ``AsyncSession``
  instances bound to the engine.
* Expose a FastAPI-compatible dependency – ``get_session()`` – that yields one
  ``AsyncSession`` per request and guarantees cleanup afterwards.

Usage
-----
Import ``get_session`` in your routers and declare it as a FastAPI dependency::

    from src.database import get_session

    @router.get("/items")
    async def list_items(session: AsyncSession = Depends(get_session)):
        ...

Notes
-----
* ``expire_on_commit=False`` prevents SQLAlchemy from issuing implicit lazy
  loads after a commit, which would fail inside an async context.
* ``pool_pre_ping=True`` lets the pool transparently replace stale connections.
"""
```

---

## 2. Section Divider Comments

Use section dividers to visually separate logical blocks within a file.
The format is:

```python
# ── Section Name ────────────────────────────────────────────────────────
```

### Rules

- Start with `# ── ` (hash, space, two em-dashes, space).
- Follow with the section name in **Title Case**.
- Pad the rest of the line with `─` (box-drawing horizontal) characters.
- Target a total line length of roughly **77 characters**.
- Place a **blank line above** and a **blank line below** each divider.

### Standard Section Names by File Type

| File type     | Typical sections                                                      |
|---------------|-----------------------------------------------------------------------|
| `database.py` | `Settings`, `Engine & Session Factory`, `ORM Base`, `FastAPI Dependency` |
| `schemas.py`  | `Request Schemas`, `Response Schemas`                                  |
| `router.py`   | `Register Routers` (in `main.py`)                                      |
| `conftest.py` | `Load Settings`, `Test Engine & Session Factory`, `Fixtures`           |
| `test_*.py`   | `Helpers`, `Tests`                                                     |
| `main.py`     | `Register Routers`                                                     |

---

## 3. Class Docstrings

### ORM Models

```python
class User(Base):
    """Represents an application user stored in the ``users`` table.

    Attributes
    ----------
    id : uuid.UUID
        Primary key generated server-side by PostgreSQL.
    email : str
        The user's email address (unique, max 320 characters per RFC 5321).
    ...
    """
```

- First line: "Represents …" or equivalent summary with the table name in
  double backticks.
- Use a **NumPy-style** `Attributes` section listing every column.
- Each attribute line: `name : type` followed by an indented description.

### Pydantic Schemas

```python
class UserCreate(BaseModel):
    """Schema for the **POST /users/** request body.

    Attributes
    ----------
    email : EmailStr
        A valid email address (validated by Pydantic's ``EmailStr``).
    ...
    """
```

- First line references the **HTTP method and path** in bold.
- Use the same NumPy-style `Attributes` section.

### Settings Classes

```python
class Settings(BaseSettings):
    """Application settings populated from environment variables.

    Pydantic-settings reads a ``.env`` file (if present) and merges the
    values with real environment variables.  The ``DATABASE_URL`` variable
    is required – the application will refuse to start without it.
    """
```

- Describe the source and behavior of settings loading.

---

## 4. Function / Method Docstrings

Use **NumPy-style** docstrings throughout.

```python
async def create_user(session: AsyncSession, data: UserCreate) -> User:
    """Persist a new user and return the created ORM instance.

    Parameters
    ----------
    session : AsyncSession
        The database session for this request.
    data : UserCreate
        Validated request payload describing the new user.

    Returns
    -------
    User
        The newly created user **after** the row has been flushed to the
        database (so server-generated defaults like ``id`` and
        ``created_at`` are populated).
    """
```

### Rules

- **Summary line**: imperative mood, one sentence, no period unless multi-sentence.
- **Parameters** section: every parameter listed as `name : Type` with an
  indented description below.
- **Returns** section: return type on one line, indented description below.
- Use `| None` in the return type when the function can return `None`.
- Wrap long descriptions at ~72 characters within the docstring.

### Short Docstrings (Router Handlers)

Router endpoint functions use a **single-line** docstring referencing the
HTTP method and path in bold:

```python
async def create_user(...) -> UserRead:
    """Handle **POST /users/** – create a user."""
```

### Short Docstrings (Test Helpers)

Small utility functions use a **single-line** docstring:

```python
def _unique_email(label: str = "user") -> str:
    """Generate a unique email address to avoid test collisions."""
```

### Short Docstrings (Test Functions)

Test functions use a **single-line** docstring describing the HTTP call
and the expected outcome:

```python
async def test_create_user(client: AsyncClient) -> None:
    """POST /users/ should create a user and return 201 with all fields."""
```

### Fixture Docstrings

```python
@pytest.fixture(scope="session", autouse=True)
async def _setup_database() -> AsyncGenerator[None, None]:
    """Create all tables before the test session, drop them afterwards.

    This fixture runs **once** for the entire test session.  It ensures
    the database schema matches the current ORM models.
    """
```

- Summarize what the fixture provides and its scope.

---

## 5. Inline Comments

### Phase/Step Comments (within functions)

Use section-style inline comments to label distinct phases inside longer
functions:

```python
# ── Startup ─────────────────────────────────────────────────────────
async with engine.begin() as conn:
    await conn.run_sync(Base.metadata.create_all)

yield  # Application runs here

# ── Shutdown ────────────────────────────────────────────────────────
await engine.dispose()
```

### Explanatory Inline Comments (in tests)

Use short comments to separate logical steps in test functions:

```python
# Verify every field we sent is echoed back.
assert body["email"] == payload["email"]

# Verify server-generated fields are present.
assert "id" in body

# Create two users so the list is non-empty.
user_a = { ... }

# Fetch the list.
response = await client.get("/users/")

# Retrieve by ID.
response = await client.get(f"/users/{user_id}")
```

- Comments go on the line **above** the code they describe.
- Use full sentences starting with a capital letter and ending with a period.

### Attribute-Level Docstrings

Immediately after a module-level variable assignment, add a docstring:

```python
engine: AsyncEngine = create_async_engine(...)
"""Global async engine instance – one per process."""
```

---

## 6. SQLAlchemy Column Comments

Every `mapped_column` must include a `comment=` keyword argument with a
short, human-readable description:

```python
email: Mapped[str] = mapped_column(
    String(320),
    unique=True,
    nullable=False,
    index=True,
    comment="User email address – unique, max 320 chars (RFC 5321).",
)
```

---

## 7. Pydantic Field Descriptions

Every Pydantic `Field()` must include a `description=` keyword:

```python
email: EmailStr = Field(
    ...,
    description="A valid email address for the new user.",
    examples=["alice@example.com"],
)
```

Use `examples=` on request schemas where it aids OpenAPI documentation.

---

## 8. FastAPI Endpoint Metadata

Every router decorator must include `summary=` and `description=`:

```python
@router.post(
    "/",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new user",
    description=(
        "Register a new user with a unique email and username. "
        "Returns the created user object including server-generated fields."
    ),
)
```

- `summary`: short title for the endpoint (shown in Swagger sidebar).
- `description`: one or two sentences with full detail (shown in expanded view).
- Multi-line descriptions use string concatenation inside parentheses.

---

## 9. Configuration File Comments

`pyproject.toml` options get a comment **above** each setting:

```toml
[tool.pytest.ini_options]
# Automatically detect and run async test functions without
# requiring the @pytest.mark.asyncio decorator on every test.
asyncio_mode = "auto"

# Standard test discovery paths.
testpaths = ["tests"]
```

---

## 10. RST Tables in Module Docstrings

Use rST grid tables for structured data in module docstrings.

### Endpoint Table (in router modules)

```
Endpoints
---------
=======  ================  ===========================  ===============
Method   Path              Description                  Response Model
=======  ================  ===========================  ===============
POST     ``/users/``       Create a new user            ``UserRead``
GET      ``/users/``       List all users (paginated)   ``list[UserRead]``
GET      ``/users/{id}``   Retrieve a user by UUID      ``UserRead``
=======  ================  ===========================  ===============
```

### Test Matrix (in test modules)

```
Test Matrix
-----------
=================================  ========  ==================
Test                               Method    Expected Status
=================================  ========  ==================
``test_create_user``               POST      201 Created
``test_list_users``                GET       200 OK
``test_get_user_not_found``        GET       404 Not Found
=================================  ========  ==================
```

---

## 11. Type Annotations

- **Always** include return type annotations on functions.
- Use `-> None` for functions that return nothing.
- Use `| None` union syntax (not `Optional[]`).
- Use `collections.abc` types (e.g. `AsyncGenerator`, `AsyncIterator`)
  instead of `typing` module equivalents.

---

## 12. Import Ordering

Imports follow this order, with a blank line between each group:

1. Standard library (`uuid`, `datetime`, `contextlib`, etc.)
2. Third-party libraries (`fastapi`, `sqlalchemy`, `pydantic`, etc.)
3. Local application imports (`from src.database import ...`)

---

## 13. General Formatting Rules

- **Line length**: aim for ~88 characters max.
- **Two blank lines** between top-level definitions (classes, functions).
- **One blank line** after section divider comments.
- **Trailing newline** at end of file.
- **`__init__.py`** files are left empty (no docstring, no code).
- Use the `# type: ignore[call-arg]` comment when Pydantic settings
  instantiation triggers a false-positive type error.
