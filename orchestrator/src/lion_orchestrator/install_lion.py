import os
from pathlib import Path
from subprocess import run as subprocess_run, CompletedProcess, CalledProcessError, DEVNULL
import logging
from .create_venv import create as create_venv
from .config import LION_VENV_DIR, PROJECT_DIR, LION_ONBOARDING_PATH, LOG_FILE

def update_or_install_lion():

    WHL_DIR = LION_ONBOARDING_PATH / "whl"

    whl_file = f"{next(WHL_DIR.glob("lion-*.whl"), None)}"  # Get the first matching wheel file (full path)
    python_exe = f"{LION_VENV_DIR / ('Scripts/python.exe' if os.name == 'nt' else 'bin/python')}"
    if Path(python_exe).exists():
        python_exe = Path(python_exe).resolve()
    else:
        logging.error("Python executable not found in the virtual environment.")
        return False

    try:
        # --- Kill running LION processes (Windows only) ---
        if os.name == "nt":
            # Kill lion.exe processes
            subprocess_run(["taskkill", "/IM", "lion.exe", "/F"], stdout=DEVNULL, stderr=DEVNULL)
            # Kill python processes running lion module
            kill_py_status: CompletedProcess = subprocess_run(
            ['wmic', 'process', 'where', 'CommandLine like "%lion%" and Name="python.exe"', 'call', 'terminate'],
            stdout=LOG_FILE, stderr=LOG_FILE
            )
        else:
            # Kill lion processes and python processes running lion
            kill_py_status: CompletedProcess = subprocess_run(["pkill", "-f", "lion"], stdout=LOG_FILE, stderr=LOG_FILE)

        if kill_py_status.returncode == 0:
            logging.info("Terminated running LION processes.")
        else:
            logging.info("No running LION processes found.")

        # --- Find wheel file ---
        if not whl_file or not Path(whl_file).exists():
            logging.error("No LION installer (.whl) found under ./whl directory.")
            return False

        if create_venv():

            # --- Uninstall old LION package if exists ---
            uninstall_lion_status: CompletedProcess = subprocess_run([str(python_exe), "-m", "pip", "uninstall", "-y", "lion"], check=False)
            if uninstall_lion_status.returncode != 0:
                logging.info("No existing LION installation found to uninstall.")

            # --- Install new package ---
            lion_install_status: CompletedProcess = subprocess_run(
                f'{python_exe} -m pip install "{whl_file}"',
                shell=False,
                check=True
            )

            if lion_install_status.returncode != 0:
                logging.error("LION installation failed.")
                return False

        # --- Verify installation ---
        result = subprocess_run(
            [str(python_exe), "-c", "import lion; print('LION installed:', lion.__package__)"],
            capture_output=True, text=True
        )

        logging.info(result.stdout.strip() or "LION verification complete.")
        logging.info("LION update completed successfully.")

    except CalledProcessError as e:
        logging.error(f"Update failed during subprocess call: {e}")
        return False
    except Exception as e:
        logging.error(f"Unexpected error during update: {e}")
        return False
    finally:
        # Remove trigger file if exists
        trigger_file = PROJECT_DIR / "lion_update.trigger"
        if trigger_file.exists():
            trigger_file.unlink()

    return True