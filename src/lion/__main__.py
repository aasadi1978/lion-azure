import logging
from os import environ, getenv
from sys import exit as sys_exit
from flask import Flask, jsonify
from waitress import serve
# Make sure bootstrap is imported first to setup env variables and logging
# bootstrap does not have any circular dependencies
import lion.bootstrap.validate_paths as validate_paths # bootstrap gets loaded in validate_paths through bootstrap\__init__.py
from lion.create_flask_app.create_tables import create_all
from lion.routes.blueprints import register_blueprints
from lion.utils.find_available_port import get_port
from lion.create_flask_app.create_app import LION_FLASK_APP
import lion.routes.initialize_global_instances as  initialize_global_instances
import lion.maintenance.process_manager as process_manager
from lion.utils.whl_version import RETTRIEVELIONVERSION

def main():

    validate_paths.validate_all()
    create_all(app=LION_FLASK_APP)
    process_manager.terminate_pids(app=LION_FLASK_APP)
    process_manager.toggle_processes(app=LION_FLASK_APP, is_redundant=False)
    initialize_global_instances.initialize_all(app=LION_FLASK_APP)
    register_blueprints(app=LION_FLASK_APP)
    RETTRIEVELIONVERSION.initialize()
    initial_load(app=LION_FLASK_APP)
    start_app(app=LION_FLASK_APP)

def initial_load(app: Flask):

    with app.app_context():

        try:
            from lion.ui.validate_shift_data import load_shift_data_if_needed
            from lion.logger.exception_logger import log_exception

            status_load = load_shift_data_if_needed()
            if status_load['code'] != 200:
                raise ValueError(f"Failed to load shift data for detached run: {status_load['message']}")
            
            logging.info(f"Initial load of shift data completed successfully in {status_load.get('time_taken', 'N/A')}.")

        except Exception:
            log_exception(popup=False, remarks='Error during initial load of shift data.', level='error')

@LION_FLASK_APP.route("/health-check", methods=["GET"])
def health():
    return jsonify({"status": "ok"}), 200

def start_app(app: Flask):

    """Start the Flask app in debug mode."""
    port = get_port()
    if port is None:
        logging.critical("Could not find a free port to start the application!")
        sys_exit(1)

    if getenv('LION_DEBUG_MODE', 'FALSE').upper() == 'TRUE':
        # This is controlled by the presence of a file called .debug_mode_on in the LION_PROJECT_HOME (current) directory
        # If the file is present, the environment variable LION_DEBUG_MODE is set to TRUE, and False, otherwise.
        try:
            app.run(host="0.0.0.0", debug=True, port=port, use_reloader=True)
        except Exception as e:
            if not str(environ.get("WERKZEUG_RUN_MAIN")) == "true":
                logging.critical(f"Failed to start in debug mode: {e}")
            else:
                logging.critical(f"Error at __main__/start_app: {str(e)}. Exiting the app with code 1.")
                sys_exit(1)

    else:
        try:
            # Timer(1, open_browser, args=(port,)).start()
            serve(app, host="0.0.0.0", port=port,
                threads=10, _quiet=True
            )

        except Exception as e:
            logging.critical(f"Error at __main__.py: {str(e)}. Exiting the app with code 1.")
            sys_exit(1)


if __name__ == "__main__":
    main()
