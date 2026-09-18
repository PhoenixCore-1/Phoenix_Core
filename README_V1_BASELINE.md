# Phoenix Core V1.0.0 — Baseline

This is the Phoenix platform baseline. It intentionally excludes business-module implementation.

## Runtime
- Backend: Python + FastAPI + Uvicorn
- Frontend: React + Vite + TypeScript
- Development database: SQLite

## End-to-end flow
Landing -> Login -> Phoenix Core -> System/Company/User Platform -> Active Modules.

## Local setup
1. Create a Python virtual environment and install the project.
2. Run `python scripts/init_dev_db.py`.
3. Start API: `uvicorn phoenix_core.http_api.app:create_development_app --factory --host 127.0.0.1 --port 8000`
4. In `frontend/company-platform`, run `npm install` then `npm run dev`.
5. Open `http://127.0.0.1:5174`.

Development accounts are printed by the database initializer. Never use these credentials outside local development.
