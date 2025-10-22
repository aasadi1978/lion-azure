# Configure logging
import logging
from logging.handlers import RotatingFileHandler
from os import environ, getenv, path
from pathlib import Path

USER_HOME_PATH = Path(path.expanduser("~")).resolve()
PROJECT_DIR = Path(getenv("LION_PROJECT_PATH", USER_HOME_PATH / "LION_APP"))
LOG_FILE = PROJECT_DIR / "orchestrator.log"
PROJECT_DIR.mkdir(parents=True, exist_ok=True)

environ["PROJECT_DIR"] = str(PROJECT_DIR)
environ["LOG_FILE"] = str(LOG_FILE)
environ["USER_HOME_PATH"] = str(USER_HOME_PATH)

logger = logging.getLogger("LION_Orchestrator")
logger.setLevel(logging.INFO)
handler = RotatingFileHandler(LOG_FILE, maxBytes=5_000_000, backupCount=3)
formatter = logging.Formatter("[%(asctime)s] %(levelname)s: %(message)s", "%Y-%m-%d %H:%M:%S")
handler.setFormatter(formatter)
logger.addHandler(handler)

logger.info("Starting LION orchestrator...")