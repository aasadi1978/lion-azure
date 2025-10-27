import logging
from flask import Flask
from lion.create_flask_app.extensions import LION_SQLALCHEMY_DB
from lion.logger.exception_logger import log_exception

"""
In this module, we define a function to create all database tables. For those already setup, it will skip them gracefully.
This makes it easy to ensure that all necessary tables are created without causing errors for existing ones or errors caused by
missing new tables.
"""
def create_all(app: Flask):
    
    with app.app_context():

        try:
            from lion.maintenance.pid_manager import PIDManager
            from lion.orm.operators import Operator
            from lion.orm.vehicle_type import VehicleType
            from lion.orm.traffic_type import TrafficType
            from lion.orm.changeover import Changeover
            from lion.orm.shift_movement_entry import ShiftMovementEntry
            from lion.orm.drivers_info import DriversInfo
            from lion.orm.cost import Cost
            from lion.orm.orm_runtimes_mileages import RuntimesMileages
            from lion.orm.driver_report import DriverReport
            from lion.orm.location_mapping import LocationMapper as AzureLocationMapper
            from lion.orm.location import Location
            from lion.optimization.orm.opt_movements import OptMovements
            from lion.orm.pickle_dumps import PickleDumps as AzurePickleDumps
            from lion.orm.resources import Resources
            from lion.orm.time_stamp import TimeStamp
            from lion.orm.user_directory import UserDirectory
            from lion.orm.user_params import UserParams as AzureUserParams
            # from lion.orm.user import User
            # from lion.orm.scenarios import Scenarios
            from lion.logger.log_entry import LogEntry

            LION_SQLALCHEMY_DB.create_all()

            logging.debug("All tables created successfully (if they did not already exist).")
        
        except Exception:
            log_exception(popup=False, remarks="Error creating database tables.", level="critical")