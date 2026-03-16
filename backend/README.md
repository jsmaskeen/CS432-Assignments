# RAJAK Backend (Phase 1 Minimal Setup)

Minimal FastAPI + SQLAlchemy setup.

## Includes

- App bootstrap
- MySQL connection via SQLAlchemy
- `Member` SQLAlchemy model + Pydantic schemas
- Testing endpoints for DB health and Member CRUD

## Quick Start

1. Create virtual environment and activate it.
2. Install dependencies:
    - `pip install -r requirements.txt`
3. Copy `.env.example` to `.env` and fill MySQL credentials.
4. Run the SQL Dump file on your MySQL server.
5. Run app:
    - `uvicorn main:app --reload`

## Docs

- Swagger UI: `http://127.0.0.1:8000/docs`

## Testing Endpoints

- `GET /api/v1/health`
- `GET /api/v1/testing/db`
- `POST /api/v1/testing/members`
- `GET /api/v1/testing/members/{member_id}`
- `GET /api/v1/testing/members`
