from pathlib import Path

# Ensure .env is loaded before paths are used
import app.env  # noqa: F401

from app.env import REPO_ROOT, WEB_ENV_FILE, get_env_path

AGENTS_ROOT = Path(__file__).resolve().parents[1]

DATA_ROOT = REPO_ROOT / "data"
RESUMES_DIR = DATA_ROOT / "resumes"
RUNS_DIR = DATA_ROOT / "runs"
JD_RUNS_DIR = DATA_ROOT / "jd-runs"

MAX_UPLOAD_BYTES = 10 * 1024 * 1024
