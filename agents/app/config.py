from pathlib import Path
import os
from dotenv import load_dotenv

AGENTS_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = AGENTS_ROOT.parent

load_dotenv(REPO_ROOT / "apps" / "web" / ".env")
load_dotenv(REPO_ROOT / ".env")

DATA_ROOT = REPO_ROOT / "data"
RESUMES_DIR = DATA_ROOT / "resumes"
RUNS_DIR = DATA_ROOT / "runs"
JD_RUNS_DIR = DATA_ROOT / "jd-runs"

MAX_UPLOAD_BYTES = 10 * 1024 * 1024
