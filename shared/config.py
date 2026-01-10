# shared/config.py
import os
from pathlib import Path
from dotenv import load_dotenv

# -------------------------------------------------
# Load environment variables
# -------------------------------------------------
load_dotenv()

# -------------------------------------------------
# Project structure
#
# sap_deliveries/
# ├─ api/
# ├─ bot/
# ├─ shared/
# │  └─ config.py  <-- this file
# ├─ data/
# -------------------------------------------------

# Project root directory (sap_deliveries)
BASE_DIR = Path(__file__).resolve().parent.parent

# Data directory (sqlite, logs, etc.)
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

# Static directories
API_STATIC_DIR = BASE_DIR / "api" / "static"

# -------------------------------------------------
# Environment / runtime config
# -------------------------------------------------
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8001"))

WEBAPP_URL = os.getenv(
    "WEBAPP_URL",
    f"http://{HOST}:{PORT}"
)

# -------------------------------------------------
# Database
# -------------------------------------------------
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    f"sqlite:///{DATA_DIR / 'deliveries.db'}"
)

# -------------------------------------------------
# Telegram
# -------------------------------------------------
BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    print("⚠ WARNING: BOT_TOKEN is not set")
