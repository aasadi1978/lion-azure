from time import sleep
from .config import LION_PY_EXE, LION_VENV_DIR
import logging
import sys
from subprocess import CalledProcessError, CompletedProcess, run as subprocess_run


def create():
    """Create a virtual environment in the PROJECT_DIR/.venv folder."""
    python_exe = sys.executable

    try:
        if not LION_VENV_DIR.exists():
            logging.info("Creating virtual environment...")
            subprocess_run([python_exe, "-m", "venv", str(LION_VENV_DIR)], check=True)
            sleep(2)  # Give some time for the venv to be created
            logging.info("Virtual environment created successfully.")
        else:
            logging.info("Virtual environment already exists.")

        # --- Ensure pip is up-to-date ---
        pip_upgrade_status: CompletedProcess = subprocess_run([str(LION_PY_EXE), "-m", "pip", "install", "--upgrade", "pip"], check=False)
        if pip_upgrade_status.returncode != 0:
            logging.warning("Failed to upgrade pip, continuing with existing version.")

    except CalledProcessError as e:
        logging.error(f"Failed to create virtual environment: {e}")
        return False
    except Exception as e:
        logging.error(f"Unexpected error during virtual environment creation: {e}")
        return False

    return LION_VENV_DIR.exists()
