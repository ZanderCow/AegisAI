AegisAI Workspace Guide

If you want to work on the front end, you gotta go to the front end folder:
- cd frontend/aegisai

If you want to work on the back end, you gotta go to the back end folder:
- cd backend

If you want to work on the end-to-end tests, you gotta go to the end-to-end test folder:
- cd e2e

If you want to work on the database, you gotta go to the database folder:
- cd db

Run End-to-End Services (Docker)

From the project root, run this to spin up database -> backend -> frontend -> selenium -> e2e tests:
- docker compose -f docker-compose.e2e.yml up --build --abort-on-container-exit --exit-code-from e2e-tests

When done, tear down everything:
- docker compose -f docker-compose.e2e.yml down --volumes --remove-orphans

CI/CD Pipeline Status

CI is set up in:
- .github/workflows/ci.yml

Deploy boilerplate is set up in:
- .github/workflows/deploy.yml

Supporting docs:
- docs/ci-cd.md
- e2e/README.md

Notes:
- CI runs backend unit tests, backend integration tests, frontend lint/build, and docker-compose Selenium e2e auth tests.
- Railway deploy is boilerplate and stays disabled until you provide credentials and enable deploy variables.
