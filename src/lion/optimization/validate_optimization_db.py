import logging
from lion.create_flask_app.create_app import LION_FLASK_APP
from lion.create_flask_app.extensions import LION_SQLALCHEMY_DB
from lion.optimization.optimization_logger import OPT_LOGGER
    
def validate_optimization_database():
    try:

        # Import optimization models so SQLAlchemy knows about them for create_all()
        from lion.optimization.orm.opt_drivers_info import OptimizationDriversInfo
        from lion.optimization.orm.opt_changeover import OptimizationChangeover
        from lion.optimization.orm.opt_movements import OptMovements
        from lion.orm.resources import Resources

        with LION_FLASK_APP.app_context():
            LION_SQLALCHEMY_DB.create_all()
        
        return True

    except Exception as e:
        OPT_LOGGER.log_exception(f"Creating optimization database tables failed: {str(e)}")
        logging.error(f"Creating optimization database tables failed: {str(e)}")
        return False
