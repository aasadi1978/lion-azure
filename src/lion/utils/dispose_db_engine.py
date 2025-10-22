from lion.create_flask_app.extensions import LION_SQLALCHEMY_DB
from lion.logger.exception_logger import log_exception


def shutdown_db_engine():
    """
    Dispose the database engine to release resources.
    This is typically called when the application is shutting down or when a significant change occurs.
    """

    status = 'OK'
    try:
        LION_SQLALCHEMY_DB.engine.dispose()
        LION_SQLALCHEMY_DB.session.close()
    except Exception as e:
        status = log_exception(f"Error disposing database engine: {e}")
    finally:
        LION_SQLALCHEMY_DB.session.close()
        LION_SQLALCHEMY_DB.engine.dispose()
    
    return status
