import os
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SECRET_KEY = os.environ.get("SECRET_KEY", "dev-only-change-me")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
DATABASE_PATH = os.environ.get("DATABASE_PATH", os.path.join(BASE_DIR, "data", "arena.db"))
