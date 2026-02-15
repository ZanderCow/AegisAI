# AegisAI Backend

The AegisAI backend is a **FastAPI** application using **MongoDB** (via the **Beanie** ODM) for persistence, **JWT tokens** for stateless authentication, and **Argon2** for password hashing. It follows a clean **layered architecture** that separates concerns across API routing, schemas, CRUD operations, models, and core services.

---

## Project Structure

```
backend/
├── main.py                          # App entrypoint & lifespan (DB init)
├── requirements.txt                 # Python dependencies
├── Dockerfile                       # Container build (Python 3.11)
├── docker-compose.test.yml          # Test env (MongoDB + pytest)
├── .env                             # Environment variables
│
├── src/
│   ├── core/                        # ⚙️ Core services
│   │   ├── config.py                # Settings (Pydantic-Settings)
│   │   ├── db.py                    # MongoDB / Beanie init
│   │   └── security.py              # JWT creation, password hashing
│   │
│   ├── models/                      # 📦 Database models
│   │   └── user_model.py            # User document (Beanie Document)
│   │
│   ├── schemas/                     # 📋 Request/Response schemas
│   │   ├── users.py                 # UserCreate, UserUpdate, UserResponse
│   │   ├── token.py                 # Token, TokenPayload
│   │   └── auth.py                  # (placeholder)
│   │
│   ├── crud/                        # 🗄️ Data-access layer
│   │   └── user.py                  # CRUDUser (create, get, authenticate)
│   │
│   └── api/                         # 🌐 API layer
│       ├── deps.py                  # Dependencies (get_current_user)
│       └── v1/
│           ├── api.py               # Router aggregator
│           └── endpoints/
│               ├── auth.py          # POST /signup, POST /login
│               ├── users.py         # GET /users/me
│               └── health.py        # GET /health
│
└── tests/
    └── test_users.py                # Integration tests (Beanie + User)
```

---

## Architecture

```mermaid
graph TB
    subgraph Client["🖥️ Client Application"]
        FE["Frontend / Mobile / API Consumer"]
    end

    subgraph FastAPI["⚡ FastAPI Application"]
        direction TB
        MW["main.py — App Entrypoint"]

        subgraph API["API Layer"]
            direction LR
            AR["api.py — Router Aggregator"]
            AUTH["auth.py — /auth endpoints"]
            USR["users.py — /users endpoints"]
            HLT["health.py — /health endpoints"]
        end

        subgraph Core["Core Services"]
            direction LR
            CFG["config.py — Settings"]
            SEC["security.py — JWT & Hashing"]
            DEPS["deps.py — Auth Dependency"]
        end

        subgraph Data["Data Layer"]
            direction LR
            SCH["schemas/ — Pydantic Schemas"]
            CRUD["crud/user.py — CRUD Operations"]
            MDL["models/user_model.py — User Document"]
        end

        DB_INIT["db.py — Beanie Init"]
    end

    subgraph Database["🗃️ MongoDB"]
        MONGO[("users collection")]
    end

    FE -->|"HTTP Requests"| MW
    MW --> AR
    AR --> AUTH
    AR --> USR
    AR --> HLT
    AUTH --> SCH
    AUTH --> CRUD
    AUTH --> SEC
    USR --> DEPS
    DEPS --> SEC
    DEPS --> MDL
    CRUD --> MDL
    CRUD --> SEC
    MDL --> MONGO
    DB_INIT --> MONGO
    MW -->|"lifespan startup"| DB_INIT
    CFG -.->|"provides settings"| SEC
    CFG -.->|"provides settings"| DB_INIT
    CFG -.->|"provides settings"| DEPS
```

---

## User Flows

### 1. Signup — `POST /api/v1/auth/signup`

A new user creates an account by submitting email, username, and password.

```mermaid
sequenceDiagram
    actor User as 👤 User
    participant FE as 🖥️ Client
    participant AUTH as auth.py
    participant SCH as UserCreate Schema
    participant CRUD as CRUDUser
    participant SEC as security.py
    participant MDL as User Model
    participant DB as 🗃️ MongoDB

    User->>FE: Fill signup form
    FE->>AUTH: POST /api/v1/auth/signup<br/>{"email", "username", "password"}

    Note over AUTH,SCH: ① Request Validation
    AUTH->>SCH: Validate with UserCreate
    SCH-->>AUTH: Validated data (or 422 error)

    Note over AUTH,CRUD: ② Uniqueness Checks
    AUTH->>CRUD: get_by_email(email)
    CRUD->>MDL: User.find_one(email)
    MDL->>DB: Query users collection
    DB-->>MDL: null (no match)
    MDL-->>CRUD: None
    CRUD-->>AUTH: None ✅

    AUTH->>CRUD: get_by_username(username)
    CRUD->>MDL: User.find_one(username)
    MDL->>DB: Query users collection
    DB-->>MDL: null (no match)
    MDL-->>CRUD: None
    CRUD-->>AUTH: None ✅

    Note over AUTH,DB: ③ User Creation
    AUTH->>CRUD: create(user_in)
    CRUD->>SEC: get_password_hash(password)
    SEC-->>CRUD: Argon2 hash
    CRUD->>MDL: User(email, username, hashed_password)
    MDL->>DB: Insert document
    DB-->>MDL: Document with _id
    MDL-->>CRUD: User object
    CRUD-->>AUTH: User object

    Note over AUTH,FE: ④ Response
    AUTH->>SCH: Serialize via UserResponse
    AUTH-->>FE: 201 {id, email, username, is_active, created_at}
    FE-->>User: Account created!
```

| Step | Component | What It Does |
|------|-----------|-------------|
| ① | `UserCreate` schema | Validates email format, requires username & password |
| ② | `CRUDUser.get_by_email/username` | Queries MongoDB to ensure no duplicate email or username (400 if found) |
| ③ | `security.get_password_hash` → `User.insert` | Hashes password with Argon2, creates Beanie Document, inserts into MongoDB |
| ④ | `UserResponse` schema | Serializes the User document, maps `_id` → `id`, strips `hashed_password` |

---

### 2. Login — `POST /api/v1/auth/login/access-token`

An existing user authenticates and receives a JWT access token.

```mermaid
sequenceDiagram
    actor User as 👤 User
    participant FE as 🖥️ Client
    participant AUTH as auth.py
    participant CRUD as CRUDUser
    participant SEC as security.py
    participant MDL as User Model
    participant DB as 🗃️ MongoDB
    participant CFG as config.py

    User->>FE: Enter email & password
    FE->>AUTH: POST /api/v1/auth/login/access-token<br/>(OAuth2 form: username=email, password)

    Note over AUTH,CRUD: ① Authentication
    AUTH->>CRUD: authenticate(email, password)
    CRUD->>MDL: User.find_one(email)
    MDL->>DB: Query users collection
    DB-->>MDL: User document
    MDL-->>CRUD: User object

    CRUD->>SEC: verify_password(plain, hashed)
    SEC-->>CRUD: True ✅
    CRUD-->>AUTH: User object

    Note over AUTH: ② Active Check
    AUTH->>AUTH: Check user.is_active
    Note right of AUTH: If inactive → 400 error

    Note over AUTH,SEC: ③ Token Generation
    AUTH->>CFG: Get SECRET_KEY, ALGORITHM, EXPIRE
    AUTH->>SEC: create_access_token(user.id, expires_delta)
    SEC->>SEC: Build JWT payload {sub: user_id, exp: timestamp}
    SEC->>SEC: jwt.encode(payload, SECRET_KEY, HS256)
    SEC-->>AUTH: "eyJhbGciOi..."

    Note over AUTH,FE: ④ Response
    AUTH-->>FE: 200 {"access_token": "eyJ...", "token_type": "bearer"}
    FE->>FE: Store token in localStorage/cookie
    FE-->>User: Logged in!
```

| Step | Component | What It Does |
|------|-----------|-------------|
| ① | `CRUDUser.authenticate` | Looks up user by email, verifies plain password against Argon2 hash |
| ② | `auth.py` | Checks `is_active` flag — inactive users get a 400 response |
| ③ | `security.create_access_token` | Creates JWT with `sub` (user ID) and `exp` (7-day expiry), signs with HS256 |
| ④ | Response | Returns the bearer token for the client to store and attach to future requests |

---

### 3. Authenticated Request — `GET /api/v1/users/me`

A logged-in user retrieves their own profile using the stored JWT.

```mermaid
sequenceDiagram
    actor User as 👤 User
    participant FE as 🖥️ Client
    participant USR as users.py
    participant DEPS as deps.py
    participant SEC as security.py
    participant TOK as TokenPayload Schema
    participant MDL as User Model
    participant DB as 🗃️ MongoDB

    User->>FE: View "My Profile"
    FE->>USR: GET /api/v1/users/me<br/>Header: Authorization: Bearer eyJ...

    Note over USR,DEPS: ① Dependency Injection
    USR->>DEPS: get_current_user(token)

    Note over DEPS,SEC: ② Token Decoding
    DEPS->>SEC: jwt.decode(token, SECRET_KEY, HS256)
    SEC-->>DEPS: {sub: "user_id", exp: timestamp}

    Note over DEPS,TOK: ③ Payload Validation
    DEPS->>TOK: TokenPayload(**payload)
    TOK-->>DEPS: token_data.sub = "user_id"

    Note over DEPS,DB: ④ User Lookup
    DEPS->>MDL: User.get(token_data.sub)
    MDL->>DB: Find by _id
    DB-->>MDL: User document
    MDL-->>DEPS: User object
    DEPS-->>USR: User object (injected)

    Note over USR,FE: ⑤ Response
    USR-->>FE: 200 {id, email, username, is_active, created_at}
    FE-->>User: Display profile
```

| Step | Component | What It Does |
|------|-----------|-------------|
| ① | FastAPI `Depends()` | Automatically calls `get_current_user` before the endpoint runs |
| ② | `jose.jwt.decode` | Decodes the JWT, verifying signature and expiration (403 if invalid) |
| ③ | `TokenPayload` schema | Validates the decoded payload structure, extracting `sub` (user ID) |
| ④ | `User.get()` | Fetches the full User document from MongoDB by ID (404 if not found) |
| ⑤ | `UserResponse` schema | Serializes the User document for the client, excluding sensitive fields |

---

### 4. Health Check — `GET /api/v1/health`

```mermaid
sequenceDiagram
    participant Client as 🖥️ Client / Load Balancer
    participant HLT as health.py

    Client->>HLT: GET /api/v1/health
    HLT-->>Client: 200 {"status": "ok", "message": "API is healthy"}
```

No authentication or database access required.

---

### 5. Application Startup

```mermaid
sequenceDiagram
    participant UV as Uvicorn
    participant APP as main.py
    participant CFG as config.py
    participant DBI as db.py
    participant MONGO as 🗃️ MongoDB

    UV->>APP: Start application
    APP->>CFG: Load Settings (from .env)
    CFG-->>APP: settings object

    Note over APP,MONGO: Lifespan startup
    APP->>DBI: init_db()
    DBI->>CFG: Get MONGODB_URL, DATABASE_NAME
    DBI->>MONGO: AsyncMongoClient(MONGODB_URL)
    MONGO-->>DBI: Connection established
    DBI->>DBI: init_beanie(database, [User])
    DBI-->>APP: DB ready ✅

    APP->>APP: Register routers (auth, users, health)
    APP-->>UV: App ready to serve requests
```

---

## Component Summary

| Layer | File(s) | Responsibility |
|-------|---------|----------------|
| **Entrypoint** | `main.py` | Creates FastAPI app, wires lifespan DB init, registers the v1 router |
| **Config** | `src/core/config.py` | Loads settings from `.env` via Pydantic-Settings (DB URL, JWT secret, token expiry) |
| **Database** | `src/core/db.py` | Initializes the async Mongo connection and Beanie ODM with registered document models |
| **Security** | `src/core/security.py` | Creates JWT tokens (`python-jose`), hashes and verifies passwords (`Argon2`) |
| **Models** | `src/models/user_model.py` | Beanie `Document` subclass mapping to the `users` MongoDB collection |
| **Schemas** | `src/schemas/users.py`, `src/schemas/token.py` | Pydantic models for request validation and response serialization |
| **CRUD** | `src/crud/user.py` | Data-access class with `create`, `get_by_email`, `get_by_username`, `authenticate` |
| **Dependencies** | `src/api/deps.py` | FastAPI dependency `get_current_user` — decodes JWT, fetches user from DB |
| **Endpoints** | `src/api/v1/endpoints/auth.py`, `users.py`, `health.py` | Route handlers for auth, user profile, and health check |
| **Infrastructure** | `Dockerfile`, `docker-compose.test.yml` | Container build and test orchestration |
| **Tests** | `tests/test_users.py` | Integration tests for Beanie init and user CRUD |
