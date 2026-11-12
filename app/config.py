from pathlib import Path
import os

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
WORKSPACES_DIR = ROOT / "workspaces"
DB_PATH = DATA_DIR / "platform.db"
DATA_DIR.mkdir(exist_ok=True)
WORKSPACES_DIR.mkdir(exist_ok=True)

APP_NAME = "Software Reconstruction Platform"
APP_VERSION = "3.3.0"
MAX_CLONE_SECONDS = int(os.getenv("MAX_CLONE_SECONDS", "180"))
