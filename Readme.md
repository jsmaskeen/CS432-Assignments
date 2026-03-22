# RAJAK: Ride Along--Just Act Kool

Cab sharing portal made for students of IIT Gandhinagar, developed across four assignments for the course CS 432 Databases (Track 1).

## To Run

### Manual (backend + frontend)

```
cd backend
python -m venv .venv

# Windows PowerShell
.venv\Scripts\Activate.ps1

# Linux / macOS / Git Bash
source .venv/bin/activate

pip install -r requirements.txt
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

In a second terminal:

```
cd frontend
npm install
npm run dev
```

### One command (shell script)

```
chmod +x start-dev.sh
./start-dev.sh
```

This script installs backend/frontend dependencies (if needed) and starts both dev servers.

## Assignments:

1. Assignment 1:
    - [`Report`](./PDFs/Report.pdf)
    - [`ER Diagram`](./ER-Diagrams/ER.png) ([High Quality Zoomable Version](https://jsmaskeen.github.io/CS432-Assignments))
    - [`SQL Dump`](./SQL-Dump/dump.sql)
2. Assignment 2:
    - Simple project structure overview:
        - `backend/`: FastAPI application (API routes, models, schemas, DB session management, auth, audit/routing helpers).
        - `frontend/`: React + Vite application (UI pages for rides, bookings, chat, admin, settlements, locations, etc.).
        - `INITIALISE_DB.sql`: database bootstrap SQL for creating/initializing core schema/data and triggers.
        - `backend/audit.log`: application level log file showing all the transactions from the app to the db.
        - `audit_modifications_log_table.json`: Data from the MySQL Logging table watching all the modifications in important tables.
        - `unauthorized_modifications_view.json`: Data from the MySQL View on the above table, which shows only the unauthorized modification entries, by checking the flag `is_authorized`.

### Group Details:

1. Aarsh Wankar (23110003)
2. Abhinav Khot (23110006)
3. Jaskirat Singh Maskeen (23110146)
4. Karan Sagar Gandhi (23110157)
5. Romit Mohane (23110279)
