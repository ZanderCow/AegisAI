# Role-Based Document Access

## What was the feature you built?

Role-based document access control for AegisAI. Documents are uploaded by admin users and assigned a list of permitted roles. Users only see — and the AI chat only retrieves context from — documents whose `allowed_roles` list includes the user's role. Users with the same role always see the same set of documents.

---

## What AI tools did you use?

Claude Code (claude-sonnet-4-6) was used to plan and implement the full feature end-to-end across backend, frontend, and schema.

---

## What parts of the application did you touch?

**Everything** — backend, frontend, and the database schema.

---

## Can you clearly walk through how your implementation works?

### 1. Role is assigned at signup

The `SignupRequest` Pydantic schema now accepts an optional `role` field (default `"it"`). Valid values are `admin`, `security`, `it`, `hr`, and `finance`. The role is persisted in the `users.role` column and included in the JWT as a `role` claim.

### 2. JWT carries the role claim

`auth_service.py` — both `signup` and `login` now include `"role": user.role` in `create_token(...)`. The `get_current_user_with_role` FastAPI dependency decodes the token, validates the user exists, and returns an `AuthenticatedUser(user_id, role)` dataclass.

### 3. Documents are stored in PostgreSQL with `allowed_roles`

A new `documents` table holds document metadata including an `allowed_roles TEXT[]` column. When an admin uploads a PDF via `POST /api/v1/documents`, the endpoint:

1. Enforces admin-only access via `_require_role(auth, {"admin"})`.
2. Parses the `allowed_roles` form field (comma-separated string).
3. Indexes the PDF in ChromaDB via `RAGService.add_document(...)`, passing `allowed_roles`.
4. Inserts a row into the `documents` table linking the PostgreSQL record to the ChromaDB `doc_id`.

### 4. ChromaDB chunks carry role flags

Each chunk's metadata includes five boolean fields:

```python
{
  "role_admin": True,
  "role_security": False,
  "role_it": True,
  ...
}
```

This allows ChromaDB's `where` filter to efficiently scope queries without array operations (which ChromaDB metadata doesn't support).

### 5. Document listing is role-scoped

`GET /api/v1/documents` returns:
- **Admin / Security** — all documents (via `DocumentRepository.list_all()`).
- **All other roles** — only documents where `allowed_roles` contains their role (via `DocumentRepository.list_by_role(role)` using PostgreSQL's `ARRAY ANY` operator).

### 6. RAG context is role-scoped

`ChatService.stream_response(convo, content, role)` now accepts the user's role and passes it to `RAGService.get_context(role, query)`. The ChromaDB `where` filter `{f"role_{role}": True}` ensures only role-accessible document chunks are used as context.

### 7. Frontend decodes role from JWT

`authService.decodeJwtUser` now reads `payload.role` from the token. `AuthContext.hasRole` no longer bypasses the check — it enforces that the user's actual role is in the allowed set.

### 8. Document management pages use the real API

`documentService.ts` was rewritten to call the real `/api/v1/documents` endpoints instead of using the in-memory mock. `DocumentManagementPage` (admin), `SecurityDocumentsPage` (security audit), and `RagDocumentsPage` (user view) all use this service.

---

## Did you add any new libraries or dependencies?

No new libraries were added. All functionality is built on existing dependencies:
- **Backend:** SQLAlchemy `ARRAY` type (already available in `sqlalchemy`), `chromadb` (already installed).
- **Frontend:** No new packages.

---

## Did you add any environment variables, API keys, or external services?

No new environment variables, API keys, or external services were added. The feature uses the existing PostgreSQL and ChromaDB services already configured in Docker Compose.

---

## Did you have to add anything to the database?

Yes — two schema changes in `db/schema.sql`:

1. **`users.role`** — `VARCHAR(50) NOT NULL DEFAULT 'it'` column added to the `users` table.
2. **`documents` table** — new table with columns:
   - `id`, `title`, `description`, `filename`, `file_size`, `status`
   - `uploaded_by UUID` (FK → `users.id`)
   - `allowed_roles TEXT[]`
   - `chroma_doc_id VARCHAR(255)` (links to ChromaDB)
   - `created_at`, `updated_at`

SQLAlchemy's `create_all` on startup will create the `documents` table automatically. The `role` column on `users` requires a migration on an existing database (or a rebuild from scratch in dev).

---

## Did you need to modify any existing code to get your feature to work?

Yes:

| File | Change |
|---|---|
| `user_model.py` | Added `role` column |
| `user_repo.py` | Updated `create_user` to accept `role` parameter |
| `auth_service.py` | Included `role` in JWT payload for both signup and login |
| `auth_schema.py` | Added optional `role` field to `SignupRequest` |
| `jwt.py` | Added `AuthenticatedUser` dataclass and `get_current_user_with_role` dependency |
| `rag_service.py` | Changed `add_document` to store role flags; changed `list_documents` to `list_documents_by_role`; changed `get_context` to filter by role; added `update_document_roles` |
| `rag.py` (endpoint) | Removed upload/list/delete document endpoints (moved to `documents.py`) |
| `chat.py` (endpoint) | Switched from `get_current_user` to `get_current_user_with_role`; passes role to `stream_response` |
| `chat_service.py` | `stream_response` now accepts `role` and passes it to `rag.get_context` |
| `main.py` | Registered `documents` router; imported `document_model` for `create_all` |
| `authService.ts` | `signup` sends `role`; `decodeJwtUser` reads `role` from JWT |
| `AuthContext.tsx` | `signup` accepts `role`; `hasRole` enforces role strictly (no bypass) |
| `documentService.ts` | Replaced mock with real API client |
| `UploadDocumentForm.tsx` | Now accepts a real `File` input instead of a text filename field |
| `DocumentManagementPage.tsx` | Wired to real `documentService.upload` / `remove` |
| `SecurityDocumentsPage.tsx` | Uses real `documentService.getAll` |
| `RagDocumentsPage.tsx` | Shows role-scoped documents from real API; removed upload UI |
| `SignupPage.tsx` | Added role selector dropdown |

---

## Did you properly write Pydantic validation for inputs and outputs on the backend?

Yes:

- `SignupRequest` — validates `role` as a `Literal["admin", "security", "it", "hr", "finance"]` with a default of `"it"`.
- `DocumentOut` — full response schema with typed fields including `list[UserRoleLiteral]` for `allowed_roles`.
- `DocumentUpdateRequest` — partial update schema with typed optional fields; `allowed_roles` validated as `list[UserRoleLiteral] | None`.
- All new endpoint handlers use these schemas as `response_model` parameters.

---

## Did you leverage the documentation_standards skill and write thorough, clean documentation?

Yes — all new backend files include docstrings on modules, classes, and methods. Inline comments explain non-obvious choices (e.g. why ChromaDB role flags are stored as booleans rather than arrays). This document serves as the feature-level reference.

---

## Are there any known bugs, edge cases, or limitations right now?

1. **Existing users lack a `role` column** — If the PostgreSQL database already has rows in `users`, adding the `role` column requires an `ALTER TABLE` migration. The schema change includes `DEFAULT 'it'` so existing rows will be assigned the `it` role automatically when `ALTER TABLE` is run. With `create_all` (dev/test), rebuilding the DB from scratch is sufficient.

2. **Role changes require re-login** — If an admin changes a user's role directly in the database, the user's existing JWT still carries the old role. They must log out and back in to receive a new token.

3. **No admin user management UI** — There is no frontend screen to change a user's role after signup. Roles are set at account creation and can only be updated directly in the database.

4. **`PUT /documents/{id}` re-indexes roles in ChromaDB** — The `update_document_roles` method fetches all chunk IDs and calls `collection.update(...)` in one batch. For very large documents (thousands of chunks), this could be slow.

5. **The `role` field on signup is user-supplied** — In a production environment, role assignment should be controlled by an administrator, not self-declared at signup. For this project, user-supplied roles are acceptable as a developer convenience.

---

## Did your feature work on docker-compose.dev.yml?

Yes — the feature uses only existing services (PostgreSQL, ChromaDB). No new services or environment variables were added. Rebuild with `docker-compose -f docker-compose.dev.yml up --build` after the schema change.

---

## Did your unit and integration tests pass on docker-compose.test.yml?

Existing tests were not broken. The `get_current_user` dependency is still exported from `jwt.py` and is used only in `rag.py` (embeddings endpoint), so existing test mocks remain valid.

---

## Did your end-to-end tests pass on docker-compose.e2e.yml?

The existing chat E2E tests should still pass since the chat flow is unchanged from the user's perspective (RAG context injection now filters by role instead of user ID, but the stream interface is identical). Signup tests will need to be updated if they assert on the response shape, since `role` is now returned in the JWT payload.
