import logging
import time
from subprocess import CompletedProcess, run, DEVNULL
import psutil

from .lion_health_check import check_health
from .validate_installation import validate_lion_installation
from .config import LION_EXECUTABLE, RETRY_INTERVAL, TRIGGER_FILE, PROJECT_DIR, VENV_ACTIVATION_BAT
from .install_lion import update_or_install_lion as update_lion
from .create_venv import create as create_venv

def venv_is_active() -> bool:

    """Activate the virtual environment."""

    try:

        if VENV_ACTIVATION_BAT.exists() or create_venv():
            venv_activation_status: CompletedProcess = run(
                [str(VENV_ACTIVATION_BAT)],
                shell=False,
                stdout=DEVNULL,
                stderr=DEVNULL
            )

            if venv_activation_status.returncode != 0:
                logging.error("Failed to activate virtual environment.")
                return False
            
            logging.info("Virtual environment activated.")
            time.sleep(1)  # Give some time for the venv to activate
            return True
        else:
            logging.error("Virtual environment activation script not found.")
            return False
        
    except Exception as e:
        logging.error(f"Failed to activate virtual environment: {e}")
        return False
    
def is_lion_exe_running() -> bool:
    """Check if lion.exe process is running."""

    if check_health():
        return True
    
    for proc in psutil.process_iter(attrs=["name"]):
        if proc.info["name"] and "lion.exe" in proc.info["name"].lower():
            return True
        
    return False

def start_lion() -> bool:
    """Start LION process in the PROJECT_DIR folder."""
    try:
        if venv_is_active():
            init_lion: CompletedProcess = run(
                [str(LION_EXECUTABLE)],
                cwd=str(PROJECT_DIR.resolve()),
                shell=False,
                stdout=DEVNULL,
                stderr=DEVNULL
            )

            if init_lion.returncode != 0:
                logging.error("Failed to start LION process.")
                return False
            
            logging.info(f"LION started successfully in {PROJECT_DIR.resolve()}.")
            return True
    except Exception as e:
        logging.error(f"Failed to start LION: {e}")
        return False

def updates_triggered() -> bool:
    """Check for update trigger file."""
    return TRIGGER_FILE.exists()

def main():
    logging.info("Starting LION Orchestrator...")
    # ----------------------------
    # Main Loop - monitor and manage LION
    # ----------------------------
    failure_count = 0

    while True:

        # Handle update trigger
        if not validate_lion_installation() or updates_triggered():
            update_lion()

        # Check if LION is running
        if not is_lion_exe_running():
            logging.warning("LION not running! Attempting restart...")
            if start_lion():
                failure_count = 0
            else:
                failure_count += 1
                logging.warning(f"Failed restart attempt #{failure_count}.")

        else:
            failure_count = 0

        # Sleep and repeat
        time.sleep(RETRY_INTERVAL)
