# RAJAK Backend (Module B App Dev)

FastAPI + SQLAlchemy backend with username/password JWT auth and ride booking APIs.

## Includes

- App bootstrap + CORS
- MySQL connection via SQLAlchemy
- JWT auth (`register`, `login`, `me`)
- Ride creation/listing/booking APIs
- Testing endpoints for health and DB connectivity

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

## Ride Endpoints

- `GET /api/v1/rides`
- `POST /api/v1/rides`
- `POST /api/v1/rides/{ride_id}/book`
- `GET /api/v1/rides/my/bookings`
