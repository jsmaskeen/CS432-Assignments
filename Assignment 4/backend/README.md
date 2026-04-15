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

## Cleanup Without mysql CLI

If `mysql` command is not installed locally, use:
- `uv run python -m scripts.cleanup_db`

Optional:
- `uv run python -m scripts.cleanup_db --skip-auth-truncate`

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

## Sharding (Assignment 4)

- Configure shard settings in `.env`:
    - `SHARD_SHARED_HOST`, `SHARD_1_PORT`, `SHARD_2_PORT`, `SHARD_3_PORT`
    - `SHARD_DB_USER`, `SHARD_DB_PASSWORD`, `SHARD_DB_NAME`
- TO check most used attribute to choose a shard key:
    - `python scripts/shard_key.py`
- Migration script for ride-centric tables:
    - Dry run: `python scripts/migrate_rides_to_shards.py --dry-run`
    - Execute: `python scripts/migrate_rides_to_shards.py`
    - Note: script also mirrors required `Members` rows into each shard so FK checks on `Rides`/`Bookings`/`Ride_Chat` succeed.
- Fake data generator (to populate empty DB quickly):
    - `python -m scripts.generate_fake_data --rides 120 --members 80`
    - Fresh reset + generate: `python -m scripts.generate_fake_data --reset-ride-data --rides 120 --members 80`
- Validation script (no-loss/no-dup checks):
    - `python scripts/validate_shard_migration.py`
- Sharding verification endpoints (admin token required):
    - `GET /api/v1/testing/sharding/ride/{ride_id}`
    - `GET /api/v1/testing/sharding/rides/range?start_ride_id=1&end_ride_id=50`
    - `GET /api/v1/testing/sharding/distribution`
