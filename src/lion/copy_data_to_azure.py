# Make sure bootstrap is imported first to setup env variables and logging
# bootstrap does not have any circular dependencies
import lion.bootstrap.validate_paths as validate_paths # bootstrap gets loaded in validate_paths through bootstrap\__init__.py
from lion.create_flask_app.create_tables import create_all
from lion.create_flask_app.create_app import LION_FLASK_APP
from lion.copy_to_azure.local_to_azure import start_copy

def run_copy():

    validate_paths.validate_all()
    create_all(app=LION_FLASK_APP)
    start_copy(app=LION_FLASK_APP)


if __name__ == "__main__":
    run_copy()