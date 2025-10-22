
from pathlib import Path
from os import getenv
# ----------------------------
# Configuration
# ----------------------------
RETRY_INTERVAL = 10        # seconds between checks
PROJECT_DIR = Path(getenv("PROJECT_DIR").strip()).resolve()
TRIGGER_FILE = PROJECT_DIR / "lion_update.trigger"
LION_VENV_DIR = PROJECT_DIR / ".venv"
LION_EXECUTABLE = PROJECT_DIR / ".venv" / "Scripts" / "lion.exe"
LION_PY_EXE = PROJECT_DIR / ".venv" / "Scripts" / "python.exe"
VENV_ACTIVATION_BAT = PROJECT_DIR / ".venv" / "Scripts" / "activate.bat"
LOG_FILE = Path(getenv("LOG_FILE", PROJECT_DIR / "orchestrator.log"))

LION_ONBOARDING_PATH = Path(getenv("OneDrive")) / "LION-UK" / "_onboarding_" 
LION_ORCHESTRATOR_PATH = PROJECT_DIR / "orchestrator"

PROJECT_DIR.mkdir(parents=True, exist_ok=True)