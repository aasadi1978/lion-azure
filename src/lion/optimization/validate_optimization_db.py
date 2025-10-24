import logging
from os import remove
from shutil import copyfile
from lion.bootstrap.constants import LION_OPTIMIZATION_DATABASE_NAME, LION_SCHEDULE_DATABASE_NAME
from lion.config.paths import LION_SQLDB_PATH
from lion.create_flask_app.create_app import LION_FLASK_APP
from lion.create_flask_app.extensions import LION_SQLALCHEMY_DB
from lion.optimization.optimization_logger import OPT_LOGGER

def fresh_start_optimization_db():
    try:
        dbpath = LION_SQLDB_PATH / LION_OPTIMIZATION_DATABASE_NAME

        if dbpath.is_file() and dbpath.exists():
            remove(dbpath)

        copyfile(LION_SQLDB_PATH / LION_SCHEDULE_DATABASE_NAME, dbpath)

        if dbpath.is_file() and dbpath.exists():
            return create_optimization_tables()

    except Exception as e:
        logging.error(f"Initializing optimization database failed: {str(e)}")
        OPT_LOGGER.log_exception(f"Initializing optimization database failed: {str(e)}")

        return False

def validate_optimization_database():
    try:
        dbpath = LION_SQLDB_PATH / LION_OPTIMIZATION_DATABASE_NAME

        if not (dbpath.is_file() and dbpath.exists()):
            copyfile(LION_SQLDB_PATH / LION_SCHEDULE_DATABASE_NAME, dbpath)

        if dbpath.is_file() and dbpath.exists():
            return create_optimization_tables()

    except Exception as e:
        logging.error(f"Initializing optimization database failed: {str(e)}")
        OPT_LOGGER.log_exception(f"Initializing optimization database failed: {str(e)}")

        return False
    
def create_optimization_tables():
    try:

        # Import optimization models so SQLAlchemy knows about them for create_all()
        from lion.orm.drivers_info import DriversInfo
        from lion.orm.changeover import Changeover
        from lion.orm.shift_movement_entry import ShiftMovementEntry
        from lion.orm.shift_index import ShiftIndex
        from lion.orm.opt_movements import OptMovements
        from lion.orm.resources import Resources

        with LION_FLASK_APP.app_context():
            LION_SQLALCHEMY_DB.create_all()
        
        return True

    except Exception as e:
        OPT_LOGGER.log_exception(f"Creating optimization database tables failed: {str(e)}")
        logging.error(f"Creating optimization database tables failed: {str(e)}")
        return False
