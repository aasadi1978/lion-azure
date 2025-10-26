import logging
import logging.handlers
from os import getenv, getpid
from pathlib import Path
import sys
from setproctitle import getproctitle



def initialize_logger(
    log_file_path: Path = None,
    log_level: int = logging.DEBUG,
    max_bytes: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 1,
    console_output: bool = True
) -> logging.Logger:
    """
    Initialize logger with file and optional console output.
    
    Args:
        log_file_path: Path to log file (defaults to 'status.log' in current directory)
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        max_bytes: Maximum size of log file before rotation
        backup_count: Number of backup files to keep
        console_output: Whether to also output logs to console
        
    Returns:
        Configured logger instance
    """

    if log_file_path is None or not Path(log_file_path).exists():
        log_file_path = Path(getenv('LION_PROJECT_HOME', str(Path().resolve()))) / 'status.log'
        
    # Ensure log directory exists
    log_file_path.parent.mkdir(parents=True, exist_ok=True)
    success_code = 1

    try:
        # Clear existing handlers more safely
        root_logger = logging.getLogger()
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
            handler.close()

    except Exception as e:
        success_code = 0
        logging.warning(f"Failed to clear existing handlers: {e}")

    if not success_code:
        logging.error(f"[FATAL] Failed to clear existing handlers: {e}")
        return success_code

    try:
        # Create formatter with process name from getproctitle()
        try:
            process_name = getproctitle()
        except ImportError:
            process_name = getpid()

        formatter = logging.Formatter(
            f"{process_name} | %(asctime)s | %(levelname)-8s | %(name)s | %(filename)s:%(lineno)d | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )

        # Create rotating file handler
        file_handler = logging.handlers.RotatingFileHandler(
            log_file_path,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding="utf-8"
        )
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)

        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(log_level)
        root_logger.addHandler(file_handler)

        # Optional console handler
        if console_output:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(log_level)
            console_handler.setFormatter(formatter)
            root_logger.addHandler(console_handler)

        # Mute all third-party debug logs globally
        for noisy_logger in ["PIL", "matplotlib", "urllib3", "asyncio", "requests", 
                             "PIL.PngImagePlugin", "werkzeug", "ortools"]:
            logging.getLogger(noisy_logger).setLevel(logging.WARNING)

        logging.info(f"Logger initialized successfully. Log file: {log_file_path}")
        success_code = 1

    except Exception as e:
        logging.error(f"[FATAL] Failed to initialize logger: {e}")
        success_code = 0

    return success_code
