from .config import LION_EXECUTABLE, LION_PY_EXE
import logging
from pathlib import Path
from subprocess import CalledProcessError, CompletedProcess, run


def validate_lion_installation() -> bool:
    """Check if LION is installed and executable."""
    lion_path = Path(LION_EXECUTABLE)

    if not lion_path.exists():
        logging.error("LION installation not found.")
        return False

    try:
        # Run with --version or similar lightweight check if available
        result: CompletedProcess = run(
            [str(LION_PY_EXE), "-m", "pip", "show", "lion"],
            capture_output=True,
            text=True,
            check=True
        )
        logging.info(f"LION installation verified: {result.stdout.strip()}")
        return True

    except CalledProcessError as e:
        logging.error(f"LION installation corrupted or failed: {e}")
        return False
    except Exception as e:
        logging.error(f"Unexpected error checking LION installation: {e}")
        return False