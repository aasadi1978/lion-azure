import atexit
import logging
from concurrent.futures import ProcessPoolExecutor


class ProcessPoolManager:
    _executor: ProcessPoolExecutor | None = None
    _max_workers: int = 6

    @classmethod
    def get_executor(cls) -> ProcessPoolExecutor:
        """
        Lazily initialize and return a shared ProcessPoolExecutor.
        Automatically recreates if the pool was broken.
        """
        if cls._executor is None:
            logging.info(f"Initializing global process pool with {cls._max_workers} workers.")
            cls._executor = ProcessPoolExecutor(max_workers=cls._max_workers)
        return cls._executor

    @classmethod
    def restart_executor(cls):
        """Shut down and restart the executor, e.g., after a crash."""
        cls.shutdown()
        logging.warning("Restarting process pool due to crash or broken state.")
        cls._executor = ProcessPoolExecutor(max_workers=cls._max_workers)

    @classmethod
    def shutdown(cls):
        """Cleanly shut down the process pool."""
        if cls._executor is not None:
            logging.info("Shutting down global process pool.")
            cls._executor.shutdown(wait=True, cancel_futures=True)
            cls._executor = None


# Ensure the pool shuts down cleanly when Flask exits
atexit.register(ProcessPoolManager.shutdown)
