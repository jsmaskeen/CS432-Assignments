# RAJAK: Ride Along--Just Act Kool

Cab sharing portal made for students of IIT Gandhinagar, developed across four assignments for the course CS 432 Databases (Track 1).

## To Run

## Testing for Module A (ACID)

Kindly run on a Linux Terminal (as we have used custom signals for crashing) or run over WSL. 

```bash
pip install pytest
cd "Assignment-3/Module_A"
pytest -v tests/ > test_output.out
```

Results: [`test_output.out`](./Assignment-3/Module_A/test_output.out)

First navigate to `Assignment-2/Module_B`
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
        - `logs/audit_modifications_log_table.json`: Data from the MySQL Logging table watching all the modifications in important tables.
        - `logs/unauthorized_modifications_view.json`: Data from the MySQL View on the above table, which shows only the unauthorized modification entries, by checking the flag `is_authorized`.

