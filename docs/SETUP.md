# Setup
# Setup
Run these commands from the project root (the directory containing `backend/`).

## Windows PowerShell
```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe scripts\init_db.py
.\.venv\Scripts\python.exe -m backend.app
```

## macOS / Linux
```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python scripts/init_db.py
.venv/bin/python -m backend.app
```

Open http://localhost:5000. Set `SECRET_KEY` for deployments; set `GEMINI_API_KEY` only if you want AI explanations. The Gemini key stays on the server. The app works without a `.env` file.

Tests:
- Windows: `.\.venv\Scripts\python.exe -m pytest tests`
- macOS / Linux: `.venv/bin/python -m pytest tests`

# Deployment
Use one worker (state is guarded by in-process locks): `gunicorn -k gthread --threads 50 -w 1 backend.app:app`, behind HTTPS (Render, Railway, Fly.io). Set SECRET_KEY, GEMINI_API_KEY, DATABASE_PATH on a persistent disk. For PostgreSQL, replace backend/db.py (all SQL is isolated there).
