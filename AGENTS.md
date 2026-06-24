# Repository Guidelines

## Project Structure & Module Organization

This repository is a FastAPI backend for IT ticketing and asset management. Application code lives in `app/`: `api/v1/routes/` contains endpoint modules, `api/v1/router.py` wires them together, `core/` holds settings and security helpers, `db/` defines database session/base setup, `models/` contains SQLAlchemy ORM models, `schemas/` contains Pydantic request/response models, and `services/` holds business logic. Tests are in `tests/` and should mirror user-visible behavior. Alembic migration support is in `alembic/` with configuration in `alembic.ini`. Database bootstrap SQL is stored in `db/it_ops_platform.sql`.

## Build, Test, and Development Commands

- `conda run -n itops`: Before executing any command, you need to load the Python environment first.
- `poetry install --no-root`: install runtime and development dependencies from `pyproject.toml`.
- `uvicorn app.main:app --reload`: run the API locally at `http://127.0.0.1:8000`.
- `pytest`: run the test suite under `tests/`.
- `ruff check .`: lint imports, Python style, upgrade hints, and common bug patterns.
- `alembic revision --autogenerate -m "message"`: create a migration from model changes.
- `alembic upgrade head`: apply pending migrations to the configured MySQL database.

## Coding Style & Naming Conventions

Target Python 3.11. Use 4-space indentation, type annotations for public functions, and clear module boundaries: routes should stay thin, services should hold business rules, schemas should define API contracts, and models should define persistence. Follow Ruff settings in `pyproject.toml`: 100-character line length with `E`, `F`, `I`, `UP`, and `B` rule families. Use snake_case for modules, functions, variables, and test names; use PascalCase for Pydantic schemas and SQLAlchemy model classes.

## Testing Guidelines

Tests use `pytest` and FastAPI `TestClient`. Name files `test_*.py` and functions `test_<behavior>()`. Prefer behavior-focused assertions on status codes and response JSON, as in `tests/test_health.py` and `tests/test_auth.py`. Add tests for new endpoints, auth behavior, validation rules, and service-level edge cases. Run `pytest` before opening a pull request.

## Commit & Pull Request Guidelines

Current history uses short imperative commit subjects such as `add user login` and `init commit`; keep subjects concise and action-oriented. Pull requests should include a brief summary, tests run (`pytest`, `ruff check .`), database migration notes when models change, and example requests/responses or screenshots for API documentation changes. Link related issues when available.

## Security & Configuration Tips

Copy `.env.example` to `.env` for local settings. Never commit real secrets, production database URLs, or token signing keys. Change `SECRET_KEY` outside local development, keep `DEBUG` disabled in production-like environments, and confirm `DATABASE_URL` points to the intended MySQL instance before running Alembic migrations.
