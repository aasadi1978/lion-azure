import logging
from flask import jsonify, request
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

# Make sure bootstrap is imported first to setup env variables and logging
# bootstrap does not have any circular dependencies
# from lion.create_flask_app.create_tables import create_all
# from lion.logger.exception_logger import log_exception
from lion.create_flask_app.create_app import LION_FLASK_APP
import lion.bootstrap.validate_paths as validate_paths # bootstrap gets loaded in validate_paths through bootstrap\__init__.py
from lion.routes.blueprints import register_blueprints
import lion.routes.initialize_global_instances as  initialize_global_instances

list_non_db_endpoints = ["health_check"]

def _create_app():

    validate_paths.validate_all()
    initialize_global_instances.initialize_all(app=LION_FLASK_APP)
    register_blueprints(app=LION_FLASK_APP)

    return LION_FLASK_APP

# Gunicorn on azure container will import this variable
app = _create_app()
# create_all(app=app)

@app.route("/health-check", methods=["GET"])
def health_check():
    return jsonify({"status": "ok"}), 200


@app.before_request
def check_db_alive():

    if request.endpoint in list_non_db_endpoints:
        return  # Skip DB check for health-check

    from lion.create_flask_app.extensions import LION_SQLALCHEMY_DB
    try:
        LION_SQLALCHEMY_DB.session.execute(text("SELECT 1"))
        return
    except SQLAlchemyError as e:
        from lion.create_flask_app.azure_sql_manager import validate_db_connection
        validate_db_connection(app)

# This is the entry point for starting the app using waitress on Windows or through whl package
# This function will not be called by Gunicorn on Azure linux container asit needs 'app' defiend in app = _create_app()
def main():

    from waitress import serve
    from socket import AF_INET, SOCK_STREAM, socket

    port = 8000
    with socket(AF_INET, SOCK_STREAM) as s:
        try:
            s.bind(("127.0.0.1", port))
        except Exception:
            logging.error(popup=True, remarks=f"Port {port} is already in use. Please free the port and try again.")
        
    serve(LION_FLASK_APP, host="127.0.0.1", port=8000, threads=10, _quiet=True)

if __name__ == "__main__":
    logging.info("Starting LION application using waitress ... if __name__ == '__main__' block reached.")
    main()
