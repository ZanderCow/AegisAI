---
name: testing
description: Guidelines and standards for writing tests across the React/Vite frontend and FastAPI backend.
---

# Testing Standards

This skill provides comprehensive guidelines for how to write tests in this project. Our stack consists of a React/Vite frontend and a FastAPI (Python) backend. As an AI Agent, you should adhere strictly to these patterns.

## Backend Testing (FastAPI + Pytest)

### Structure & Location
- Place all backend tests inside the `backend/tests/` directory.
- Differentiate between unit tests (`backend/tests/unit/`) and integration tests (`backend/tests/integration/`).

### Integration Tests
- **Framework**: `pytest`, `pytest_asyncio`, and `httpx.AsyncClient`.
- **Database Isolation**: We use an in-memory SQLite database (`sqlite+aiosqlite:///:memory:`) for integration tests to ensure isolation and speed.
- **Dependency Override**: Use FastAPI's `app.dependency_overrides` to swap out the production `get_db` generator with the testing session generator.
- **Fixtures**: 
  - Define an `autouse=True` async fixture (e.g., `setup_database`) that calls `Base.metadata.create_all` before the test and `drop_all` after the test.
  - Define an async `client` fixture using `AsyncClient(transport=ASGITransport(app=app), base_url="http://test")`.
- **Naming & Async**: Use `@pytest.mark.asyncio` on async test functions. Name them `test_<behavior>`.

### Unit Tests
- Fast, isolated tests focusing on a single module (e.g., `test_jwt.py` testing `create_token`).
- Do not require database setup or network layers. Mock external dependencies if necessary.

## Frontend Testing (React + Vitest)

### Structure & Location
- Place tests inside the `frontend/src/test/` directory. (e.g., previously they were side-by-side with components, but now we isolate them directly under `test/`).
- Mirror the source code structure (e.g., tests for `src/components/ui/Badge.tsx` go in `src/test/components/ui/Badge.test.tsx`).

### Tools & Patterns
- **Framework & Runner**: `vitest` for the test runner and assertions (`describe`, `it`, `expect`).
- **DOM Testing**: `@testing-library/react` for rendering components (`render`, `screen`).
- **Assertions**: We use `jest-dom` matchers like `.toBeInTheDocument()` and `.toHaveClass()`.
- **Variables & Variants**: When testing UI components with variants (e.g., success, warning, danger), write separate `it` blocks verifying that each variant applies the correct CSS classes.
- **Custom Classes**: Always verify that custom `className` properties passed as props are properly merged with default component classes.

## Executing Tests

Docker Compose is utilized to orchestrate the execution of tests across the stack:
- **`docker-compose.dev.yml`**: Use this configuration to run your backend unit tests, backend integration tests, and frontend unit tests.
- **`docker-compose.yml`**: Use this configuration to execute the complete end-to-end (E2E) test suite.

## General Agent AI Execution Rules
- **Progressive Disclosure**: Only read relevant files as needed. Do not guess class names or test names.
- **Conciseness**: Produce minimal boilerplate. Keep test files focused on the behavior being validated.
- **Idempotency**: Ensure tests can be run multiple times independently with zero shared state side-effects.
