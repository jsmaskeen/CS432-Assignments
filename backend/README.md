# RAJAK Backend (Module B App Dev)

FastAPI + SQLAlchemy backend with username/password JWT auth and ride booking APIs.

## Includes

- App bootstrap + CORS
- MySQL connection via SQLAlchemy
- JWT auth (`register`, `login`, `me`)
- Role field (`user` / `admin`) in credentials
- Ride creation/listing/booking APIs
- Testing endpoints for health and DB connectivity
- Audit logging to `audit.log` for write operations

## Quick Start

1. Create virtual environment and activate it.
2. Install dependencies:
    - `pip install -r requirements.txt`
3. Copy `.env.example` to `.env` and fill MySQL credentials.
4. Run the SQL dump on your MySQL server.
5. Configure JWT and DB values in `.env`.
6. Run app:
    - `uvicorn main:app --reload`

## Docs

- Swagger UI: `http://127.0.0.1:8000/docs`

## Testing Endpoints

- `GET /api/v1/health`
- `GET /api/v1/testing/db`

## Auth Endpoints

- `POST /api/v1/auth/register`
- `POST /api/v1/auth/login`
- `GET /api/v1/auth/me`
- `POST /api/v1/auth/admin/promote` (admin only)

## Admin Bootstrap

- Set `ADMIN_BOOTSTRAP_USERNAME` in `.env`.
- If a user registers with this username, they are assigned `admin` role.
- Existing user with that username is also promoted at startup.

## Audit File

- Data-modifying API actions append JSON lines to `audit.log`.
- This lets you compare API-attributed changes with direct DB edits.

## Ride Endpoints

- `GET /api/v1/rides`
- `POST /api/v1/rides`
- `POST /api/v1/rides/{ride_id}/book`
- `GET /api/v1/rides/my/bookings`
