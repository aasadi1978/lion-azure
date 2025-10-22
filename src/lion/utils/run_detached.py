import logging
from multiprocessing import Process, get_start_method, set_start_method
from os import getpid
from pathlib import Path
from typing import Callable


class DetachedRuns:

    _instance = None
    def __new__(cls):
        if not cls._instance:
            cls._instance = super(DetachedRuns, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if not self._initialized:
            self.initialize()

    def initialize(self, log_dir: Path | str = ''):
        """Initialize the DetachedRuns manager."""
        if self._initialized:
            return

        self.log_dir = Path(log_dir if Path(log_dir).exists() else Path().resolve() / "status.log").resolve()
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.active_processes = {}
        self.cleanup()

        self._initialized = True
    
    def restart(self):
        self._initialized = False
        self.initialize()

    @classmethod
    def get_instance(cls):
        return cls()

    def _run_cold_start(self, *args, **kwargs):
        """
        In this module, we take the following steps in order:
        
        - we initialize a dedicated logger for the new session.
        - we reload the config to ensure the detached run has its own fresh config.
        - we create a new Flask app instance to ensure no state is shared.
        """
        try:
            # Import inside function to avoid import-time delays
            from lion.create_flask_app.create_app import FLASK_APP_INSTANCE
            from lion.logger.logger_handler import initialize_logger
            import lion.bootstrap.validate_paths as validate_paths
            from lion.routes import initialize_global_instances
            
            initialize_logger()
            validate_paths.validate_all()

            FLASK_APP_INSTANCE.reset_instance()
            app = FLASK_APP_INSTANCE.lion_flask_app()

            if kwargs.get('bind', ''):
                """
                Update the database bind key for the detached run so that it uses the correct database.
                """
                FLASK_APP_INSTANCE.config.update({
                    'LION_USER_SPECIFIED_BIND': kwargs['bind']
                })

            initialize_global_instances.initialize_all(app=FLASK_APP_INSTANCE)

        except Exception as e:
            logging.error(f"Error during cold start in DetachedRuns: {e}")
            return None
        
        return app

    def _run_wrapper(self, func: Callable, run_id: str, *args, **kwargs):

        """Internal wrapper that runs the target function with its own logging.

        In this module, we take the following steps in order:
        
        - we initialize a dedicated logger for the new session.
        - we reload the config to ensure the detached run has its own fresh config.
        - we create a new Flask app instance to ensure no state is shared.
        """

        import setproctitle
        import time

        setproctitle.setproctitle(run_id)
        time.sleep(0.5)  # Give time for the process title to update

        try:
            # Import inside function to avoid import-time delays
            from lion.ui.validate_shift_data import load_shift_data_if_needed
            detached_run_app = self._run_cold_start(bind=kwargs.get('bind', ''))

            if not detached_run_app:
                logging.error("Failed to create Flask app for detached run.")
                return

            with detached_run_app.app_context():
                
                if load_shift_data_if_needed()['code'] != 200:
                    logging.error("Failed to load shift data for detached run.")
                    return

                logging.info(f"Detached run process started with the process title-pid: {f"{run_id}-{getpid()}"}")
                func(*args, **kwargs)

        except Exception as e:
            logging.error(f"Error during detached run: {e}")
            print(e)
        finally:
            logging.info(f"Finished detached run: {func.__name__}")

    def cleanup(self):
        """Remove finished processes from tracking."""
        finished = [rid for rid, p in self.active_processes.items() if not p.is_alive()]
        for rid in finished:
            try:
                self.active_processes[rid].join(timeout=1)  # Wait max 1 second
            except Exception as e:
                logging.warning(f"Error joining process {rid}: {e}")
            finally:
                del self.active_processes[rid]

    def get_process_status(self, run_id: str = None):
        """Get status of running processes."""
        if run_id:
            if run_id in self.active_processes:
                return {
                    'run_id': run_id,
                    'alive': self.active_processes[run_id].is_alive(),
                    'pid': self.active_processes[run_id].pid
                }
            return {'run_id': run_id, 'status': 'not_found'}
        
        # Return status of all processes
        status = {}
        for rid, p in self.active_processes.items():
            status[rid] = {
                'alive': p.is_alive(),
                'pid': p.pid
            }
        return status

    def terminate_process(self, run_id: str):
        """Terminate a specific process."""
        if run_id in self.active_processes:
            try:
                self.active_processes[run_id].terminate()
                self.active_processes[run_id].join(timeout=5)
                del self.active_processes[run_id]
                return True
            except Exception as e:
                logging.error(f"Error terminating process {run_id}: {e}")
                return False
        return False

    def run_immediate(self, func: Callable, *args, **kwargs) -> str:
        """
        Start a completely detached process that returns immediately.
        Returns a run_id string instead of waiting for process creation.
        """
        import threading

        process_name = kwargs.get('process_title', '').lower().replace(' ', '-').replace('python', '').replace('py-', '').strip()
        run_id = f"py-{process_name}-{getpid()}"

        def fire_and_forget():
            try:
                logging.info(f"Starting immediate detached run: {run_id}-{func.__name__}")
                
                # Set spawn method for Windows compatibility
                if get_start_method(allow_none=True) != 'spawn':
                    set_start_method('spawn', force=True)
                
                p = Process(
                    target=self._run_wrapper,
                    args=(func, run_id) + args,
                    kwargs=kwargs,
                    name=run_id
                )
                p.start()
                
                # Don't track this process - true fire and forget
                logging.info(f"Fire-and-forget process started with PID: {p.pid}")
                
            except Exception as e:
                logging.error(f"Failed to start immediate detached run: {e}")

        # Start in thread and return immediately
        thread = threading.Thread(target=fire_and_forget, daemon=True)
        thread.start()
        
        return run_id


DETACHEDRUNS = DetachedRuns.get_instance()