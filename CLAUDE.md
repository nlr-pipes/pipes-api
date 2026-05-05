# Agent Guide

This file provides guidance to coding agent when working with code in this project repository.

## 1. Project Overview

PIPES API is a REST API that manages datasets, models, and end-to-end project workflows for the NLR PIPES platform.
It is built with FastAPI and exposes API resources for projects, project runs, models, model runs, datasets, handoffs,
tasks, teams, users, access groups, and catalog entries.

---

## 2. Architecture and Tech Stack

PIPES API Server is the core of the PIPES platform, where the REST API endpoints would be consumed

| Layer | Technology |
|---|---|
| Web framework | FastAPI 0.128, Python ≥ 3.10 |
| ASGI server | Uvicorn |
| ODM / async driver | Beanie 1.30 + Motor (AsyncIOMotorClient) |
| Database (local) | MongoDB 6.0 (Docker) |
| Database (deployed) | AWS DocumentDB (replica set, TLS) |
| Auth | AWS Cognito — JWT verified with `python-jose`; `CognitoJWKsVerifier` caches JWKS |
| Settings | `pydantic-settings` — env-based (`local` / `testing` / `dev` / `stage` / `prod`) |
| HTTP schemas | Pydantic v2 (`BaseModel` for request/response, `beanie.Document` for DB collections) |
| Local dev | `docker-compose.yaml` — `mongo` + `api` services; hot-reload via volume mount |
| Linter / formatter | Ruff (line-length 119, double quotes, space indent, Google docstyle) |
| Pre-commit hooks | check-yaml/json/toml, pyupgrade (py310+), mypy, ruff-check --fix, ruff-format, mypy |

Auth flow: every protected route declares `user: UserDocument = Depends(auth_required)`.
`auth_required` calls `CognitoJWKsVerifier` to validate the Bearer token, then looks up or creates the `UserDocument` in the DB.

Environment variables are loaded from `.env` (local) or `.env.test` (testing).
Required vars include `PIPES_ENV`, `PIPES_COGNITO_USER_POOL_ID`, `PIPES_COGNITO_CLIENT_ID`, `PIPES_DOCDB_HOST`, `PIPES_DOCDB_PORT`.

---

## 3. Project Layout

The `pipes/` package is the top-level container.
Each resource lives in its own sub-package with a consistent internal structure.

```
pipes-api/
├── main.py                   # Uvicorn entry point
├── entrypoint.sh             # Docker start script
├── docker-compose.yaml       # Local dev: mongo + api
├── Dockerfile                # Dev image
├── deployment/               # Production Dockerfile & entrypoint
├── pyproject.toml            # Build, deps, ruff, mypy config
├── requirements.txt          # Pinned runtime deps
├── requirements-dev.txt      # Dev/test extras
├── scripts/                  # One-off utility scripts (import_project, etc.)
├── tests/
│   ├── conftest.py           # Fixtures: settings, TestClient, Cognito access_token
│   ├── unit/                 # Fast tests; no live AWS/DB required
│   └── integration/          # Tests against real Cognito / DocDB
├── tox.ini                   # The tox test config file
└── pipes/
    ├── app.py                # FastAPI app factory, lifespan, CORS, routers
    ├── version.py            # __version__ (managed by setuptools-scm)
    ├── config/
    │   ├── settings.py       # Env-specific Settings classes
    │   └── logging.py
    ├── common/
    │   ├── constants.py      # NodeLabel enum, shared constants
    │   ├── exceptions.py     # All custom exception classes
    │   ├── schemas.py        # Shared Pydantic base schemas
    │   ├── utilities.py      # Helper functions (parse_datetime, etc.)
    │   └── validators.py     # ContextValidator, DomainValidator base classes
    ├── db/
    │   ├── abstract.py       # AbstractDatabase ABC
    │   ├── document.py       # DocumentDB (Beanie helpers: find_one, exists, …)
    │   ├── dynamo.py         # DynamoDB client (if used)
    │   └── manager.py        # AbstractObjectManager (provides self.d → DocumentDB)
    ├── users/
    │   ├── auth.py           # CognitoJWKsVerifier, auth_required dependency
    │   ├── manager.py
    │   ├── routes.py
    │   ├── schemas.py        # UserDocument (Beanie), UserCreate, UserRead
    │   └── validators.py
    └── <resource>/           # projects, models, modelruns, datasets, handoffs,
        ├── contexts.py       #   tasks, teams, projectruns, accessgroups,
        ├── manager.py        #   catalogdatasets, catalogmodels, …
        ├── routes.py
        ├── schemas.py
        └── validators.py
```

### Per-resource module conventions

| Module | Responsibility |
|---|---|
| `schemas.py` | Beanie `Document` (DB collection) + Pydantic `BaseModel` subtypes (`Create`, `Update`, `BasicRead`, `DetailRead`) |
| `contexts.py` | Lightweight Pydantic models that carry request context: `SimpleContext` (raw strings) → `DocumentContext` (loaded docs) → `ObjectContext` (ObjectIds) |
| `validators.py` | `ContextValidator` subclass (existence + permission check) and `DomainValidator` subclass (business-rule validation) |
| `manager.py` | Async business logic; inherits `AbstractObjectManager`; accesses DB via `self.d` |
| `routes.py` | FastAPI `APIRouter`; receives `user` from `Depends(auth_required)`; calls manager; maps exceptions to HTTP status codes |

---

## 4. Coding Style and Conventions

### General

- Python 3.10+ type-hint syntax is acceptable (`X | Y` instead of `Optional[X]`).
- Use `async`/`await` throughout — all DB calls and route handlers are async.
- Maximum line length: **119 characters**.

### Imports

- Group in order: `__future__`, stdlib, third-party, local (`pipes.*`). Ruff enforces this with `isort` rules.
- Prefer absolute imports (`from pipes.projects.schemas import …`).

### Schemas (Pydantic / Beanie)

- DB collections: subclass `beanie.Document`. Define `Settings` inner class with `name` and `indexes` when needed.
- Request/response models: subclass `pydantic.BaseModel`. Use `Create`, `Update`, `BasicRead`, `DetailRead` suffixes.
- Use `Field(title=…, description=…)` on every field.
- Use `@field_validator(…, mode="before")` with `@classmethod` for input coercion.
- Docstrings follow Google style and list each attribute under `Attributes:`.

### Routes

- Declare the response model explicitly: `@router.get("/…", response_model=…)`.
- Use `status_code=201` for `POST` endpoints that create resources.
- Catch domain/context exceptions and re-raise as `HTTPException` with the appropriate status code:
  - `400` — `DocumentDoesNotExist`, `DomainValidationError`, `ContextValidationError`
  - `403` — `UserPermissionDenied`

### Managers

- Inherit `AbstractObjectManager`.
- Access DocumentDB via the `self.d` property (returns a `DocumentDB` instance).
- Decompose complex operations into focused private methods prefixed with `_`.

### Validators

- **ContextValidator**: implement `validate_document(context)` and `validate_permission(user)`. Call `super().validate_permission(user)` to enforce the active-user check.
- **DomainValidator**: implement methods with names starting with `validate_`; the base `validate()` method calls them all automatically.

### Exceptions

- Use the custom exceptions from `pipes.common.exceptions` exclusively — never raise raw `ValueError` or `Exception` for application-level errors.

### Ruff Formating

Run locally before committing:

```bash
ruff check --fix .
ruff format .
```

Pre-commit enforces both on every commit. Mypy also runs via pre-commit.

---

## 5. Testing

### Setup

```bash
# Install dev dependencies
pip install -e ".[dev,test]"

# Copy and fill in test environment variables
cp .env.example .env.test   # set PIPES_ENV=testing and Cognito/DocDB test values
```

### Running tests

```bash
# Run all tests with coverage
pytest --cov=pipes --disable-pytest-warnings tests/

# Via tox (matches CI)
tox

# Coverage report (must be 100 % for tox:coverage env)
tox -e coverage
```

### Test structure

- `tests/unit/` — fast, no live infrastructure. Mock DB and Cognito interactions.
- `tests/integration/` — require real Cognito credentials. Token is fetched once from AWS and cached in `tests/cognito-idp-auth.json`; subsequent runs reuse it until expiry.

### Key fixtures (`tests/conftest.py`)

| Fixture | Scope | Purpose |
|---|---|---|
| `pipes_settings` | function | Returns `TestingSettings` from `get_settings("testing")` |
| `test_client` | function (autouse) | `TestClient(app)` — synchronous HTTPX client wrapping the FastAPI app |
| `access_token` | function | Cognito `AccessToken`; caches to disk; fetches fresh when expired |

### Conventions

- Use `test_client` to make HTTP requests; pass the `access_token` as `Authorization: Bearer <token>` for protected endpoints.
- Assert both status codes and response body fields.
- Unit tests for validators should test `validate_document` and `validate_permission` independently.
- Add a test for every new route, manager method, and validator.
