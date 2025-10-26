import logging


# Make sure bootstrap is imported first to setup env variables and logging
# bootstrap does not have any circular dependencies
from lion.logger.exception_logger import log_exception
import lion.bootstrap.validate_paths as validate_paths # bootstrap gets loaded in validate_paths through bootstrap\__init__.py
from lion.create_flask_app.create_tables import create_all
from lion.routes.blueprints import register_blueprints
from lion.create_flask_app.create_app import LION_FLASK_APP
import lion.routes.initialize_global_instances as  initialize_global_instances
import lion.maintenance.process_manager as process_manager

def initialize_app():

    logging.info(f"Starting LION Flask app initialization ...")
    validate_paths.validate_all()
    create_all(app=LION_FLASK_APP)
    process_manager.terminate_pids(app=LION_FLASK_APP)
    process_manager.toggle_processes(app=LION_FLASK_APP, is_redundant=False)
    initialize_global_instances.initialize_all(app=LION_FLASK_APP)
    register_blueprints(app=LION_FLASK_APP)

    with LION_FLASK_APP.app_context():
        try:
            from lion.ui.validate_shift_data import load_shift_data_if_needed

            status_load = load_shift_data_if_needed()
            if status_load['code'] != 200:
                raise ValueError(f"Failed to load shift data for detached run: {status_load['message']}")

            logging.info(f"Initial load of shift data completed successfully in {status_load.get('time_taken', 'N/A')}.")
        except Exception:
            log_exception(popup=False, remarks='Error during initial load of shift data.', level='error')

def _create_app():

    initialize_app()
    return LION_FLASK_APP

# Gunicorn on azure container will import this variable
app = _create_app()

# This is the entry point for starting the app using waitress on Windows or through whl package
def main():

    from waitress import serve
    from socket import AF_INET, SOCK_STREAM, socket

    port = 8000
    with socket(AF_INET, SOCK_STREAM) as s:
        try:
            s.bind(("127.0.0.1", port))
        except Exception:
            log_exception(popup=True, remarks=f"Port {port} is already in use. Please free the port and try again.")
        
    serve(LION_FLASK_APP, host="127.0.0.1", port=8000, threads=10, _quiet=True)

if __name__ == "__main__":
    logging.info("Starting LION application using waitress ... if __name__ == '__main__' block reached.")
    main()
