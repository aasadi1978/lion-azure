import os
from flask import Flask


from lion.logger.exception_logger import log_exception
from lion.create_flask_app.create_app import LION_FLASK_APP

def terminate_pids(app: Flask = LION_FLASK_APP):
    """Dispose of redundant PIDs by killing their processes and removing their entries from the database."""

    try:
        with app.app_context():
            from lion.maintenance.pid_manager import PIDManager
            PIDManager.kill_redundant_processes()
    except Exception as e:
        log_exception(popup=False, remarks=f'Error terminating redundant processes: {e}', level='error')    

def toggle_processes(app: Flask = LION_FLASK_APP, **kwargs):
    """Mark existing PIDs as redundant if user specifies, otherwise mark as non-redundant."""

    with app.app_context():

        try:
            from lion.maintenance.pid_manager import PIDManager
            proc_title = 'lion-app-session'
            pid = os.getpid()
            PIDManager.register_pid(pid=pid, process_name=proc_title if proc_title else f'lion-python-{pid}', 
                                    is_redundant=kwargs.get('is_redundant', False))
        
        except Exception as e:
            log_exception(popup=False, remarks=f"Error toggling process redundancy: {e}", level='error')